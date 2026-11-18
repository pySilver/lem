#!/usr/bin/env bash
# A small change: one criterion in the task directory, no plan on the branch, one builder, the checks
# with the check of the criteria once, one read, and a short pull request. And what keeps the short path
# safe: a full change with no plan is refused, a careful small change is not green and no agent merges
# it, and a small change does not lower the bar.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

SMALL=$WORK/small
git init -q -b main "$SMALL" && ident "$SMALL"
project --repo "$SMALL" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[checks]' 'commands = ["true"]' '[flow]' 'topics = ["a customer is charged the wrong price"]' > "$SMALL/.lem/project.toml"
git -C "$SMALL" add -A && git -C "$SMALL" commit -q -m "chore: start"
s() { land --repo "$SMALL" "$@"; }
criteria() { "$PY" -B "$CRITERIA" --repo "$SMALL" "$@"; }
dir_of() { echo "$SMALL/.lem/state/tasks/$1"; }
# small_in SLUG SIZE: a task whose one criterion is in its task directory, approved as Lem does it for SIZE
# (`small` in his name, with no --file, `full` by him), with a worktree on its branch and no plan on it
small_in() {
  local tree
  project --repo "$SMALL" task-dir "$1" --ask "The date column of the report must never wrap." >/dev/null
  printf '%s\n' '## Acceptance criteria' '' "Size: $2, because the ask is one sentence." '' '1. The date column of the report never wraps: 2026-11-17 stays on one line.' > "$(dir_of "$1")/criteria.md"
  if [ "$2" = small ]; then criteria approve "$1" --small >/dev/null; else criteria approve "$1" --file "$(dir_of "$1")/criteria.md" >/dev/null; fi
  tree=$(project --repo "$SMALL" worktree-dir "$1")
  git -C "$SMALL" worktree add -q "$tree" -b "fix/$1" main
  echo "$tree"
}
# built SLUG TREE: the builder's change, its test, the test line under the criterion, and the state `ready`
built() {
  mkdir -p "$2/tests" && printf '%s\n' 'td { white-space: nowrap; }' > "$2/$1.css" && echo "grep -q nowrap $1.css" > "$2/tests/$1.sh"
  git -C "$2" add -A && git -C "$2" commit -q -m "fix(report): the date column never wraps"
  printf '%s\n' "   - test: \`sh tests/$1.sh\` in \`tests/$1.sh\`" >> "$(dir_of "$1")/criteria.md"
  project --repo "$2" state "$1" ready "the small change is built" >/dev/null
}
reds() { grep -c "\"event\": \"task.red\", \"task\": \"$1\"" "$SMALL/.lem/state/events.jsonl"; }
SHORT=$WORK/short-notes.md
printf '%s\n' 'none' > "$SHORT"

# Lem's approval in the owner's name takes no --file: its file is the task directory's criteria.md.
small_in by-name small >/dev/null
by_name=$(criteria approved by-name | field '(d["approved"]["by"], d["approved"]["size"], d["approved"]["criteria"][0]["n"])' 2>&1 || true)
no_file=$(criteria approve by-name 2>&1 || true)
if [ "$by_name" = "('lem', 'small', 1)" ] && grep -qF "approve needs --file" <<<"$no_file"; then
  pass "Lem approves a small change's criterion in the owner's name with --small and no --file, from the task directory's criteria.md; the owner's approval still needs its --file"
else
  fail "the approval in the owner's name: $by_name / $no_file"
fi
project --repo "$SMALL" state by-name dropped "the test is over" >/dev/null

