#!/usr/bin/env bash
# Lem's board, offline: one repository whose tasks stand in every lane, written with Lem's own
# scripts (project.py state and log, decisions.py, stories.py), and the pages headless Chrome draws
# from it: the lanes, each task for the owner with where he answers, and the board of one task with
# its decisions, its stories' approval and read, and where its time went.
#
# A real run writes its events minutes apart, and a test writes them in seconds, so the events of
# two tasks get their times moved afterwards (`retime`), the way a run would have spaced them. The
# scripts wrote every other field. LEM_BOARD_SHOTS=DIR also writes pictures of the pages there,
# over the same tasks marked as examples (board.py --demo), at 900, 1400 and 1800 px in a light and a
# dark theme, and prints where the lanes start on a 1400 x 900 window. The README's pictures are of
# a normal afternoon instead: tests/board-showcase.py.
set -euo pipefail

cd "$(dirname "$0")/.."
SCRIPTS=$PWD/skills/lem/scripts
WORK=$(cd "$(mktemp -d)" && pwd -P)
trap 'rm -rf "$WORK"' EXIT
PY=$(python3 -I -c 'import sys; print(sys.executable)')
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1

fails=0
pass() { printf 'ok   %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; fails=$((fails + 1)); }
R=$WORK/shop
STATE=$R/.git/lem
project() { "$PY" -B "$SCRIPTS/project.py" --repo "$R" "$@"; }
decide() { "$PY" -B "$SCRIPTS/decisions.py" --repo "$R" "$@"; }
# CASE: the run that ends badly, which every choice for the owner carries above his card
CASE=(--case $'1. Order 1042 has the gift note "for Ania".\n2. The export writes the note where the choice puts it.\n3. A reader that takes the columns by place reads the note as the total.'
  --case-was derived --cause "Readers of the export take its columns by place.")
stories() { "$PY" -B "$SCRIPTS/stories.py" --repo "$R" "$@"; }
board() { env -u AGTERM_SESSION_ID -u AGTERM_SOCKET -u AGT_SESSION_ID -u AGT_SOCKET "$PY" -B "$SCRIPTS/board.py" --repo "$R" "$@"; }
field() { "$PY" -c 'import json, sys; d = json.load(sys.stdin); print(eval(sys.argv[1], {"d": d}))' "$1"; }
task() { project task-dir "$1" --ask "$2" >/dev/null; }

git init -q -b main "$R" && git -C "$R" config user.name t && git -C "$R" config user.email t@t
echo one > "$R/app.txt" && git -C "$R" add -A && git -C "$R" commit -q -m "chore: start"
project init --base main >/dev/null
# two gate commands: one run of the gate is both, on one tip
"$PY" -I -c 'import re, sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(re.sub(r"(?m)^commands = \[\]$", "commands = [\"make test\", \"make lint\"]", s, count=1))' "$R/.lem/project.toml"
grep -q '^commands = \["make test", "make lint"\]$' "$R/.lem/project.toml" || { printf 'FAIL the fixture: the settings got no gate commands\n'; exit 1; }
git -C "$R" add -A && git -C "$R" commit -q -m "chore: the settings"

# retime SLUG BASE MINUTES...: the events of one task, in the order the scripts wrote them, get the
# times BASE + MINUTES (BASE is an ISO time, or `now`). A decision's own time moves with its event,
# and a choice's deadline stays its wait after its question, as decisions.py writes it.
#
# `now` is one fixed moment, NOW, the next whole minute after the last event of the fixture, and the
# pages are drawn with their clock stopped at it (draw). So a count-down or a share of an open task
# reads the same on a fast run and on a loaded one. Each retime is noted where its task's events end
# and run once NOW is known, before the board is written.
RETIME=$(cat <<'PY'
import json, sys
from datetime import datetime, timedelta, timezone
log, now, slug, base, *minutes = sys.argv[1:]
start = datetime.strptime(now if base == "now" else base, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
rows = [json.loads(line) for line in open(log, encoding="utf-8") if line.strip()]
mine = [row for row in rows if row["task"] == slug]
if len(mine) != len(minutes):
    sys.exit(f"retime: {slug} has {len(mine)} events and {len(minutes)} times were given: {[row['event'] for row in mine]}")
iso = lambda moment: moment.strftime("%Y-%m-%dT%H:%M:%SZ")
for row, offset in zip(mine, minutes):
    moment = start + timedelta(minutes=float(offset))
    row["ts"] = iso(moment)
    if row["event"].startswith("decision."):
        row["at"] = iso(moment)
    if row["event"] == "decision.asked":
        row["deadline"] = iso(moment + timedelta(minutes=row["wait_minutes"]))
open(log, "w", encoding="utf-8").write("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
open(log.removesuffix("jsonl") + "js", "w", encoding="utf-8").write("".join(f"lemEvent({json.dumps(row, ensure_ascii=False)});\n" for row in rows))
PY
)
retime() { printf '%s\n' "$*" >> "$WORK/retimes"; }
retime_all() {
  local args
  while read -r -a args; do "$PY" -I -c "$RETIME" "$STATE/events.jsonl" "$NOW" "${args[@]}"; done < "$WORK/retimes"
}
# past SLUG ID...: the wait of each choice ends in decisions.py's own record, the way fifteen minutes later would find it
past() { "$PY" -I -c 'import json, sys
path = sys.argv[1]
lines = [json.loads(line) for line in open(path)]
for line in lines:
    if line["kind"] == "asked" and str(line["id"]) in sys.argv[2:]: line["deadline"] = "2026-01-01T00:00:00Z"
open(path, "w").write("".join(json.dumps(line) + "\n" for line in lines))' "$STATE/tasks/$1/decisions.jsonl" "${@:2}"; }
# story_file FILE KIND: the stories the owner approves, in the form `stories.py --help` gives
story_file() {
  if [ "$2" = correction ]; then
    printf '%s\n' '## Stories' '' 'Kind: correction, because the request is one sentence.' '' '1. The footer says "Terms", not "Terms and condtions".' > "$1"
  else
    printf '%s\n' '## Stories' '' 'Kind: feature, because the export gets a new column and two readers of it.' '' \
      '1. A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has that text in its row.' \
      '2. An order with no gift note has an empty cell, not the word "None".' > "$1"
  fi
}

# The task with the decisions: stories read and approved, a build with a choice of each kind.
G=gift-note-export
task "$G" "Add the gift note to the CSV export"
story_file "$WORK/gift.md" feature
digest=$(stories digest "$G" --file "$WORK/gift.md" | field 'd["digest"]')
project log "$G" stories.read by=lem asked:=3 answered:=2 'families:=["opus", "sol"]' 'silent:=[{"name": "Accountant, sol", "why": "the model was at capacity"}]' \
  stories:=2 flagged:=1 split:=true "digest=$digest" >/dev/null
stories approve "$G" --file "$WORK/gift.md" >/dev/null
project state "$G" building "lead: builder" >/dev/null
project state "$G" building "plan committed, 3 tasks" >/dev/null
project state "$G" building "task 1 of 3" >/dev/null
decide log "$G" --what "The name of the new column" --chose gift_note --why "the other columns of the export are in snake case" --by lead --undo "rename the column" >/dev/null
decide log "$G" --what "Two notes on one order" --chose "both notes, with a semicolon between them" --why "a merchant reads both" --by personas \
  --said "The merchant and the accountant both picked the semicolon." >/dev/null
decide ask "$G" "${CASE[@]}" --what "Where the note goes in the row" --option "the last column" --option "after the price" --recommended "the last column" \
  --why "an import that reads the columns by place keeps working" --said "The merchant picked the last column, the accountant after the price." >/dev/null
decide answer "$G" 3 --chose "the last column" --words "last, like the other new columns" >/dev/null
project state "$G" building "task 2 of 3" >/dev/null
decide ask "$G" "${CASE[@]}" --what "Email the merchants about the new column" --option "send it" --option "do not send it" --recommended "do not send it" \
  --why "the column is visible in the export" --said "The merchant wants the email, the accountant does not." --irreversible person >/dev/null
decide ask "$G" "${CASE[@]}" --what "The header of the column" --option "Gift note" --option "Note" --recommended "Gift note" --why "it says what the cell holds" --said "The two personas split." >/dev/null
decide ask "$G" "${CASE[@]}" --what "A note longer than the cell" --option "all of it" --option "200 characters" --recommended "all of it" --why "nothing is lost" --said "The two personas split." >/dev/null
past "$G" 5 6
decide timeout "$G" 5 >/dev/null
decide ask "$G" "${CASE[@]}" --what "The note of a cancelled order" --option "keep it" --option "leave it out" --recommended "keep it" --why "the export shows cancelled orders as they were" \
  --said "The merchant would keep it, the accountant is in doubt." >/dev/null
retime "$G" now -60 -52 -51 -45 -44 -40 -35 -34 -31 -30 -27 -26 -25 -10 -5

# The task whose time the card draws: it ran from its stories to a merged pull request, on 10 November.
L=landed-one
task "$L" "Show the order's currency on the invoice"
story_file "$WORK/landed.md" feature
digest=$(stories digest "$L" --file "$WORK/landed.md" | field 'd["digest"]')
project log "$L" stories.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' stories:=2 flagged:=1 split:=false "digest=$digest" >/dev/null
stories approve "$L" --file "$WORK/landed.md" >/dev/null
project state "$L" building "lead: session" >/dev/null
# the talk's start is not in this log, as in a log written before the lead logged it
project log "$L" plan.talk reviewer=codex turns:=19 questions:=4 settled:=3 open:=1 repaired:=2 design:=1 unargued:=1 root:=2 layer:=0 shared:=0 >/dev/null
project state "$L" building "plan committed, 2 tasks" >/dev/null
project state "$L" building "task 1 of 2" >/dev/null
project state "$L" building "task 2 of 2" >/dev/null
decide ask "$L" "${CASE[@]}" --what "The symbol or the code of the currency" --option "the symbol" --option "the code" --recommended "the code" --why "two currencies share the dollar sign" --said "The two personas split." >/dev/null
decide answer "$L" 1 --chose "the code" >/dev/null
project log "$L" task.red ok:=true "digest=$digest" base=0a1b2c3d4 tip=abc123456 'tests:=[]' 'without_a_test:=[]' 'run_without:=[]' >/dev/null
project state "$L" ready "the report is written" >/dev/null
project state "$L" landing "the checks start" >/dev/null
project log "$L" gate "command=make test" exit:=0 "last=12 passed" tip=abc1234 >/dev/null
project log "$L" gate "command=make lint" exit:=0 "last=All checks passed" tip=abc1234 >/dev/null
project log "$L" task.red ok:=true "digest=$digest" base=0a1b2c3d4 tip=abc123456 'tests:=[]' 'without_a_test:=[]' 'run_without:=[]' >/dev/null
project log "$L" review attempt:=1 round:=1 kind=round verdict=clean must_fix:=0 should:=1 nit:=2 'answered:=["codex", "claude"]' 'silent:=[]' \
  'ran:=[{"name": "correctness", "why": "the invoice changes"}]' 'left_out:=[{"name": "security", "why": "no input is read"}]' tip=abc1234 >/dev/null
project log "$L" proposed green:=true 'not_green:=[]' tip=abc1234 >/dev/null
project state "$L" open "pull request https://github.com/acme/shop/pull/7" "green" >/dev/null
project state "$L" landed "main: pull request https://github.com/acme/shop/pull/7 is merged" >/dev/null
retime "$L" 2026-11-10T09:00:00Z 10 22 23 34 35 40 58 65 72 80 82 85 87 88 90 101 103 104 150

# One task for each other thing a lane holds.
task stories-wait "Round the totals of the monthly report"
project state stories-wait held "the stories wait for the owner" >/dev/null
task held-question "Which currency rounds half up"
project state held-question building "lead: builder" >/dev/null
project state held-question held "the investigation waits for one more fact" >/dev/null
task held-choice "Refund the duplicate orders"
project state held-choice building "lead: builder" >/dev/null
decide ask held-choice "${CASE[@]}" --what "Refund the 12 duplicate orders now" --option "refund them" --option "leave them" --recommended "leave them" --why "a refund cannot be taken back" \
  --said "The two personas split." --irreversible money >/dev/null
project state held-choice held "choice 1 waits for the owner" >/dev/null
task open-pr "Sort the export by date"
project state open-pr open "pull request https://github.com/acme/shop/pull/9" "not green: story 1 changed during the build" >/dev/null
task ready-to-land "Fix the typo in the invoice"
project state ready-to-land open "ready to land on main at abc1234" "green" >/dev/null
task plan-for-you "Move the reports to a queue"
project state plan-for-you planned "the plan waits for the owner to read it" >/dev/null
task night-draft "Split the settings page"
project state night-draft drafted "a plan written at night" >/dev/null
task building-one "Cache the product list"
project state building-one building "task 1 of 2" >/dev/null
task queued-one "Add a dark theme"
project state queued-one queued "waits for a free place" >/dev/null
task blocked-one "Upgrade the database driver"
project state blocked-one blocked "the base moved and the rebase has a conflict" >/dev/null
task ready-one "Name the export files by date"
project state ready-one ready "the report is written" >/dev/null
task in-checks "Trim the order notes"
project state in-checks ready "the report is written" >/dev/null
project state in-checks landing "the checks start" >/dev/null
project log in-checks gate "command=make test" exit:=0 "last=9 passed" tip=def5678 >/dev/null
task correction-one "The footer says Terms and condtions"
story_file "$WORK/correction.md" correction
stories approve correction-one --file "$WORK/correction.md" --correction >/dev/null
# a small change has no lead: one builder makes it (stages/new.md, "A small change")
project state correction-one building "small change: one builder" >/dev/null
project log correction-one builder.start "job=the small change" >/dev/null

# A choice taken by a timeout written an hour after its wait ended, and a review logged in the same
# second as the next state block: on 11 November.
T=timed-out
task "$T" "Round the shipping costs"
project state "$T" building "lead: builder" >/dev/null
decide ask "$T" "${CASE[@]}" --what "Round up or to the nearest cent" --option "up" --option "to the nearest cent" --recommended "to the nearest cent" --why "the carrier rounds so" --said "The two personas split." >/dev/null
past "$T" 1
decide timeout "$T" 1 >/dev/null
project state "$T" ready "the report is written" >/dev/null
project state "$T" landing "the checks start" >/dev/null
project log "$T" gate "command=make test" exit:=0 "last=3 passed" tip=abc1234 >/dev/null
project log "$T" task.red ok:=true digest=000000000000 base=0a1b2c3d4 tip=abc123456 'tests:=[]' 'without_a_test:=[]' 'run_without:=[]' >/dev/null
project log "$T" review attempt:=1 round:=1 kind=read verdict=clean must_fix:=0 should:=0 nit:=0 'answered:=["codex"]' 'silent:=[]' 'ran:=[]' 'left_out:=[]' tip=abc1234 >/dev/null
project state "$T" open "ready to land on main at abc1234" "green" >/dev/null
project state "$T" landed "main abc1234" >/dev/null
retime "$T" 2026-11-11T09:00:00Z 0 5 65 70 72 74 76 80 80 90

# One run of the gate in a landing that is still open: its first command failed, and its second ran after it.
task red-gate "Keep the cart for a week"
project state red-gate ready "the report is written" >/dev/null
project state red-gate landing "the checks start" >/dev/null
project log red-gate gate "command=make test" exit:=1 "last=1 failed, 8 passed" tip=fed4321 >/dev/null
project log red-gate gate "command=make lint" exit:=0 "last=All checks passed" tip=fed4321 >/dev/null
retime red-gate now -40 -30 -25 -20

# Stories that nobody was confused by, which still wait for the owner's yes: he left before he gave it.
task clear-read-held "Show the stock on the product page"
printf '%s\n' '## Stories' '' 'Kind: feature, because the page gets a new line.' '' '1. A product with 3 in stock says "3 left".' > "$WORK/stock.md"
digest=$(stories digest clear-read-held --file "$WORK/stock.md" | field 'd["digest"]')
project log clear-read-held stories.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
project state clear-read-held held "the stories wait for the owner" >/dev/null

# A story change of the build that the owner's next approval took over, and one after that approval.
C=changed-then-approved
task "$C" "Name the export file by its date"
printf '%s\n' '## Stories' '' 'Kind: feature, because the file name changes.' '' '1. The export of 3 May is named export-05-03.csv.' '2. A second export that day gets -2.' > "$WORK/name-1.md"
stories approve "$C" --file "$WORK/name-1.md" >/dev/null
project state "$C" building "lead: builder" >/dev/null
decide story "$C" --changed 1 --was "The export of 3 May is named export-05-03.csv." --now "The export of 3 May is named export-2026-05-03.csv." --why "a year keeps the names apart" --by lead >/dev/null
printf '%s\n' '## Stories' '' 'Kind: feature, because the file name changes.' '' '1. The export of 3 May is named export-2026-05-03.csv.' '2. A second export that day gets -2.' > "$WORK/name-2.md"
stories approve "$C" --file "$WORK/name-2.md" >/dev/null
decide story "$C" --changed 2 --was "A second export that day gets -2." --now "A second export that day gets -2, a third -3." --why "the counter goes on" --by lead >/dev/null

# The rare path: the lead's read found nobody confused, and froze the plan's stories.
task rare-path "Show the VAT number on the invoice"
rw=$(project worktree-dir rare-path)
git -C "$R" worktree add -q -b feat/rare-path "$rw" main
mkdir -p "$rw/docs/plans"
printf '%s\n' '# Rare path' '' '## Stories' '' 'Kind: feature, because the invoice gets a new line.' '' '1. An invoice to a company shows its VAT number under its name.' '' '## Tasks' '' '1. The line.' > "$rw/docs/plans/20261116-rare-path.md"
project state rare-path building "lead: builder" >/dev/null
digest=$(stories digest rare-path | field 'd["digest"]')
project log rare-path stories.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
stories approve rare-path --read >/dev/null

# A task the owner holds at the reviewer's trust prompt: a step of his, and no decision.
task trust-prompt "Move the review to Codex"
project state trust-prompt building "lead: session" >/dev/null
project state trust-prompt held "the reviewer's trust prompt waits for the owner's yes" >/dev/null

# The usual path writes the personas' read before the task's first state block.
task read-first "Show the order's weight on the label"
printf '%s\n' '## Stories' '' 'Kind: feature, because the label gets a new line.' '' '1. A parcel of 2.5 kg says "2.5 kg" on its label.' > "$WORK/weight.md"
digest=$(stories digest read-first --file "$WORK/weight.md" | field 'd["digest"]')
project log read-first stories.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null

# The plan's stories and their tests' result, and then a new approval of other stories.
task approved-again "Print the packing slip in German"
printf '%s\n' '## Stories' '' 'Kind: feature, because the slip gets a language.' '' '1. A slip for Berlin is in German.' > "$WORK/slip-1.md"
printf '%s\n' '## Stories' '' 'Kind: feature, because the slip gets a language.' '' '1. A slip for Berlin or Vienna is in German.' > "$WORK/slip-2.md"
stories approve approved-again --file "$WORK/slip-1.md" >/dev/null
project state approved-again building "task 1 of 1" >/dev/null
project log approved-again task.stories kind=feature "why=the slip gets a language." digest=0123456789ab \
  'stories:=[{"n": 1, "text": "A slip for Berlin is in German.", "tests": [{"command": "sh tests/slip.sh", "files": ["tests/slip.sh"]}], "no_test": null}]' >/dev/null
project log approved-again task.red ok:=true digest=0123456789ab base=0a1b2c3d4 tip=abc123456 \
  'tests:=[{"story": 1, "command": "sh tests/slip.sh", "files": ["tests/slip.sh"], "on_branch": 0, "on_base": 1, "problem": null}]' 'without_a_test:=[]' 'run_without:=[]' >/dev/null
stories approve approved-again --file "$WORK/slip-2.md" >/dev/null

# Stories read and approved, changed by the build, then approved again as they were read: nothing is unread.
# Beside it the same without the second approval: the change was not read.
for slug in restored-read unread-change; do
  task "$slug" "Name the carrier on the slip"
  printf '%s\n' '## Stories' '' 'Kind: feature, because the slip gets a line.' '' '1. A DHL parcel says "DHL" on its slip.' > "$WORK/$slug.md"
  digest=$(stories digest "$slug" --file "$WORK/$slug.md" | field 'd["digest"]')
  project log "$slug" stories.read by=lem asked:=2 answered:=2 'families:=["opus", "sol"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
  stories approve "$slug" --file "$WORK/$slug.md" >/dev/null
  project state "$slug" building "lead: builder" >/dev/null
  decide story "$slug" --changed 1 --was 'A DHL parcel says "DHL" on its slip.' --now 'A DHL parcel says "DHL Express" on its slip.' --why "the carrier's own name" --by lead >/dev/null
done
stories approve restored-read --file "$WORK/restored-read.md" >/dev/null

# The two experts' advice on five choices: one they settled while the owner was away, with his answer
# after it, one taken at
# the end of its wait with their shared pick, one at the end of its wait while they split, and two
# that still wait, the first with a shared pick and the second with none. Its state block comes a
# minute after the gift note's, so that the gift note stays the news of the board of all tasks.
X=expert-advice
task "$X" "Print the invoice for the post"
project state "$X" building "lead: builder" >/dev/null
decide ask "$X" "${CASE[@]}" --what "The paper size" --option "A4" --option "Letter" --recommended "Letter" --why "the printer has Letter in its tray" --said "The two personas split." >/dev/null
decide advise "$X" 1 --expert fable --pick A4 --why "every customer of the shop is in Europe, where the post reads A4" >/dev/null
decide advise "$X" 1 --expert astra --pick A4 --why "the envelopes of the shop are cut for A4" >/dev/null
decide settle "$X" 1 --away >/dev/null
decide answer "$X" 1 --chose Letter --words "Letter, it is in the tray" >/dev/null
decide ask "$X" "${CASE[@]}" --what "The color of the logo" --option "black" --option "the green of the shop" --recommended "black" --why "a black logo prints on every printer" --said "The two personas split." >/dev/null
decide advise "$X" 2 --expert fable --pick "the green of the shop" --why "the invoice is a page of the shop" >/dev/null
decide advise "$X" 2 --expert astra --pick "the green of the shop" --why "the printer prints in color" >/dev/null
decide ask "$X" "${CASE[@]}" --what "The order number on the page" --option "at the top" --option "at the foot" --recommended "at the top" --why "the post office reads the top first" --said "The two personas split." >/dev/null
decide advise "$X" 3 --expert fable --pick "at the top" --why "a reader looks for it first" >/dev/null
decide advise "$X" 3 --expert astra --pick "at the foot" --why "the top holds the address window" >/dev/null
past "$X" 2 3
decide timeout "$X" 2 >/dev/null
decide timeout "$X" 3 >/dev/null
decide ask "$X" "${CASE[@]}" --what "The font of the invoice" --option "serif" --option "sans" --recommended "sans" --why "it reads well on a screen" --said "The two personas split." >/dev/null
decide advise "$X" 4 --expert fable --pick serif --why "a printed invoice reads better in serif" >/dev/null
decide advise "$X" 4 --expert astra --pick serif --why "the letters of the shop are in serif" >/dev/null
decide ask "$X" "${CASE[@]}" --what "The size of the total" --option "12 pt" --option "14 pt" --recommended "14 pt" --why "a reader finds the total first" --said "The two personas split." >/dev/null
decide advise "$X" 5 --expert fable --none --why "the total should be bold, not bigger" >/dev/null
decide advise "$X" 5 --expert astra --pick "12 pt" --why "the other lines are 12 pt" >/dev/null
retime "$X" now -50 -49 -48 -47 -46 -45.5 -45 -44 -43 -42 -41 -40 -29 -26 -6 -5 -4 -3 -2 -1

# A landing whose polish pass is logged and whose checks run, and one that has only started.
P=polished
task "$P" "Name the invoice files by order"
project state "$P" ready "the report is written" >/dev/null
project state "$P" landing "the checks start" >/dev/null
project log "$P" polish before=abc1234 after=def5678 commits:=2 'filed:=["docs/backlog/invoice-footer-typo.md"]' >/dev/null
# the review read the diff against the topics and called it careful, which the plan did not
project log "$P" careful.missed round:=1 "why=the file name holds the order's total, which a customer pays" >/dev/null
retime "$P" now -40 -30 -12 -12
task landing-starts "Print the order date on the invoice"
project state landing-starts ready "the report is written" >/dev/null
project state landing-starts landing "the checks start" >/dev/null
retime landing-starts now -20 -10

# A plan talk from its start to its record, on 12 November, and one that has started and has no record yet.
K=talked-plan
task "$K" "Move the price rounding into one place"
project state "$K" building "lead: session" >/dev/null
project log "$K" plan.talk.start reviewer=codex >/dev/null
project log "$K" plan.talk reviewer=codex turns:=7 questions:=3 settled:=2 open:=1 repaired:=2 design:=1 unargued:=2 root:=1 layer:=1 shared:=1 >/dev/null
project state "$K" building "plan committed, 4 tasks" >/dev/null
project state "$K" dropped "the test is over" >/dev/null
retime "$K" 2026-11-12T09:00:00Z 0 2 20 21 25
task talk-runs "Split the invoice service"
project state talk-runs building "lead: session" >/dev/null
project log talk-runs plan.talk.start reviewer=claude >/dev/null
retime talk-runs now -70 -10
# A careful plan's talk in a companion that Lem opened, then the builder lead that builds it.
M=talk-then-build
task "$M" "Round the prices once"
project state "$M" building "lead: session" >/dev/null
project state "$M" building "session: C0FFEE" >/dev/null
project log "$M" plan.talk.start reviewer=codex >/dev/null
project log "$M" plan.talk reviewer=codex turns:=5 questions:=2 settled:=2 open:=0 repaired:=2 design:=0 unargued:=0 root:=0 layer:=1 shared:=0 >/dev/null
project state "$M" planned "the plan talk is done" >/dev/null
project state "$M" building "lead: builder" >/dev/null
project state "$M" building "plan committed, 4 tasks" >/dev/null
project state "$M" building "task 1 of 4" >/dev/null
retime "$M" now -60 -59 -58 -40 -39 -38 -37 -36

# A bug that its investigation found to be none: the task ends answered, with its report.
A=refund-shows-zero
task "$A" "Invoices show 0 after a refund"
project state "$A" building "a builder reproduces the bug and finds its cause" "investigation: bug" "kind: bug, because the ask says the total is wrong today" >/dev/null
printf '%s\n' '# Investigation' '' 'Reproduced: yes, with tests/refund.sh.' > "$STATE/tasks/$A/investigation.md"
project log "$A" investigation kind=bug call=not-a-bug "line=a refund is a credit note, and the invoice shows what is left to pay" where=billing/invoice.py:total reproduced:=true >/dev/null
project state "$A" answered "not a bug: the invoice shows what is left to pay" "report: investigation.md" >/dev/null
retime "$A" now -30 -12 -11
# A bug whose investigation runs.
task cart-total-wrong "The cart total is wrong since yesterday"
project state cart-total-wrong building "a builder reproduces the bug and finds its cause" "investigation: bug" "kind: bug, because the ask says the total is wrong since yesterday" >/dev/null
project log cart-total-wrong investigation.start kind=bug >/dev/null

# A feature whose every stage logged its start (SKILL.md), from the interview to the merge, on 13
# November: the time card draws each span from its start to the event that ends it.
S=started-stages
task "$S" "Print the order date on the invoice"
printf '%s\n' '## Stories' '' 'Kind: feature, because the invoice gets a line.' '' '1. The invoice of order 1042, placed on 3 May, says "Ordered 3 May".' > "$WORK/started.md"
digest=$(stories digest "$S" --file "$WORK/started.md" | field 'd["digest"]')
project state "$S" held "the interview waits for the owner" "kind: feature, because the invoice gets a line" >/dev/null
project log "$S" scout.start >/dev/null
project log "$S" interview.start >/dev/null
project log "$S" scout >/dev/null
project log "$S" stories.read.start by=lem >/dev/null
project log "$S" stories.read by=lem asked:=3 answered:=3 'families:=["opus", "sol"]' 'silent:=[]' stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
project state "$S" held "the stories wait for the owner" >/dev/null
stories approve "$S" --file "$WORK/started.md" >/dev/null
project state "$S" building "lead: builder" >/dev/null
project state "$S" building "plan committed, 2 tasks" >/dev/null
project state "$S" building "task 1 of 2" >/dev/null
project log "$S" builder.start "job=task 1 of 2" >/dev/null
project state "$S" building "task 2 of 2" >/dev/null
project log "$S" builder.start "job=task 2 of 2" >/dev/null
project state "$S" ready "the report is written" >/dev/null
project state "$S" landing "the checks start" >/dev/null
project log "$S" polish.start before=abc123456 >/dev/null
project log "$S" polish before=abc1234 after=def5678 commits:=1 'filed:=[]' >/dev/null
project log "$S" gate.start tip=def567890 commands:=2 >/dev/null
project log "$S" gate "command=make test" exit:=0 "last=14 passed" tip=def5678 >/dev/null
project log "$S" gate "command=make lint" exit:=0 "last=All checks passed" tip=def5678 >/dev/null
project log "$S" task.red ok:=true "digest=$digest" base=0a1b2c3d4 tip=def567890 'tests:=[]' 'without_a_test:=[]' 'run_without:=[]' >/dev/null
project log "$S" review.start attempt:=1 floor=read >/dev/null
project log "$S" review attempt:=1 round:=1 kind=read verdict=clean must_fix:=0 should:=0 nit:=0 'answered:=["codex"]' 'silent:=[]' 'ran:=[]' 'left_out:=[]' tip=def5678 >/dev/null
project log "$S" proposed green:=true 'not_green:=[]' tip=def5678 >/dev/null
project state "$S" open "pull request https://github.com/acme/shop/pull/12" "green" >/dev/null
project state "$S" landed "main: pull request https://github.com/acme/shop/pull/12 is merged" >/dev/null
retime "$S" 2026-11-13T09:00:00Z 0 1 2 6 20 25 25 30 31 40 41 42 60 61 80 81 83 90 91 94 95 96 97 101 102 102 110
# A landing whose checks started and have no result yet.
task gate-runs "Trim the cart notes"
project state gate-runs ready "the report is written" >/dev/null
project state gate-runs landing "the checks start" >/dev/null
project log gate-runs gate.start tip=abc123456 commands:=2 >/dev/null
retime gate-runs now -20 -10 -5

# A read of the stories in which no persona answered, and the stories still wait for the owner.
task silent-read "Show the delivery date on the order page"
printf '%s\n' '## Stories' '' 'Kind: feature, because the page gets a new line.' '' '1. An order shipped on 3 May says "arrives 5 May".' > "$WORK/delivery.md"
digest=$(stories digest silent-read --file "$WORK/delivery.md" | field 'd["digest"]')
project log silent-read stories.read by=lem asked:=2 answered:=0 'families:=[]' \
  'silent:=[{"name": "Merchant, opus", "why": "the model timed out"}, {"name": "Accountant, sol", "why": "the model was at capacity"}]' \
  stories:=1 flagged:=0 split:=false "digest=$digest" >/dev/null
project state silent-read held "the stories wait for the owner" >/dev/null
# A task queued behind another one that names the same thing (stages/new.md, step 6).
task queued-after "Cache the product images"
project state queued-after queued "waits for the task that caches the product list" "after: building-one" >/dev/null

# The backlog of the main checkout: an item whose place is gone, one whose place is there, one whose
# file cannot be read by anyone, and one decided against.
mkdir -p "$R/docs/backlog"
printf '%s\n' '---' 'worth: yes' 'where: billing/gone.py:total' 'added: 2026-11-01' '---' '' '# The total of a refund is rounded twice' '' 'Seen in a review.' > "$R/docs/backlog/refund-rounded-twice.md"
printf '%s\n' '---' 'worth: later' 'where: app.txt' 'added: 2026-11-02' '---' '' '# The app file has one line' > "$R/docs/backlog/app-one-line.md"
printf '%s\n' '---' 'worth: yes' 'where: locked.txt:secret' 'added: 2026-11-03' '---' '' '# The locked file' > "$R/docs/backlog/locked-file.md"
printf '%s\n' '---' 'worth: no' 'added: 2026-11-04' '---' '' '# Rewrite the shop in another language' '' 'Decided against: the shop works.' > "$R/docs/backlog/rewrite-the-shop.md"
echo secret > "$R/locked.txt"
git -C "$R" add -A && git -C "$R" commit -q -m "docs: the backlog"
chmod 000 "$R/locked.txt"

NOW=$("$PY" -I -c 'from datetime import datetime, timedelta, timezone; print((datetime.now(timezone.utc) + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:00Z"))')
retime_all

if [ "$(grep -c '"event": "decision.' "$STATE/events.jsonl")" = 37 ] && [ "$(grep -c '"task": "gift-note-export"' "$STATE/events.js")" = 15 ]; then
  pass "the fixture is written by Lem's scripts: every decision is an event, and the board's copy of the log holds the moved times"
else
  fail "the fixture: $(grep -c '"event": "decision.' "$STATE/events.jsonl") decision events"
fi

# An item whose place is a file nobody can read is shown with that problem, and the board of the
# other items is still written.
if board --no-open > "$WORK/board.json" 2> "$WORK/board.err" \
  && why=$("$PY" -I -c 'import json, re, sys
feed = json.loads(re.fullmatch(r"lemBacklog\((.*)\);\n", open(sys.argv[1], encoding="utf-8").read(), re.S).group(1))
problems = {item["slug"]: item["where_problem"] for item in feed["items"]}
want = {"locked-file": "the file cannot be read", "refund-rounded-twice": "the file is not there", "app-one-line": "", "rewrite-the-shop": ""}
print("" if problems == want else f"the items: {problems}")
sys.exit(problems != want)' "$STATE/backlog.js"); then
  pass "a backlog item whose place is a file nobody can read says so, and the board of the other items is written"
else
  fail "a backlog item with an unreadable place: ${why:-$(tail -1 "$WORK/board.err")}"
fi
for slug in "$G" "$L" correction-one "$T" red-gate clear-read-held "$C" rare-path read-first approved-again restored-read unread-change "$X" "$P" landing-starts "$K" talk-runs "$M" "$A" cart-total-wrong silent-read queued-after \
  "$S" gate-runs held-choice held-question trust-prompt stories-wait plan-for-you night-draft open-pr ready-to-land; do board --no-open --task "$slug" >/dev/null; done

SHOWN=$(cat <<'PY'
import re, sys
from html.parser import HTMLParser
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip = 0; self.text = []; self.title = ""; self.in_title = False
    def handle_starttag(self, tag, attrs):
        self.skip += tag in ("script", "style"); self.in_title = tag == "title" and not self.skip
    def handle_endtag(self, tag):
        self.skip -= tag in ("script", "style"); self.in_title = False
    def handle_data(self, data):
        if self.in_title and not self.title: self.title = data
        elif not self.skip: self.text.append(data)
p = P(); p.feed(open(sys.argv[1], encoding="utf-8").read())
shown = " ".join(" ".join(p.text).split())
# "!TEXT" must not be on the page, "~PATTERN" is a regular expression that must match it, and
# "=N:TEXT" is a text that is on the page N times
missing = [want for want in sys.argv[2:] if want[0] not in "!~=" and want not in shown and want not in p.title]
for want in [w for w in sys.argv[2:] if w.startswith("=")]:
    n, _, text = want[1:].partition(":")
    if shown.count(text) != int(n): missing.append(f"{text!r} is on the page {shown.count(text)} times, not {n}")
missing += [f"no match of {want[1:]!r}" for want in sys.argv[2:] if want.startswith("~") and not re.search(want[1:], shown)]
missing += [f"no {want[1:]!r}" for want in sys.argv[2:] if want.startswith("!") and (want[1:] in shown or want[1:] in p.title)]
if "PROBLEM" in p.title or "does not parse" in shown: missing.append(f"no problem on the page (title {p.title!r})")
print("; ".join(missing))
sys.exit(bool(missing))
PY
)
# TIMECARD DOM 'ROW|ROW|...' 'ROW=TOTAL · SHARE' ...: the rows of the time card, in order, and its legend, item for item
TIMECARD=$(cat <<'PY'
import html, re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
rows = [html.unescape(row) for row in re.findall(r'<text class="lane-label"[^>]*>([^<]*)</text>', dom)]
area = dom[dom.index('id="legend"'):]
area = area[:area.index("</div>")]
legend = {html.unescape(label): html.unescape(value) for label, value in re.findall(r"<span[^>]*><i[^>]*></i>(.*?)<em>(.*?)</em></span>", area)}
want = dict(item.split("=", 1) for item in sys.argv[3:])
# a value that starts with "~" is a regular expression, for a total that grows with the clock
same = set(legend) == set(want) and all(re.fullmatch(value[1:], legend[label]) if value.startswith("~") else value == legend[label] for label, value in want.items())
wrong = ([f"the rows are {rows}"] if rows != sys.argv[2].split("|") else []) + ([f"the legend is {legend}"] if not same else [])
print("; ".join(wrong))
sys.exit(bool(wrong))
PY
)
# BANNERS DOM PATTERN ...: each regular expression matches the text of one banner, and "!PATTERN"
# none. A banner folded under the first ones counts too; "#N" says that N banners are shown, and
# "=PATTERN" matches the text of the line that unfolds the rest.
BANNERS=$(cat <<'PY'
import re, sys
from html.parser import HTMLParser
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack = []; self.banners = []; self.fold = []; self.inside = None; self.done = False
    def handle_starttag(self, tag, attrs):
        if tag in VOID or self.done: return
        a = dict(attrs); cls = (a.get("class") or "").split()
        if a.get("id") == "banners": self.inside = len(self.stack)
        hidden = "hidden" in a or any(n["hidden"] for n in self.stack)
        node = {"tag": tag, "hidden": hidden, "banner": None, "fold": None}
        if self.inside is not None and tag == "div" and "banner" in cls and not any(n["banner"] is not None for n in self.stack):
            node["banner"] = {"text": [], "shown": not hidden}; self.banners.append(node["banner"])
        if self.inside is not None and "banner-fold" in cls:
            node["fold"] = []; self.fold.append(node["fold"])
        self.stack.append(node)
    def handle_endtag(self, tag):
        if tag in VOID or self.done or not self.stack: return
        self.stack.pop()
        if self.inside is not None and len(self.stack) == self.inside: self.done = True
    def handle_data(self, data):
        for n in self.stack:
            if n["banner"] is not None: n["banner"]["text"].append(data)
            if n["fold"] is not None: n["fold"].append(data)
p = P(); p.feed(open(sys.argv[1], encoding="utf-8").read())
banners = [" ".join(" ".join(b["text"]).split()) for b in p.banners]
shown = sum(b["shown"] for b in p.banners)
fold = " ".join(" ".join(" ".join(f) for f in p.fold).split())
wrong = []
for want in sys.argv[2:]:
    if want.startswith("#"):
        if shown != int(want[1:]): wrong.append(f"{shown} banners are shown, not {want[1:]}")
    elif want.startswith("="):
        if not re.search(want[1:], fold): wrong.append(f"the fold says {fold!r}, not {want[1:]!r}")
    elif want.startswith("!"):
        if any(re.search(want[1:], text) for text in banners): wrong.append(f"a banner matches {want[1:]!r}")
    elif not any(re.search(want, text) for text in banners):
        wrong.append(f"no banner matches {want!r}")
print("; ".join(wrong) + (f" (the banners: {banners})" if wrong else ""))
sys.exit(bool(wrong))
PY
)
# LANES DOM 'LANE=TITLE|LINE' ...: the card of TITLE is in LANE, and its one line of where the task
# is, is LINE. "#counts": the head of each lane counts its cards and the older ones it names.
# "#short": every card has one such line and no paragraph of where the owner answers.
LANES=$(cat <<'PY'
import html, re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
text = lambda s: " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())
lanes, counts, lines = {}, {}, {}
for part in re.split(r'<div class="lane a-', dom)[1:]:
    title = text(re.search(r'<div class="lane-head">(.*?)<em', part, re.S).group(1))
    head = text(re.search(r'<div class="lane-head">.*?<em[^>]*>(.*?)</em>', part, re.S).group(1))
    older = re.search(r'<div class="more">and (\d+) older', part)
    cards = {}
    for card in re.split(r'<button class="tcard ', part)[1:]:
        name = text(re.search(r'<div class="tc-title">(.*?)</div>', card, re.S).group(1))
        said = [text(x) for x in re.findall(r'<div class="tc-text">(.*?)</div>', card, re.S)]
        cards[name] = said[0] if said else ""
        lines[name] = (len(said), 'class="tc-where"' in card)
    lanes[title] = cards
    counts[title] = (head, len(cards) + int(older.group(1) if older else 0))
wrong = []
if "#counts" in sys.argv[2:]:
    wrong += [f"the head of {lane!r} says {head!r} over {n} cards" for lane, (head, n) in counts.items() if head != str(n)]
if "#short" in sys.argv[2:]:
    wrong += [f"{name!r} has {n} lines and {'a' if where else 'no'} paragraph of where to answer" for name, (n, where) in lines.items() if n != 1 or where]
for want in [w for w in sys.argv[2:] if not w.startswith("#")]:
    lane, _, rest = want.partition("=")
    name, _, where = rest.partition("|")
    if name not in lanes.get(lane, {}):
        wrong.append(f"{name!r} is not in {lane!r} ({ {k: list(v) for k, v in lanes.items()} })")
    elif where and lanes[lane][name] != where:
        wrong.append(f"{name!r} says {lanes[lane][name]!r}, not {where!r}")
print("; ".join(wrong))
sys.exit(bool(wrong))
PY
)
# ROWS DOM ID 'ANCHOR|WANT|...' ...: a row of the element ID (one of its children) holds the text
# ANCHOR, and that same row holds each WANT: a text, "!TEXT" that it must not hold, "~PATTERN" a
# regular expression, "@CLASS" a class of the row. So a text of another row cannot stand in.
ROWS=$(cat <<'PY'
import re, sys
from html.parser import HTMLParser
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
class P(HTMLParser):
    def __init__(self, target):
        super().__init__(); self.target = target; self.depth = 0; self.inside = None; self.done = False; self.rows = []
    def handle_starttag(self, tag, attrs):
        if tag in VOID: return
        self.depth += 1
        if self.inside is None and not self.done and dict(attrs).get("id") == self.target: self.inside = self.depth
        elif self.inside is not None and self.depth == self.inside + 1: self.rows.append({"cls": (dict(attrs).get("class") or "").split(), "text": []})
    def handle_endtag(self, tag):
        if tag in VOID: return
        if self.inside is not None and self.depth == self.inside: self.inside = None; self.done = True
        self.depth -= 1
    def handle_data(self, data):
        if self.inside is not None and self.depth > self.inside and self.rows: self.rows[-1]["text"].append(data)
p = P(sys.argv[2]); p.feed(open(sys.argv[1], encoding="utf-8").read())
rows = [{"cls": r["cls"], "text": " ".join(" ".join(r["text"]).split())} for r in p.rows]
wrong = []
for want in sys.argv[3:]:
    anchor, *needs = want.split("|")
    row = next((r for r in rows if anchor in r["text"]), None)
    if row is None:
        wrong.append(f"no row of #{sys.argv[2]} holds {anchor!r} (its rows: {[r['text'][:90] for r in rows]})")
        continue
    for need in needs:
        ok = (need[1:] in row["cls"]) if need.startswith("@") else (need[1:] not in row["text"]) if need.startswith("!") \
            else bool(re.search(need[1:], row["text"])) if need.startswith("~") else need in row["text"]
        if not ok: wrong.append(f"the row {anchor!r} does not hold {need!r}: {row['text']!r} (class {' '.join(row['cls'])})")
print("; ".join(wrong))
sys.exit(bool(wrong))
PY
)

chrome=""
for c in google-chrome chromium chromium-browser "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
  if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then chrome=$c; break; fi
done
# Every clock time on the pages is in UTC, so a check of one reads the same on every machine.
headless() { TZ=UTC "$chrome" --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" "$@" 2>/dev/null || true; }
# draw PAGE [TAB]: the page as Chrome leaves it, into PAGE.dom (PAGE-TAB.dom for a tab), with its clock
# stopped at NOW: a script before the page's own makes Date.now() give NOW. board.py writes the page
# again at every run, so each draw puts the script in once more.
STOP=$(cat <<'PY'
import sys
page, now = sys.argv[1:]
text = open(page, encoding="utf-8").read()
mark = "<script>/* the fixture's clock */"
if mark not in text:
    text = text.replace("<head>", f'<head>{mark} {{ const fixed = Date.parse("{now}"); Date.now = () => fixed; }}</script>', 1)
open(page, "w", encoding="utf-8").write(text)
PY
)
draw() {
  "$PY" -I -c "$STOP" "$STATE/$1.html" "$NOW"
  headless --virtual-time-budget=5000 --dump-dom "file://$STATE/$1.html${2:+#$2}" > "$WORK/$1${2:+-$2}.dom"
}

if [ -z "$chrome" ]; then
  printf 'SKIP the board pages: no Chrome or Chromium found\n'
else
  draw board
fi
if [ -n "$chrome" ] && [ ! -s "$WORK/board.dom" ]; then
  # A Chrome that cannot start (a sandbox that forbids it) says nothing about the page.
  printf 'SKIP the board pages: %s printed no page\n' "$chrome"
elif [ -n "$chrome" ]; then
  # shellcheck disable=SC1111  # the curly quotes around a state's own line are the page's
  if why=$("$PY" -I -B -c "$LANES" "$WORK/board.dom" "#short" \
    "Waits for you=Gift note export|Choice 7 waits for you: The note of a cancelled order · 10m left" \
    "Waits for you=Held choice|Choice 1 waits for you: Refund the 12 duplicate orders now · no end" \
    "Waits for you=Held question|The investigation waits for one more fact" \
    "Waits for you=Trust prompt|The reviewer's trust prompt waits for your yes" \
    "Building=Approved again" "Building=Restored read" "Building=Unread change" \
    "Waits for you=Clear read held|The stories wait for you" "Waits for you=Stories wait|The stories wait for you" "Waits for you=Silent read|The stories wait for you" \
    "Waits for you=Plan for you|Planned: the plan waits for you to read it" \
    "Waits for you=Night draft|Drafted at night: a plan written at night" \
    "Waits for you=Open pr|Waits for the merge: pull request #9" \
    "Waits for you=Ready to land|Waits for the merge: ready to land on main at abc1234" \
    "Building=Building one|Task 1 of 2" "Building=Queued one|Queued: waits for a free place" "Building=Blocked one|Blocked: the base moved and the rebase has a conflict" \
    "Building=Correction one|One builder makes the change" "Building=Changed then approved" "Building=Rare path" \
    "Checks and review=Ready one|Ready for its checks: the report is written" "Checks and review=In checks|The checks start" "Checks and review=Red gate" \
    "Done=Landed one|Landed: main: pull request #7 is merged" "Done=Timed out" "Building=Queued after"); then
    pass "each task is in the lane of who acts, and its card says in one line where it is, in your words and not the lane's title again; no card has a paragraph of where you answer"
  else
    fail "the lanes: $why"
  fi
  # Where you answer is on the task's own board: a choice, one more fact, a step of his, the stories,
  # a plan, a draft, a pull request, a branch to land.
  wheres=()
  # shellcheck disable=SC1111,SC1112  # the curly quotes are the page's
  for want in "held-question|It waits on what its state says: “the investigation waits for one more fact”. Lem tells you in its session what to do and where." \
    "trust-prompt|It waits on what its state says: “the reviewer's trust prompt waits for your yes”. Lem tells you in its session what to do and where." \
    "held-choice|Lem puts choice 1 to you as a page in its session. Answer it there: it waits for your word, with no end." \
    "stories-wait|Lem shows you the stories, with the personas’ read on top, as a page in its session. Approve or change them there." \
    "silent-read|Lem shows you the stories as a page in its session. No persona answered the read of them. Approve or change them there." \
    "plan-for-you|Read the plan, then tell Lem in its session: build it or drop it." \
    "night-draft|Tell Lem in its session: /lem build night-draft, or drop it." \
    "open-pr|Merge the pull request, or tell Lem in its session to land it." \
    "ready-to-land|Tell Lem in its session to land it."; do
    draw "task-${want%%|*}"
    why=$("$PY" -I -B -c "$ROWS" "$WORK/task-${want%%|*}.dom" now "Where you answer:|${want#*|}") || wheres+=("${want%%|*}: $why")
  done
  if [ "${#wheres[@]}" -eq 0 ]; then
    pass "each task that waits for you says on its own board where you answer: a choice, one more fact, a step of yours, the stories, a plan, a draft, a pull request, a branch to land"
  else
    fail "where you answer: ${wheres[*]}"
  fi
  # The head of a lane counts the cards under it, and the page's title counts what the lanes hold.
  if why=$("$PY" -I -B -c "$LANES" "$WORK/board.dom" "#counts") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/board.dom" "12 wait for you, 10 build, 6 in checks and review, 2 queued, 1 blocked"); then
    pass "the head of each lane counts the cards under it, and the title's numbers add up to the lanes: a task that builds while a choice waits for the owner is counted once, where it waits"
  else
    fail "the counts of the lanes: $why"
  fi
  # Each banner is read alone, so that a card's text elsewhere on the page cannot stand in for one.
  # The most pressing wait, choice 7, is the large card's, with where you answer, and no banner's.
  if why=$("$PY" -I -B -c "$BANNERS" "$WORK/board.dom" \
    "^Choice 4 waits for you: Gift note export · Email the merchants about the new column · no end: no timeout takes it$" \
    "^Choice 1 waits for you: Held choice · Refund the 12 duplicate orders now · no end: no timeout takes it$" \
    "^Waits for you: Stories wait · the stories wait for you · [0-9][0-9ms ]*$" "!^Choice 7" "!^Choice 6" "!Choice 5 waits for you: Gift note export" "!^Waits for you: Held choice" \
    "!Lem puts" "!Lem shows you" "!Answer it there" "!^Choice [123] waits for you: Expert advice") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/board.dom" now \
      "You · choice 7 of the task|Gift note export|The note of a cancelled order|10:00|Where you answer: Lem puts choice 7 to you as a page in its session. Answer it there before its wait ends; then the build goes on with the recommended action.") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/board.dom" "=1:Lem puts choice 7 to you" "=0:Lem puts choice 4 to you" "=0:Lem shows you the stories" "!Demo data"); then
    pass "the large card has the most pressing wait with where you answer, said once on the page; the banners are the waits after it, one line each with its count-down, or no end for an irreversible step, and none whose wait is over"
  else
    fail "the banners: $why"
  fi
  # Ten banners would fill a screen: the first three are shown, and one line counts the rest.
  if why=$("$PY" -I -B -c "$BANNERS" "$WORK/board.dom" "#3" "=^7 more: 6 wait for you, 1 blocked · Show them" "^Blocked: Blocked one"); then
    pass "past three banners the rest fold under one line that counts what waits for the owner and what is blocked, so the lanes stay on the first screen"
  else
    fail "the fold of the banners: $why"
  fi
  # Each number once: the title and the lanes count the tasks; a chip says the places, in a warning
  # color at the limit, and what no other place says. The board of all tasks has no ring and no grid.
  if ! grep -q 'class="ring-wrap"' "$WORK/board.dom" && ! grep -q 'class="stats"' "$WORK/board.dom" \
    && grep -Eq '<span class="chip you"[^>]*>(<svg[^>]*>.*</svg>)?<b>17 of 4</b> places</span>' "$WORK/board.dom" \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/board.dom" "2 proposed · 1 not green" "!landed today" "!places taken" "!wait for the merge"); then
    pass "the board of all tasks says each number once: no ring and no grid of counts, the places as a chip in a warning color at the limit, and the proposed requests that are not green"
  else
    fail "the numbers of the board: ${why:-a ring, a grid or the chip of the places}"
  fi

  draw "task-$G"
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$G.dom" "Decisions" "2 wait for you · 1 with the wait over · 4 taken" \
    "Choice 7 waits for you: The note of a cancelled order" "options: keep it · leave it out" "recommended: keep it, because the export shows cancelled orders as they were" \
    "the personas: The merchant would keep it, the accountant is in doubt." "Its wait ends at " 'then the build goes on with “keep it”, the recommended option, unless both experts pick one option before then.' "10m left" \
    "Choice 4 waits for you: Email the merchants about the new column" "It waits for your answer, with no end: it sends something to a person, so no timeout takes it." "no end" \
    "Choice 6, its wait is over: A note longer than the cell" 'and no timeout is written yet: the build goes on with “all of it”, the recommended option, as no expert advised.' "wait over" \
    "5. The header of the column → Gift note" "taken by the timeout at " "no answer came in 15 minutes. The recommended action stands, and the pull request is not green for it." \
    "1. The name of the new column → gift_note" "taken by the agent, because the other columns of the export are in snake case" "to undo: rename the column" \
    "2. Two notes on one order → both notes, with a semicolon between them" "taken by the personas, because a merchant reads both" "the personas: The merchant and the accountant both picked the semicolon." \
    "3. Where the note goes in the row → the last column" 'answered by you: “last, like the other new columns”' \
    "2 choices wait for you" "left of the wait, until "); then
    pass "the board of one task has a Decisions card: each choice that waits with the end of its wait and its count-down, an irreversible one with no end, one whose wait is over, one taken by the timeout, and each taken one with what, by whom and why"
  else
    fail "the Decisions card: $why"
  fi
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$G.dom" "The two model families split on a story." "1 of 2 stories flagged" \
    "read by 2 of 3 personas, two model families (opus, sol), run by Lem" "no answer from Accountant, sol (the model was at capacity)" "Approved by you after the personas’ read" \
    'A CSV export holds the gift note of an order: order 1042 with the note "for Ania" has that text in its row.' "no test yet: the agent adds its tests in the plan") \
    && "$PY" -I -c 'import re, sys
dom = re.sub(r"<[^>]+>", " ", open(sys.argv[1], encoding="utf-8").read())
sys.exit(not dom.index("The two model families split") < dom.index("1 of 2 stories flagged") < dom.index("read by 2 of 3 personas"))' "$WORK/task-$G.dom"; then
    pass "the Stories card shows the personas' read with a split between the families said first, who answered of how many, who did not and why, and the owner's approval after it"
  else
    fail "the Stories card: ${why:-the split is not said first}"
  fi
  draw task-correction-one
  # shellcheck disable=SC1112  # the curly quotes are the page's
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-correction-one.dom" "Taken as a small change: Lem approved its one story in your name" \
    'You may still say “this is a feature”' "The personas do not read the one story of a small change." "small change, because the request is one sentence." \
    "One builder makes the change" "!a correction" "!correction, because"); then
    pass "a small change's Stories card says that Lem approved its one story in your name, that you may call it a feature, and that the personas do not read it, in the words the stages use"
  else
    fail "a small change's Stories card: $why"
  fi
  # A small change has one builder and no lead: the builders' row from its start, and phases with no
  # stories to wait in and no plan.
  if grep -q 'data-head="The builders · The small change"' "$WORK/task-correction-one.dom" \
    && ! grep -q 'data-head="The agent · It plans the task"' "$WORK/task-correction-one.dom" \
    && why=$("$PY" -I -c 'import re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
phases = re.findall(r"class=\"phase ?(cur|past)?\"><i[^>]*></i>([^<]*)<", dom)
names = [name for _, name in phases]
ok = names == ["Change", "Checks", "Review", "Proposed", "Landed"] and phases[0][0] == "cur"
print("" if ok else f"the phases are {phases}")
sys.exit(not ok)' "$WORK/task-correction-one.dom"); then
    pass "a small change is drawn as one builder's work, on the builders' row, and its phases are the change, the checks, the review, proposed and landed"
  else
    fail "a small change on the board: ${why:-its span on the time card}"
  fi

  draw "task-$L"
  # The rows and the legend are read from the card itself, so that a name elsewhere on the page cannot stand in for a row.
  if why=$("$PY" -I -B -c "$TIMECARD" "$WORK/task-$L.dom" "You|Lem|The agent|The builders|The personas|The checks|The review" \
    "You=1h 05m · 46%" "Lem=6m 00s · 4%" "The agent=17m · 12%" "The builders=42m · 30%" "The checks=5m 00s · 4%" "The review=11m · 8%") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$L.dom" "Where the time went" "Stories" "Plan" "T1" "T2" "Checks" "PR") \
    && ! grep -q 'class="nowline"' "$WORK/task-$L.dom" && grep -q 'class="ring-wrap"' "$WORK/task-$L.dom"; then
    pass "the time card of a task has a row for each actor that held its work and a band for each stage and plan task, and its legend gives each actor's total and share of the task's time"
  else
    fail "the time card: $why"
  fi
  # Under the card one short line; what the card leaves out is the hover of its legend.
  if grep -q '<div id="tl-note" class="tl-note">Each row is who held the work; a band is a stage. Hover the legend for how the shares add up.</div>' "$WORK/task-$L.dom" \
    && grep -q 'id="legend" class="legend" title="Rows overlap where the build goes on while a choice waits for you' "$WORK/task-$L.dom"; then
    pass "the time card's note is one short line, and the rest of what it said is the hover of the legend"
  else
    fail "the note of the time card: $(grep -o '<div id="tl-note"[^<]*' "$WORK/task-$L.dom")"
  fi
  # Each stage whose start is logged is a span from its start to the event that ends it, on the row
  # of who held the work, and the rest of each block is the coordinator's.
  draw "task-$S"
  # shellcheck disable=SC1112  # the curly quote is the page's
  if why=$("$PY" -I -B -c "$TIMECARD" "$WORK/task-$S.dom" "You|Lem|The agent|The builders|The personas|The checks|The review" \
      "You=33m · 30%" "Lem=6m 00s · 5%" "The agent=12m · 11%" "The builders=49m · 45%" "The personas=5m 00s · 5%" "The checks=5m 00s · 5%" "The review=4m 00s · 4%") \
    && grep -q 'data-head="You · The interview" data-sub="Lem asks you one question at a time"' "$WORK/task-$S.dom" \
    && grep -q 'data-head="The builders · The scout reads the code"' "$WORK/task-$S.dom" \
    && grep -q 'data-head="The personas · The personas’ read of the stories" data-sub="3 of 3 answered, two model families · nobody confused"' "$WORK/task-$S.dom" \
    && ! grep -q '<circle[^>]*data-head="The personas' "$WORK/task-$S.dom" \
    && grep -q 'data-head="The builders · Task 1 of 2"' "$WORK/task-$S.dom" && grep -q 'data-head="The agent · It briefs the builder"' "$WORK/task-$S.dom" \
    && grep -q 'data-head="Lem · The rebase onto the base"' "$WORK/task-$S.dom" \
    && grep -q 'data-head="The builders · The polish pass" data-sub="abc1234 → def5678 · 1 commit"' "$WORK/task-$S.dom" \
    && grep -q 'data-head="The checks · The checks: make test"' "$WORK/task-$S.dom" \
    && grep -q 'data-head="The review · Review round 1: one read"' "$WORK/task-$S.dom" \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$S.dom" feed "A builder started · task 1 of 2" "The checks started|2 commands on def567890" "The review started|attempt 1 · one read" \
      "The interview started" "The scout started" "The personas’ read of the stories started|run by Lem" "The polish pass started|on abc123456"); then
    pass "the interview, the scout, the personas' read, each builder, the polish pass, the checks and the review are drawn from their logged start to the event that ends each, on the row of who held the work, and the activity says each start in words"
  else
    fail "the logged starts on the time card: ${why:-a span of a stage}"
  fi
  # A step that started and has not ended runs to now: the checks with no result yet, an investigation.
  draw task-gate-runs && draw task-cart-total-wrong
  if grep -q 'data-head="The checks · The checks run: 0 of 2 commands done"' "$WORK/task-gate-runs.dom" \
    && grep -q 'data-head="Lem · The rebase onto the base"' "$WORK/task-gate-runs.dom" \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-gate-runs.dom" now "The checks run") \
    && grep -Eq 'class="seg live"[^>]*data-head="The builders · The investigation"' "$WORK/task-cart-total-wrong.dom"; then
    pass "a step whose start is logged and whose end is not runs to now: the checks with no result yet, and an investigation"
  else
    fail "a step that runs: ${why:-a live span}"
  fi
  # The hover, as a reader's mouse makes it: over a band of the plan, and over a span of the owner's row.
  cat > "$STATE/probe.html" <<'PROBE'
<!doctype html><meta charset="utf-8"><iframe id="f" src="task-landed-one.html" style="width:1400px;height:1400px;border:0"></iframe><pre id="out"></pre>
<script>
const wait = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  await wait(1500);
  const w = document.getElementById('f').contentWindow, d = w.document, log = {};
  const hover = node => {
    const box = node.getBoundingClientRect();
    node.dispatchEvent(new w.MouseEvent('mousemove', {bubbles: true, clientX: box.left + Math.min(4, box.width / 2), clientY: box.top + box.height / 2}));
    const tip = d.getElementById('tip');
    return tip.hidden ? 'hidden' : [...tip.children].map(n => n.textContent).join(' | ');
  };
  log.band = hover(d.querySelector('[data-head="Task 1"]'));
  log.span = hover(d.querySelector('[data-head^="You · Choice 1"]'));
  log.mark = hover(d.querySelector('circle[data-head^="The personas"]'));
  d.getElementById('tl-wrap').dispatchEvent(new w.MouseEvent('mouseleave'));
  log.left = d.getElementById('tip').hidden;
  document.getElementById('out').textContent = JSON.stringify(log);
})().catch(e => { document.getElementById('out').textContent = JSON.stringify({error: String(e)}); });
</script>
PROBE
  headless --allow-file-access-from-files --virtual-time-budget=8000 --dump-dom "file://$STATE/probe.html" > "$WORK/probe.dom"
  rm -f "$STATE/probe.html"
  # shellcheck disable=SC1112  # the apostrophe in the expected hover is the page's own
  hovered=$("$PY" -I -c 'import html, json, re, sys
found = re.search(r"<pre id=\"out\">(.*?)</pre>", open(sys.argv[1], encoding="utf-8").read(), re.S)
d = json.loads(html.unescape(found.group(1))) if found and found.group(1) else {"error": "the probe printed nothing"}
wrong = [name for name, ok in {
    "an error": "error" not in d,
    "a band: its stage, its length and its two clock times": d.get("band") == "Task 1 | of 2 | 18m · Nov 10 09:40:00 → 09:58:00",
    "a span: who, what, its length and its clock times": d.get("span", "").startswith("You · Choice 1: The symbol or the code of the currency | you answered: the code | 7m 00s · Nov 10 10:05:00 → 10:12:00"),
    "a mark: what ended, and when": d.get("mark", "").startswith("The personas · The personas’ read of the stories ended | 2 of 2 answered") and d.get("mark", "").endswith("at Nov 10 09:10:00"),
    "the hover goes when the mouse leaves": d.get("left") is True,
}.items() if not ok]
print("; ".join(wrong) or "ok", "" if not wrong else json.dumps(d))' "$WORK/probe.dom" 2>&1 || true)
  if [ ! -s "$WORK/probe.dom" ]; then
    printf 'SKIP the hover of the time card: %s printed no page\n' "$chrome"
  elif [ "$hovered" = "ok " ]; then
    pass "a hover on a band, a span or a mark of the time card says what it is, how long it took and its two clock times, as in \"Task 1 · 18m · 09:40:00 → 09:58:00\""
  else
    fail "the hover of the time card: $hovered"
  fi

  # A choice whose wait ended at 09:20 and whose timeout was written at 10:05 held the owner 15 minutes, not an hour.
  draw "task-$T"
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$T.dom" "You 25m · 28%") \
    && grep -q 'data-head="You · Choice 1: Round up or to the nearest cent" data-sub="its wait ended at 09:20; the timeout took “to the nearest cent” at 10:05"' "$WORK/task-$T.dom"; then
    pass "a choice holds the owner's row from its question to the end of its wait, and not until a timeout written later"
  else
    fail "a choice after its wait: ${why:-the hover of the choice}"
  fi
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$T.dom" "The review 4m 00s · 4%" "Lem 2m 00s · 2%" "The checks 4m 00s · 4%"); then
    pass "a review logged in the same second as the next state block is still the review's time: the order of the log, not the second, says which block an event belongs to"
  else
    fail "an event in the second of the next block: $why"
  fi
  draw task-red-gate
  # The task is open, so its card runs to NOW, where the page's clock stands: Lem holds 30m, the checks 10m.
  if why=$("$PY" -I -B -c "$TIMECARD" "$WORK/task-red-gate.dom" "You|Lem|The checks" "The checks=10m · 25%" "Lem=30m · 75%") \
    && grep -q 'data-head="Lem · After a failed check: a repair or a stop, and no event says which yet"' "$WORK/task-red-gate.dom" \
    && ! grep -q 'data-head="The checks · The checks run' "$WORK/task-red-gate.dom"; then
    pass "a gate run whose first command failed is checks until its last command, with no repair between its commands, and after the whole run failed the time is not drawn as checks that go on"
  else
    fail "after a failed check: ${why:-the span after the red gate}"
  fi
  draw task-read-first
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-read-first.dom" "No state was written yet for the task \"read-first\": its 1 event is in the activity below" \
    "The personas read the stories" "nobody confused · 2 of 2 answered"); then
    pass "the board of a task whose stories were read before its first state block draws its events and says that its state comes later"
  else
    fail "a task with events and no state: $why"
  fi
  draw task-approved-again
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-approved-again.dom" "1. A slip for Berlin or Vienna is in German." \
    "approved after the plan’s stories were recorded: the agent records them again, with their tests" "approval 2; it replaces approval 1" \
    "!held by its tests" "!A slip for Berlin is in German." "feature, because the slip gets a language."); then
    pass "after a new approval the Stories card shows the approved stories, not the plan's older ones and their tests' result"
  else
    fail "stories approved after the plan's: $why"
  fi
  draw task-restored-read && draw task-unread-change
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-restored-read.dom" "Story 1 changed during the build" "!the change was not read") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-unread-change.dom" "The stories changed after this read by a change of the build, and the change was not read."); then
    pass "the Stories card says that a change was not read only while the stories as they stand are not the ones read: his approval of the read stories again clears it"
  else
    fail "the unread change: $why"
  fi
  draw task-clear-read-held
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-clear-read-held.dom" "Nobody confused" "The stories wait for your yes" "!The build started with no wait for you"); then
    pass "a read that found nobody confused does not say that the build started, while the stories wait for the owner's yes"
  else
    fail "a clear read that waits for him: $why"
  fi
  draw "task-$C"
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$C.dom" "approval 2; it replaces approval 1" \
    "Story 1 changed during the build" "Approved by you afterwards (approval 2): it is yours, and no cause of not green" \
    "Story 2 changed during the build" "the counter goes on · by the agent · the pull request is not green for it" \
    "!a year keeps the names apart · by the agent · the pull request is not green for it"); then
    pass "a story change that the owner's later approval took over is his and no cause of not green, and a change after that approval still is one"
  else
    fail "story changes and approvals: $why"
  fi
  draw task-rare-path
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-rare-path.dom" "Frozen by the personas’ read, with no wait for you" "!Taken as a correction" "!Approved by you"); then
    pass "stories the personas' read froze on the rare path are shown as such, never as a correction or as the owner's yes"
  else
    fail "the read's approval: $why"
  fi

  # The experts' advice. Each check reads one row of one card, or one banner, so that a text of
  # another choice or of the activity cannot stand in for it.
  draw "task-$X"
  # shellcheck disable=SC1111,SC1112  # the curly quotes around a pick are the page's
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" decisions \
      "Choice 4 waits for you: The font of the invoice|Fable picks “serif”, because a printed invoice reads better in serif|Astra picks “serif”, because the letters of the shop are in serif|~Its wait ends at [0-9]{2}:[0-9]{2}; then the build goes on with “serif”, the experts’ shared pick\.|Where you answer: Lem puts choice 4 to you as a page in its session. Answer it there before its wait ends; then the build goes on with the experts’ shared pick.|!the recommended option" \
      "Choice 5 waits for you: The size of the total|Fable finds that none of the options fits, because the total should be bold, not bigger|Astra picks “12 pt”, because the other lines are 12 pt|then the build goes on with “14 pt”, the recommended option, as the experts have no shared pick.|then the build goes on with the recommended action.|!the experts’ shared pick" \
      "1. The paper size|!Fable picks|!waits for you") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" now \
      "2 choices wait for you|The font of the invoice|the experts: Fable “serif” · Astra “serif”|~until [0-9]{2}:[0-9]{2}; then the build goes on with the experts’ shared pick") \
    && why=$("$PY" -I -B -c "$BANNERS" "$WORK/board.dom" \
      "^Choice 4 waits for you: Expert advice · The font of the invoice · .* then the build goes on with the experts’ shared pick\.$" \
      "^Choice 5 waits for you: Expert advice · The size of the total · .* then the build goes on with the recommended action\.$"); then
    pass "a choice that waits shows each expert's advice in its own row of the Decisions card, a pick or none fits with its reasons, and its row, its banner and the head of its board say that the end of the wait takes the experts' shared pick when both agree, else the recommended option"
  else
    fail "the experts' advice on a choice that waits: $why"
  fi
  # shellcheck disable=SC1111,SC1112  # the curly quotes around a pick are the page's
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" decisions \
      "1. The paper size → A4|@a-bad|~taken by the experts at [0-9]{2}:[0-9]{2}, while you were away, before its wait ended: both picked it\. The pull request is not green for it\.|Fable picked “A4”, because every customer of the shop is in Europe, where the post reads A4|Astra picked “A4”, because the envelopes of the shop are cut for A4|~Your answer came at [0-9]{2}:[0-9]{2}, after the experts took it: “Letter” \(Letter, it is in the tray\)\. It differs from what was taken|!taken by the timeout") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" feed \
      "Choice 1 taken by the experts while you were away|A4|Fable: every customer of the shop is in Europe, where the post reads A4 · Astra: the envelopes of the shop are cut for A4" \
      "Your answer to choice 1 came after it was taken|Letter") \
    && grep -Eq 'data-head="You · Choice 1: The paper size" data-sub="the experts took “A4” at [0-9]{2}:[0-9]{2}, while you were away"' "$WORK/task-$X.dom"; then
    pass "a choice the experts settled while the owner was away is in the Decisions card as taken by the experts, marked like a timeout, with their pick and both reasons, and his answer after it as after the experts took it; the activity and the time card say so"
  else
    fail "a choice the experts settled: ${why:-the hover of the settled choice}"
  fi
  # shellcheck disable=SC1111,SC1112  # the curly quotes around a pick are the page's
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" decisions \
      "2. The color of the logo → the green of the shop|@a-bad|~taken by the experts at the end of the wait, at [0-9]{2}:[0-9]{2}: no answer came in 15 minutes, and both picked it\. The pull request is not green for it\.|Fable picked “the green of the shop”, because the invoice is a page of the shop|Astra picked “the green of the shop”, because the printer prints in color|!taken by the timeout" \
      "3. The order number on the page → at the top|@a-bad|~taken by the timeout at [0-9]{2}:[0-9]{2}: no answer came in 15 minutes\. The recommended action stands, and the pull request is not green for it\.|the experts split: Fable picked “at the top”, because a reader looks for it first · Astra picked “at the foot”, because the top holds the address window|!taken by the experts") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" feed \
      "Choice 2 taken by the experts at the end of its wait|the green of the shop|Fable: the invoice is a page of the shop · Astra: the printer prints in color" \
      "Choice 3 taken by the timeout|at the top|!experts" \
      "Astra advised on choice 3|picks “at the foot”|the top holds the address window" \
      "Fable advised on choice 5|none of the options fits|the total should be bold, not bigger") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$X.dom" progress "Decisions|3 taken, 1 by the timeout, 2 by the experts") \
    && grep -Eq 'data-head="You · Choice 2: The color of the logo" data-sub="its wait ended at [0-9]{2}:[0-9]{2}; the experts’ shared pick “the green of the shop” was taken at [0-9]{2}:[0-9]{2}"' "$WORK/task-$X.dom"; then
    pass "a timeout that took the experts' shared pick names them with both reasons, and one whose experts split is the timeout's with the recommended option and each expert's advice, in the Decisions card, the activity, the count of decisions and the time card"
  else
    fail "a timeout with the experts' advice: ${why:-the hover of the timeout the experts took}"
  fi
  draw "task-$P" && draw task-landing-starts
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$P.dom" feed "The polish pass|2 commits, 1 item filed in the backlog|abc1234 → def5678|docs/backlog/invoice-footer-typo.md") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$P.dom" feed "Careful by the review, not by the plan|round 1: the file name holds the order's total, which a customer pays") \
    && why=$("$PY" -I -B -c "$TIMECARD" "$WORK/task-$P.dom" "You|Lem|The builders|The checks" "Lem=10m · 25%" "The builders=18m · 45%" "The checks=12m · 30%") \
    && grep -q 'data-head="The builders · The polish pass" data-sub="from the event before it: its start is not logged, so the rebase onto the base is in it"' "$WORK/task-$P.dom" \
    && grep -q 'data-head="The checks · The checks run"' "$WORK/task-$P.dom" \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$P.dom" now "The checks and the review run on it") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-landing-starts.dom" now "It starts its landing: the rebase onto the base, then the polish pass|!The checks and the review run on it") \
    && grep -q 'data-head="Lem · The landing starts: the rebase onto the base, then the polish pass, and no event says which runs yet"' "$WORK/task-landing-starts.dom" \
    && ! grep -q 'data-head="The checks · The checks run"' "$WORK/task-landing-starts.dom"; then
    pass "the polish pass is in the activity with its commits and the items it filed, and on the time card as the builders' span from the event before it; a landing with no polish and no check yet says that it starts, not that its checks run; a careful call the review made and the plan missed is in the activity with the review's reason"
  else
    fail "the polish pass: ${why:-a span of the time card}"
  fi
  # The plan talk from its start to its record is a span of the review's row, with its counts; with
  # no start in the log it is a dot where it ended, and with a start and no record yet it runs.
  draw "task-$K" && draw task-talk-runs && draw "task-$L"
  if grep -q 'data-head="The review · The plan talk" data-sub="with codex: 3 questions in 7 turns · 2 settled, 1 open, 1 of them a design choice · 2 repaired: 1 at the cause, 1 a layer over a cited decision · 1 decision two questions named · 2 raised, not argued"' "$WORK/task-$K.dom" \
    && why=$("$PY" -I -B -c "$TIMECARD" "$WORK/task-$K.dom" "You|The agent|The review" "The agent=25m · 100%" "The review=18m · 72%") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$K.dom" feed "The plan talk started|with codex" "The plan talk ended|with codex: 3 questions in 7 turns|1 of them a design choice|2 raised, not argued") \
    && ! grep -q 'data-sub="[^"]*its start is not logged' "$WORK/task-$K.dom" \
    && grep -q 'data-head="The review · The plan talk ended" data-sub="with codex: 4 questions in 19 turns, over the bound of 18 for its 4 questions · 3 settled, 1 open, 1 of them a design choice · 2 repaired: 2 at the cause · 1 raised, not argued · its start is not logged"' "$WORK/task-$L.dom" \
    && grep -q 'data-head="The review · The plan talk runs" data-sub="with claude; its record comes when the talk ends"' "$WORK/task-talk-runs.dom"; then
    pass "the plan talk is the review's span from its start to its record, with its questions, turns, settled, open, design choices, repairs at the cause and layers over a cited decision, decisions two questions named and questions raised and not argued; one with no start logged is a dot where it ended, and one with no record yet runs"
  else
    fail "the plan talk on the time card: ${why:-a span or a dot of the talk}"
  fi
  # The talk's companion is shown as a companion of the talk, and the builder lead after it.
  draw "task-$M"
  if grep -q 'title="A companion session talks the plan through, with the reviewer in its other pane; an agent builds it after the talk"' "$WORK/task-talk-runs.dom" \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-talk-runs.dom" "Its companion talks the plan through" "plan talk" "a companion talks the plan through, with the reviewer in its other pane" "!Its session builds it" "!defend") \
    && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$M.dom" "one agent builds the plan its companion talked through" "An agent builds it" "!builder lead") \
    && grep -q 'data-head="Lem · The plan talk is done: the plan waits for the agent that builds it"' "$WORK/task-$M.dom" \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$M.dom" feed "The plan talk ended|with codex: 2 questions in 5 turns|2 repaired: 1 a layer over a cited decision|!at the cause") \
    && grep -q 'title="A companion session talks the plan through' "$WORK/board.dom" && why=$("$PY" -I -B -c "$SHOWN" "$WORK/board.dom" "!one agent"); then
    pass "a task whose plan talk runs in its companion shows the companion as the talk's, and after the talk the builder lead that builds it, with the wait between the two as Lem's and the layer the talk accepted"
  else
    fail "the talk's companion and the builder after it: ${why:-a tag, a head or a span}"
  fi
  # An answered task is in the lane of what ended, with its investigation's answer, on the board and on its own.
  draw "task-$A"
  if why=$("$PY" -I -B -c "$LANES" "$WORK/board.dom" "Done=Refund shows zero|") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/board.dom" lanes \
      "Refund shows zero|No bug: a refund is a credit note, and the invoice shows what is left to pay|a bug|!Waits for you|!Answered: not a bug") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$A.dom" now \
      "Answered: it ended with a report and nothing to merge|Closed|No bug: the code does what it should:|a refund is a credit note, and the invoice shows what is left to pay|billing/invoice.py:total|reproduced|investigation.md in the task directory") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$A.dom" feed \
      "The investigation found no bug|a refund is a credit note, and the invoice shows what is left to pay|billing/invoice.py:total · reproduced" "Answered|not a bug: the invoice shows what is left to pay") \
    && ! grep -q 'class="phase cur"' "$WORK/task-$A.dom" \
    && grep -q 'data-head="The builders · The investigation" data-sub="a builder reproduces the bug and finds its cause · a bug, because the ask says the total is wrong today"' "$WORK/task-$A.dom" \
    && grep -q 'data-head="Investigation"' "$WORK/task-$A.dom" && why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$A.dom" "Inv." "!Waits for you"); then
    pass "an answered task is in the lane of what ended with its kind and its investigation's answer; its own board says it ended with a report, names the call, the cause's place and the report, and draws the investigation as the builders' span"
  else
    fail "an answered task: ${why:-the span of the investigation, or a phase marked as current}"
  fi
  draw task-cart-total-wrong
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/board.dom" lanes "Cart total wrong|Investigating: a builder reproduces the bug and finds its cause|a bug") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-cart-total-wrong.dom" now "The investigator acts|Its investigator examines it, before any story|a bug, because the ask says the total is wrong since yesterday|!lead"); then
    pass "a task whose investigation runs says so on its card and on its own board, and names the investigator, not a lead"
  else
    fail "a task whose investigation runs: $why"
  fi
  # The investigation is the first step of the task's phases while it runs, and the time card of a
  # span under six minutes reads its axis to the second, so no two ticks say the same minute.
  if grep -Eq 'class="phase cur"><i[^>]*></i>Investigation<' "$WORK/task-cart-total-wrong.dom" \
    && ! grep -q 'class="phase past"' "$WORK/task-cart-total-wrong.dom" \
    && grep -Eq 'class="phase past"><i[^>]*></i>Investigation<' "$WORK/task-$A.dom" \
    && why=$("$PY" -I -c 'import re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
area = dom[dom.index("id=\"timeline\""):]
ticks = re.findall(r"<text class=\"axis\"[^>]*>([^<]*)</text>", area)
ok = len(ticks) == 7 and len(set(ticks)) == 7 and all(re.fullmatch(r"\d\d:\d\d:\d\d", x) for x in ticks)
print("" if ok else f"the ticks are {ticks}")
sys.exit(not ok)' "$WORK/task-cart-total-wrong.dom"); then
    pass "a task whose bug is investigated has the investigation as its first phase, current while it runs and done after it, and a short time card reads its axis to the second"
  else
    fail "the investigation's phase or a short axis: ${why:-a phase}"
  fi
  # An answered task lands nowhere and has no stories, decisions, checks or review: none is drawn empty.
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$A.dom" "!lands on" "!The agent writes the stories") \
    && grep -Eq 'id="stories-card"[^>]* hidden' "$WORK/task-$A.dom" && grep -Eq 'id="decisions-card"[^>]* hidden' "$WORK/task-$A.dom" \
    && grep -Eq 'id="gate-card"[^>]* hidden' "$WORK/task-$A.dom" && grep -Eq 'id="review-card"[^>]* hidden' "$WORK/task-$A.dom" \
    && ! grep -Eq 'id="decisions-card"[^>]* hidden' "$WORK/task-$G.dom"; then
    pass "an answered task names no branch it lands on, and draws no empty card of stories, decisions, checks or review"
  else
    fail "the empty cards of an answered task: ${why:-a card is drawn}"
  fi
  # The rest of an answered task's card: its phases end with the answer, and its checks and review say why there are none.
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$A.dom" progress "Investigation|Answered|!Stories|!Landed|none: it ended with a report") \
    && [ "$(grep -o 'class="phase past"' "$WORK/task-$A.dom" | wc -l | tr -d ' ')" = 2 ]; then
    pass "an answered task's phases are its investigation and its answer, and its checks and review say that it ended with a report"
  else
    fail "the phases of an answered task: ${why:-a phase is not done}"
  fi
  # The time card gives the task's whole time beside the rows' totals, which are shares of it; a
  # choice that no expert advised on yet says so in one line.
  # shellcheck disable=SC1111,SC1112  # the curly quotes are the page's
  if grep -Eq '<span class="whole"[^>]*>2h 20m in all</span>' "$WORK/task-$L.dom" \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-$G.dom" decisions "Choice 7 waits for you: The note of a cancelled order|No expert advised on it yet.|!Fable: no advice yet|!Astra: no advice yet"); then
    pass "the time card says the task's whole time beside the rows' shares of it, and a choice with no advice yet says so in one line"
  else
    fail "the whole time, or the experts' empty advice: ${why:-no whole time on the card}"
  fi
  # A read in which nobody answered says so, in the bad color, with each persona that was silent.
  draw task-silent-read && draw task-queued-after
  # shellcheck disable=SC1111,SC1112  # the curly quotes are the page's
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/task-silent-read.dom" stories "Nobody answered the personas’ read|(0 of 2)|@a-bad|no answer from Merchant, opus (the model timed out)|no answer from Accountant, sol|!Nobody confused|!read by 0") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-queued-after.dom" now "Waits for a free place|it starts after “Building one” ends"); then
    pass "a read of the stories that no persona answered is shown as no read, with who was silent and why, and a task queued behind another names it"
  else
    fail "a read nobody answered, or a task queued after another: $why"
  fi
  # The board of all tasks: its activity takes the whole width, and its legend has one entry for each
  # look of a bar, so three statuses drawn in one color are one entry.
  if grep -q 'id="cols" class="cols one"' "$WORK/board.dom" && grep -Eq 'id="stack" class="stack" hidden' "$WORK/board.dom" \
    && ! grep -q 'id="cols" class="cols one"' "$WORK/task-$G.dom" \
    && why=$("$PY" -I -c 'import html, re, sys
dom = open(sys.argv[1], encoding="utf-8").read()
area = dom[dom.index("id=\"legend\""):]
area = area[:area.index("</div>")]
items = [(cls, i or "", html.unescape(label)) for cls, i, label in re.findall(r"<span class=\"([^\"]*)\"[^>]*><i(?: class=\"([^\"]*)\")?></i>([^<]*)</span>", area)]
looks = [(cls, i) for cls, i, _ in items]
labels = [label for *_, label in items]
ok = len(set(looks)) == len(looks) and "Waits for you · Waits for the merge · Drafted at night" in labels and "Waits for the merge" not in labels
print("" if ok else f"the legend is {items}")
sys.exit(not ok)' "$WORK/board.dom"); then
    pass "on the board of all tasks the activity takes the whole width, and the legend has one entry for each look of a bar: the statuses that wait for the owner share one"
  else
    fail "the activity's width or the legend: ${why:-the activity is in a column}"
  fi
  # The backlog tab counts the items whose place is gone or cannot be read, in a sentence.
  draw board backlog
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/board-backlog.dom" "4 items in docs/backlog · 2 items name a place that is gone or cannot be read" \
    "billing/gone.py:total · the file is not there" "locked.txt:secret · the file cannot be read" "Decided against" "!points at" "!2 point "); then
    pass "the backlog tab says how many items name a place that is gone or cannot be read, and marks each one"
  else
    fail "the backlog tab: $why"
  fi
  # A fixed line of a state block is said in words on every page, or left out; never shown as it is written.
  raw=()
  for dom in "$WORK/board.dom" "$WORK"/task-*.dom; do
    [ -e "$dom" ] || continue
    why=$("$PY" -I -B -c "$SHOWN" "$dom" "!lead: builder" "!lead: session" "!session: C0FFEE" "!plan committed" "!investigation: bug" "!kind: bug" "!after: building-one" "!report: investigation.md" \
      "!small change: one builder" "!the owner" "!careful path" "!interview.start" "!scout.start" "!stories.read.start" "!investigation.start" "!builder.start" "!polish.start" "!gate.start" "!review.start") \
      || raw+=("$(basename "$dom"): $why")
  done
  if [ "${#raw[@]}" -eq 0 ] \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/board.dom" lanes "Correction one|One builder makes the change|small change" "Talk runs|Its companion talks the plan through|plan talk"); then
    pass "no page shows a fixed line of a state block or a stage's start as it is written, says the owner in the third person, or names a careful path: who works on a task, its plan, its kind, its investigation and what it waits for are said in words to you"
  else
    fail "a fixed line of a state block: ${raw[*]:-} ${why:-}"
  fi
  # The project's own asker: the page says where the owner answers, by the settings' tools.ask: on the
  # large card of the board, and on the task's own board.
  printf '%s\n' '[tools]' 'ask = "terminal"' > "$R/.lem/project.local.toml"
  board --no-open >/dev/null && draw board && draw task-stories-wait
  cp "$WORK/board.dom" "$WORK/board-terminal.dom" && cp "$WORK/task-stories-wait.dom" "$WORK/stories-terminal.dom"
  printf '%s\n' '[tools]' 'ask = "my-asker"' > "$R/.lem/project.local.toml"
  board --no-open >/dev/null && draw task-held-choice && draw task-stories-wait
  rm "$R/.lem/project.local.toml"
  board --no-open >/dev/null && draw board
  # shellcheck disable=SC1112  # the curly quote is the page's
  if why=$("$PY" -I -B -c "$ROWS" "$WORK/board-terminal.dom" now \
      "Gift note export|Where you answer: Lem asks you choice 7 in its session, as text in the conversation. Answer it there before its wait ends; then the build goes on with the recommended action.") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/stories-terminal.dom" now \
      "Where you answer: Lem shows you the stories, with the personas’ read on top, in its session, as text in the conversation. Approve or change them there.") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-held-choice.dom" now \
      "Where you answer: Lem asks you choice 1 with my-asker, the asker this project names. Answer it there: it waits for your word, with no end.") \
    && why=$("$PY" -I -B -c "$ROWS" "$WORK/task-stories-wait.dom" now \
      "Where you answer: Lem shows you the stories, with the personas’ read on top, with my-asker, the asker this project names. Approve or change them there."); then
    pass "where the owner answers follows the project's tools.ask: Lem's page, the conversation, or the developer's own asker by its name"
  else
    fail "the project's asker: $why"
  fi

  # A board of example tasks says so on every page, and a picture of it is taken over that mark.
  board --no-open --demo >/dev/null
  board --no-open --task "$L" >/dev/null
  board --no-open --task "$G" >/dev/null
  draw "task-$L"
  if why=$("$PY" -I -B -c "$SHOWN" "$WORK/task-$L.dom" "Demo data. These tasks are examples and not real work. Nothing on this page waits for you." "Demo data · Lem · shop · one task"); then
    pass "board --demo marks the board of one task as example data, banner and eyebrow"
  else
    fail "the demo banner: $why"
  fi
  # The pictures of this stress case, to look at: three widths, a light and a dark theme. The README's
  # pictures come from tests/board-showcase.py, a normal afternoon.
  if [ -n "${LEM_BOARD_SHOTS:-}" ]; then
    mkdir -p "$LEM_BOARD_SHOTS"
    for page in board "task-$G" "task-$L"; do
      draw "$page"
      cp "$STATE/$page.html" "$WORK/light.html"
      for theme in light dark; do
        if [ "$theme" = dark ]; then
          "$PY" -I -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("<head>", "<head><style>:root { --agterm-background: #15181c; --agterm-foreground: #dde1e6; }</style>", 1))' "$STATE/$page.html"
        fi
        for width in 900 1400 1800; do
          headless --hide-scrollbars --window-size="$width,2400" --virtual-time-budget=5000 --screenshot="$LEM_BOARD_SHOTS/$page-$width-$theme.png" "file://$STATE/$page.html"
          printf 'shot %s\n' "$LEM_BOARD_SHOTS/$page-$width-$theme.png"
        done
      done
      cp "$WORK/light.html" "$STATE/$page.html"
    done
    # where the lanes start on a 1400 x 900 window, and the tallest card of each lane over its shortest
    cp "$STATE/board.html" "$WORK/board-page.html"
    "$PY" -I -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("</body>", """<script>setTimeout(() => { const pre = document.createElement("pre"); pre.id = "measured";
  const ratio = [...document.querySelectorAll("#lanes .lane")].map(l => [...l.querySelectorAll(".tcard")].map(c => c.offsetHeight)).filter(h => h.length).map(h => Math.round(100 * Math.max(...h) / Math.min(...h)) / 100);
  pre.textContent = JSON.stringify({lanes: Math.round(document.getElementById("lanes-section").getBoundingClientRect().top), card_height_ratio: ratio}); document.body.append(pre); }, 2500);</script></body>""", 1))' "$STATE/board.html"
    headless --window-size=1400,900 --virtual-time-budget=6000 --dump-dom "file://$STATE/board.html" \
      | "$PY" -I -c 'import html, re, sys; found = re.search(r"<pre id=\"measured\">([^<]*)", sys.stdin.read()); print("measured at 1400 x 900:", html.unescape(found.group(1)) if found else "nothing")'
    cp "$WORK/board-page.html" "$STATE/board.html"
  fi
fi

if [ "$fails" -gt 0 ]; then
  printf '%d failed\n' "$fails"
  exit 1
fi
printf 'all passed\n'
