# shellcheck shell=bash
# shellcheck disable=SC2034  # the paths and values here are read by the blocks that source this file
# What every block of Lem's script checks shares: the strict mode, the root of the checkout, a
# folder of its own, the interpreter, the count of its checks (checks.sh), and the helpers more than
# one block calls. A block sources this file first and ends with `finish`. Each block runs alone, so
# nothing here depends on the order in which the blocks run.
set -eEuo pipefail

# -P: the folder as it is on disk, the way readlink and git name it: a checkout under /tmp is
# under /private/tmp on macOS.
cd -P "$(dirname "${BASH_SOURCE[0]}")/.."
PROJECT=$PWD/skills/lem/scripts/project.py
CRITERIA=$PWD/skills/lem/scripts/criteria.py
DECISIONS=$PWD/skills/lem/scripts/decisions.py
LAND=$PWD/skills/lem/scripts/land.py
WORK=$(cd "$(mktemp -d)" && pwd -P)
# shellcheck source=tests/checks.sh
. tests/checks.sh
trap 'stopped; rm -rf "$WORK"' EXIT
PY=$(python3 -I -c 'import sys; print(sys.executable)')
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1

project() { "$PY" -B "$PROJECT" "$@"; }
status_of() { set +e; "$@" >/dev/null 2>&1; local code=$?; set -e; echo "$code"; }
field() { "$PY" -c 'import json, sys; d = json.load(sys.stdin); print(eval(sys.argv[1], {"d": d}))' "$1"; }
commit() { git -C "$1" -c user.name=t -c user.email=t@t commit -q --allow-empty -m "$2"; }
# CASE: the run that ends badly, which every choice for the owner carries above his card (decisions.py ask)
CASE=(--case $'1. Order 1042 has two gift notes, "for Ania" and "for Ola".\n2. The export writes one cell for the note of an order.\n3. The merchant prints the slip with one note, and Ola gets none.'
  --case-was derived --cause "An order has one cell for its note, and every export of notes shares that cell.")