# A small change goes from Lem's approval in his name to the merge with no plan file on the branch.
tree=$(small_in date-nowrap small)
built date-nowrap "$tree"
shown=$(criteria show date-nowrap 2>&1 | field '(d["small"], d["size"], d["plan"].endswith("tasks/date-nowrap/criteria.md"))' 2>&1 || true)
s start date-nowrap >/dev/null && s base date-nowrap >/dev/null
gated=$(s checks date-nowrap 2>&1 | field '(d["green"], d["polish"], d["criteria"]["ok"])' 2>&1 || true)
due=$(s read date-nowrap 2>&1 | field '(d["due"], d["floor"], d["small"], d["tasks"])' 2>&1 || true)
s read date-nowrap >/dev/null 2>&1 || true
s read date-nowrap --record "$(clean 1)" >/dev/null 2>&1 || true
proposed=$(s propose date-nowrap --title "fix(report): the date column never wraps" --notes "$SHORT" 2>&1 | field 'd["green"]' 2>&1 || true)
merged=$(s land date-nowrap --by agent 2>&1 | field 'd["pushed"]' 2>&1 || true)
text=$(dir_of date-nowrap)/pr.md
if [ "$shown" = "(True, 'small', True)" ] && [ "$gated" = "(True, None, True)" ] && [ "$due" = "('review', 'read', True, 1)" ] \
  && [ "$proposed" = True ] && [ "$merged" = False ] && [ "$(status_in "$SMALL" date-nowrap)" = landed ] && [ "$(reds date-nowrap)" = 1 ] \
  && [ -z "$(git -C "$SMALL" ls-tree -r --name-only main -- docs/plans)" ] \
  && [ "$(sed -n 1p "$text")" = '**Green.** The checks passed with the bar where it was, the review left no must-fix, no criterion changed, and no decision was taken by timeout or by the experts.' ] \
  && ! grep -qi 'correction\|machine checks' "$text" \
  && grep -qxF -- '1. The date column of the report never wraps: 2026-11-17 stays on one line.' "$text" \
  && grep -qxF -- "   - \`sh tests/date-nowrap.sh\`: passes on the branch, fails on the base commit" "$text" \
  && grep -qxF -- '- the review, round 1 (one read; answered: codex): clean, 0 must-fix, 0 should, 0 nit' "$text" \
  && ! grep -q 'polish pass\|## Decisions of the build\|personas asked\|size:' "$text" && [ "$(grep -c '' "$text")" -le 20 ] \
  && ! grep -qiwE 'you|your' "$text" && [ ! -e "$(dir_of date-nowrap)/built.md" ] && [ ! -e "$(dir_of date-nowrap)/decisions.md" ]; then
  pass "a small change with its criterion in the task directory goes from Lem's approval through the gate, one read and a short pull request to an agent's merge, with no plan file on the branch, the check of the criteria run once, and neither of a full change's two files for the owner"
else
  fail "a small change: $shown / $gated / $due / $proposed / $merged / reds $(reds date-nowrap) / $(cat "$text" 2>/dev/null)"
fi

# The landing logs the start of the checks and of the review itself, so that each has a span: the review's once for its attempt, however often read is asked.
events_of() { "$PY" -c 'import json, sys; print([(e["event"], {k: v for k, v in e.items() if k in ("tip", "commands", "attempt", "floor")}) for e in map(json.loads, open(sys.argv[1])) if e["task"] == sys.argv[2] and e["event"] in ("gate.start", "gate", "review.start", "review")])' "$SMALL/.lem/state/events.jsonl" "$1"; }
tip=$(git -C "$SMALL" rev-parse --short=9 main)
if [ "$(events_of date-nowrap)" = "[('gate.start', {'tip': '$tip', 'commands': 1}), ('gate', {'tip': '$tip'}), ('review.start', {'attempt': 1, 'floor': 'read'}), ('review', {'attempt': 1, 'tip': '$tip'})]" ]; then
  pass "gate logs gate.start with the tip and the count of its commands before the first runs, and read logs review.start once for the attempt that is due, before the review's record"
else
  fail "the starts of the landing: $(events_of date-nowrap)"
fi

# A small change's builder files what it saw outside the change, in a commit of its own after the change's:
# no polish pass runs or starts, the gate, the check of the criteria and the bar take the item as a document of
# the change, the read covers it, and the pull request lists it.
tree=$(small_in date-outside small)
built date-outside "$tree"
item=docs/backlog/a-range-over-two-months-repeats-the-year.md
mkdir -p "$tree/docs/backlog" && printf '%s\n' '---' 'worth: later' 'where: report.css' 'added: 2026-11-17' '---' \
  '# a range over two months repeats the year' '' 'The range 28 Feb to 3 Mar 2026 reads "28 Feb 2026 - 3 Mar 2026"; a noqa in a note is no mark.' '' \
  'Seen outside the change by the builder of task date-outside (2026-11-17); the base commit has it.' > "$tree/$item"
git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): what the builder of date-outside saw outside it"
s start date-outside >/dev/null && s base date-outside >/dev/null
no_polish=$(s polish date-outside 2>&1 || true)
outside_gate=$(s checks date-outside 2>&1 | field '(d["green"], d["criteria"]["ok"], d["bar"]["lowered"], d["criteria"]["run_without"])' 2>&1 || true)
s read date-outside >/dev/null 2>&1 || true
s read date-outside --record "$(clean 1)" >/dev/null 2>&1 || true
outside_due=$(s read date-outside 2>&1 | field '(d["due"], d["to_file"])' 2>&1 || true)
outside_green=$(s propose date-outside --title "fix(report): the date column never wraps" --notes "$SHORT" 2>&1 | field 'd["green"]' 2>&1 || true)
text=$(dir_of date-outside)/pr.md
if grep -qF "a small change has no polish pass" <<<"$no_polish" && grep -qF "\`lem land checks date-outside\`" <<<"$no_polish" \
  && [ "$outside_gate" = "(True, True, [], ['date-outside.css', '$item'])" ] && [ "$outside_due" = "('none', [])" ] && [ "$outside_green" = True ] \
  && grep -qxF -- "- filed in the backlog by the builder: \`$item\`" "$text" && ! grep -q 'polish' "$text" \
  && ! grep -q "\"event\": \"polish.start\", \"task\": \"date-outside\"" "$SMALL/.lem/state/events.jsonl"; then
  pass "a small change whose builder filed a defect outside it in its own commit has no polish pass, which refuses to start: the gate, the check of the criteria and the bar pass with the item, the read covers it, and the pull request lists it"
else
  fail "a small change with an item of its builder: $no_polish / $outside_gate / $outside_due / $outside_green / $(cat "$text" 2>/dev/null)"
fi
project --repo "$SMALL" state date-outside dropped "the test is over" >/dev/null

# A full change keeps its criteria at the top of its plan: with no plan file on the branch it is refused, also with a criterion file in the task directory.
tree=$(small_in date-feature full)
built date-feature "$tree"
feature=$(criteria show date-feature 2>&1 || true)
s start date-feature >/dev/null && s base date-feature >/dev/null
feature_gate=$(s checks date-feature 2>&1 || true)
if grep -qF "criteria.md says \`Size: full\`: only a small change (\`Size: small\`) keeps its criterion in the task directory" <<<"$feature" \
  && grep -qF "A full change's criteria are at the top of its plan" <<<"$feature_gate" && [ "$(kept_in "$SMALL" date-feature gated)" = None ]; then
  pass "a full change with no plan file on the branch is refused by the criteria and by the gate, also with a criterion file in its task directory"
else
  fail "a full change with no plan: $feature / $feature_gate"
fi
project --repo "$SMALL" state date-feature dropped "the test is over" >/dev/null

# A small change whose diff reaches what guards the project is careful: the full set, not green, and a person merges it.
tree=$(small_in gate-edit small)
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[checks]' 'commands = ["true", "true"]' '[flow]' 'topics = ["a customer is charged the wrong price"]' > "$tree/.lem/project.toml"
built gate-edit "$tree"
s start gate-edit >/dev/null && s base gate-edit >/dev/null && { s checks gate-edit > "$WORK/gate-edit.out" 2>&1 || true; }
floor=$(s read gate-edit 2>&1 | field '(d["floor"], len(d["careful"]))' 2>&1 || true)
one_read=$(s read gate-edit --record "$(clean 1)" 2>&1 || true)
s read gate-edit --record "$(record 1 '{"kind": "full", "ran": [{"name": "full", "why": "the change edits the gate"}], "answered": ["codex"]}')" >/dev/null 2>&1 || true
careful_green=$(s propose gate-edit --title "chore: two gate commands" --notes "$MIG" 2>&1 | field 'd["green"]' 2>&1 || true)
by_agent=$(s land gate-edit --by agent 2>&1 || true)
text=$(dir_of gate-edit)/pr.md
if [ "$floor" = "('full', 1)" ] && grep -qF "this change gets the project's full set at the least" <<<"$one_read" && [ "$careful_green" = False ] \
  && grep -qF "a small change that is careful" <<<"$(sed -n 3p "$text")" && grep -qF "a careful request is merged by a person" <<<"$by_agent" \
  && [ "$(status_in "$SMALL" gate-edit)" = open ]; then
  pass "a small change whose diff edits the gate of the settings gets the full set, is not green because a careful change took the short path, and no agent merges it"
else
  fail "a careful small change: $(grep -v "^ \|^[{}]" "$WORK/gate-edit.out") / $floor / $one_read / $careful_green / $by_agent / $(cat "$text" 2>/dev/null)"
fi
project --repo "$SMALL" state gate-edit dropped "the test is over" >/dev/null

# A small change does not lower the bar: there is no plan for the reason, and a lowered bar takes the full change's path.
tree=$(small_in skips-test small)
printf '%s\n' 'import pytest' '' '@pytest.mark.skip' 'def test_old():' '    assert True' > "$tree/tests/test_old.py"
built skips-test "$tree"
s start skips-test >/dev/null && s base skips-test >/dev/null
lowered=$(s checks skips-test 2>&1 || true)
if grep -qF "a small change does not lower the bar: tests/test_old.py" <<<"$lowered" && grep -qF "it is a full change" <<<"$lowered" && [ "$(kept_in "$SMALL" skips-test gated)" = None ]; then
  pass "a small change that lowers the bar is refused at the gate, with the full change's path named, since a small change has no plan to give the reason in"
else
  fail "a small change that lowers the bar: $(grep -v "^ \|^[{}]" <<<"$lowered")"
fi
project --repo "$SMALL" state skips-test dropped "the test is over" >/dev/null

finish