# soon COMMAND...: run COMMAND until it succeeds, five times a second and for 30 seconds at most,
# for what another process does when a loaded machine starts it late. It never fails by itself:
# the check after it says whether what it waited for came.
soon() {
  local tries=150
  until "$@"; do
    tries=$((tries - 1))
    [ "$tries" -gt 0 ] || return 0
    sleep 0.2
  done
}
# past FILE ID...: the wait of each choice ends, as its deadline is written into the past, the way fifteen minutes later would find it
past() { "$PY" -c 'import json, sys
lines = [json.loads(line) for line in open(sys.argv[1])]
for line in lines:
    if line["kind"] == "asked" and str(line["id"]) in sys.argv[2:]: line["deadline"] = "2026-01-01T00:00:00Z"
open(sys.argv[1], "w").write("".join(json.dumps(line) + "\n" for line in lines))' "$@"; }

# The landing's helpers, for every block that takes a task through land.py.
land() { "$PY" -B "$LAND" "$@"; }
ident() { git -C "$1" config user.name t; git -C "$1" config user.email t@t; }
# plan_in TREE SLUG TEST: the task's plan, a full change's, with one criterion that TEST holds; TEST is `no test: REASON` for a criterion with none
plan_in() {
  local held="   - test: \`$3\` in \`tests/$2.sh\`"
  case "$3" in "no test:"*) held="   - $3" ;; esac
  mkdir -p "$1/docs/plans" "$1/tests"
  printf '%s\n' "# $2" '' '## Acceptance criteria' '' 'Size: full, because the ticket names the word and the file.' '' \
    '1. The file holds the word the owner asked for.' "$held" '' '## Tasks' '' '1. The change.' > "$1/docs/plans/20261115-$2.md"
}
# task_in REPO SLUG FILE TEXT: a full change with a worktree, one commit that writes FILE, its plan and the test of its criterion,
# and the state `ready`. Its landing needs a polish pass (polish_in) and its proposal a read of its criteria (read_in).
task_in() {
  local tree
  project --repo "$1" task-dir "$2" --ask "Put $4 into $3." >/dev/null
  tree=$(project --repo "$1" worktree-dir "$2")
  git -C "$1" worktree add -q "$tree" -b "fix/$2" main
  plan_in "$tree" "$2" "sh tests/$2.sh"
  printf '%s\n' "$4" > "$tree/$3" && echo "grep -qx $4 $3" > "$tree/tests/$2.sh"
  git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: $2"
  project --repo "$tree" state "$2" ready "the report is written" >/dev/null
}
# small_task_in REPO SLUG FILE TEXT: a small change with a worktree: its one criterion in the task directory, approved in
# the owner's name, with the test line under it; one commit that writes FILE and the test, no plan; and the state `ready`
small_task_in() {
  local tree directory
  directory=$(project --repo "$1" task-dir "$2" --ask "Put $4 into $3.")
  printf '%s\n' '## Acceptance criteria' '' 'Size: small, because the request is one sentence.' '' '1. The file holds the word the owner asked for.' > "$directory/criteria.md"
  "$PY" -B "$CRITERIA" --repo "$1" approve "$2" --file "$directory/criteria.md" --small >/dev/null
  printf '%s\n' "   - test: \`sh tests/$2.sh\` in \`tests/$2.sh\`" >> "$directory/criteria.md"
  tree=$(project --repo "$1" worktree-dir "$2")
  git -C "$1" worktree add -q "$tree" -b "fix/$2" main
  mkdir -p "$tree/tests" && printf '%s\n' "$4" > "$tree/$3" && echo "grep -qx $4 $3" > "$tree/tests/$2.sh"
  git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: $2"
  project --repo "$tree" state "$2" ready "the small change is built" >/dev/null
}
# read_in REPO SLUG: the personas' read of the plan's criteria by the lead, as a full change from a complete request has it: two personas of one
# model family, nobody confused. A full change is not proposed without one.
read_in() {
  local digest
  digest=$("$PY" -B "$CRITERIA" --repo "$1" digest "$2" | field 'd["digest"]')
  project --repo "$1" log "$2" criteria.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
}
# polish_in REPO SLUG: the polish pass of a full change's landing, which here changes nothing; none when this landing's pass is done already
polish_in() {
  local started
  started=$(land --repo "$1" polish "$2") || return 1
  if [ "$(field 'd["done"]' <<<"$started")" = False ]; then land --repo "$1" polish "$2" --done >/dev/null; fi
}
status_in() { project --repo "$1" tasks | field "next(t[\"status\"] for t in d if t[\"slug\"] == \"$2\")"; }
kept_in() { "$PY" -c 'import json, sys; print(json.load(open(sys.argv[1])).get(sys.argv[2]))' "$1/.lem/state/tasks/$2/landing.json" "$3"; }
# record N JSON: the file that says what a review was and what it found, as the Nth start of the task's review;
# its careful call is "not careful" with one sentence of why, unless JSON makes its own
NOT_CAREFUL="the diff reaches no topic of the settings"
record() {
  "$PY" -c 'import json, sys; json.dump({"attempt": int(sys.argv[1]), "careful": False, "careful_why": sys.argv[4], **json.loads(sys.argv[2])}, open(sys.argv[3], "w"))' "$1" "$2" "$WORK/record.json" "$NOT_CAREFUL"
  echo "$WORK/record.json"
}
# clean N: the record of one read that found nothing
clean() { record "$1" '{"kind": "read", "answered": ["codex"]}'; }
# the notes of a pull request, and the same notes with the migration a careful request needs
NOTES=$WORK/notes.md
printf '%s\n' '## Decisions' '' 'none' '' '## Left open' '' 'none' '' '## Worth a look' '' '- the one line of the file.' '' '## Filed in the backlog' '' 'none' '' '## Not done' '' 'none' > "$NOTES"
MIG=$WORK/notes-migration.md
cp "$NOTES" "$MIG" && printf '%s\n' '' '## Migration' '' 'none' >> "$MIG"

# The block's last line, which tests/test-lem.sh reads: `all checks passed`, or the count that failed.
finish() {
  results_add_up
  finished=yes
  if [ "$fails" -gt 0 ]; then
    printf '\n%s check(s) failed\n' "$fails"
    exit 1
  fi
  printf '\nall checks passed\n'
}

# the count of the block's checks, before the first of them
collected
