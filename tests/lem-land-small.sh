#!/usr/bin/env bash
# A small change: one story in the task directory, no plan on the branch, one builder, the checks
# with the stories' check once, one read, and a short pull request. And what keeps the short path
# safe: a feature with no plan is refused, a careful small change is not green and no agent merges
# it, and a small change does not lower the bar.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

SMALL=$WORK/small
git init -q -b main "$SMALL" && ident "$SMALL"
project --repo "$SMALL" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[gate]' 'commands = ["true"]' '[flow]' 'topics = ["a customer is charged the wrong price"]' > "$SMALL/.lem/project.toml"
git -C "$SMALL" add -A && git -C "$SMALL" commit -q -m "chore: start"
s() { land --repo "$SMALL" "$@"; }
stories() { "$PY" -B "$STORIES" --repo "$SMALL" "$@"; }
dir_of() { echo "$SMALL/.git/lem/tasks/$1"; }
# small_in SLUG KIND: a task whose one story is in its task directory, approved as Lem does it for KIND
# (`correction` in his name, `feature` by him), with a worktree on its branch and no plan on it
small_in() {
  local tree
  project --repo "$SMALL" task-dir "$1" --ask "The date column of the report must never wrap." >/dev/null
  printf '%s\n' '## Stories' '' "Kind: $2, because the ask is one sentence." '' '1. The date column of the report never wraps: 2026-11-17 stays on one line.' > "$(dir_of "$1")/stories.md"
  if [ "$2" = correction ]; then stories approve "$1" --file "$(dir_of "$1")/stories.md" --correction >/dev/null; else stories approve "$1" --file "$(dir_of "$1")/stories.md" >/dev/null; fi
  tree=$(project --repo "$SMALL" worktree-dir "$1")
  git -C "$SMALL" worktree add -q "$tree" -b "fix/$1" main
  echo "$tree"
}
# built SLUG TREE: the builder's change, its test, the test line under the story, and the state `ready`
built() {
  mkdir -p "$2/tests" && printf '%s\n' 'td { white-space: nowrap; }' > "$2/$1.css" && echo "grep -q nowrap $1.css" > "$2/tests/$1.sh"
  git -C "$2" add -A && git -C "$2" commit -q -m "fix(report): the date column never wraps"
  printf '%s\n' "   - test: \`sh tests/$1.sh\` in \`tests/$1.sh\`" >> "$(dir_of "$1")/stories.md"
  project --repo "$2" state "$1" ready "the small change is built" >/dev/null
}
reds() { grep -c "\"event\": \"task.red\", \"task\": \"$1\"" "$SMALL/.git/lem/events.jsonl"; }
SHORT=$WORK/short-notes.md
printf '%s\n' 'none' > "$SHORT"

# A small change goes from Lem's approval in his name to the merge with no plan file on the branch.
tree=$(small_in date-nowrap correction)
built date-nowrap "$tree"
shown=$(stories show date-nowrap 2>&1 | field '(d["small"], d["kind"], d["plan"].endswith("tasks/date-nowrap/stories.md"))' 2>&1 || true)
s start date-nowrap >/dev/null && s base date-nowrap >/dev/null
gated=$(s gate date-nowrap 2>&1 | field '(d["green"], d["polish"], d["stories"]["ok"])' 2>&1 || true)
due=$(s read date-nowrap 2>&1 | field '(d["due"], d["floor"], d["small"], d["tasks"])' 2>&1 || true)
s read date-nowrap --record "$(clean 1)" >/dev/null 2>&1 || true
proposed=$(s propose date-nowrap --title "fix(report): the date column never wraps" --notes "$SHORT" 2>&1 | field 'd["green"]' 2>&1 || true)
merged=$(s land date-nowrap --by agent 2>&1 | field 'd["pushed"]' 2>&1 || true)
text=$(dir_of date-nowrap)/pr.md
if [ "$shown" = "(True, 'correction', True)" ] && [ "$gated" = "(True, None, True)" ] && [ "$due" = "('review', 'read', True, 1)" ] \
  && [ "$proposed" = True ] && [ "$merged" = False ] && [ "$(status_in "$SMALL" date-nowrap)" = landed ] && [ "$(reds date-nowrap)" = 1 ] \
  && [ -z "$(git -C "$SMALL" ls-tree -r --name-only main -- docs/plans)" ] \
  && [ "$(sed -n 1p "$text")" = '**Green.** The checks passed with the bar where it was, and the review left no must-fix.' ] \
  && grep -qxF -- '1. The date column of the report never wraps: 2026-11-17 stays on one line.' "$text" \
  && grep -qxF -- "   - \`sh tests/date-nowrap.sh\`: passes on the branch, fails on the base commit" "$text" \
  && grep -qxF -- '- the review, round 1 (one read; answered: codex): clean, 0 must-fix, 0 should, 0 nit' "$text" \
  && ! grep -q 'polish pass\|## Decisions of the build\|personas asked\|size:' "$text" && [ "$(grep -c '' "$text")" -le 20 ]; then
  pass "a small change with its story in the task directory goes from Lem's approval through the gate, one read and a short pull request to an agent's merge, with no plan file on the branch and the stories' check run once"
else
  fail "a small change: $shown / $gated / $due / $proposed / $merged / reds $(reds date-nowrap) / $(cat "$text" 2>/dev/null)"
fi

# A feature keeps its stories at the top of its plan: with no plan file on the branch it is refused, also with a story file in the task directory.
tree=$(small_in date-feature feature)
built date-feature "$tree"
feature=$(stories show date-feature 2>&1 || true)
s start date-feature >/dev/null && s base date-feature >/dev/null
feature_gate=$(s gate date-feature 2>&1 || true)
if grep -qF "stories.md says \`Kind: feature\`: only a small change (\`Kind: correction\`) keeps its story in the task directory" <<<"$feature" \
  && grep -qF "A feature's stories are at the top of its plan" <<<"$feature_gate" && [ "$(kept_in "$SMALL" date-feature gated)" = None ]; then
  pass "a feature with no plan file on the branch is refused by the stories and by the gate, also with a story file in its task directory"
else
  fail "a feature with no plan: $feature / $feature_gate"
fi
project --repo "$SMALL" state date-feature dropped "the test is over" >/dev/null

# A small change whose diff reaches what guards the project is careful: the full set, not green, and a person merges it.
tree=$(small_in gate-edit correction)
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[gate]' 'commands = ["true", "true"]' '[flow]' 'topics = ["a customer is charged the wrong price"]' > "$tree/.lem/project.toml"
built gate-edit "$tree"
s start gate-edit >/dev/null && s base gate-edit >/dev/null && { s gate gate-edit > "$WORK/gate-edit.out" 2>&1 || true; }
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

# A small change does not lower the bar: there is no plan for the reason, and a lowered bar takes the feature path.
tree=$(small_in skips-test correction)
printf '%s\n' 'import pytest' '' '@pytest.mark.skip' 'def test_old():' '    assert True' > "$tree/tests/test_old.py"
built skips-test "$tree"
s start skips-test >/dev/null && s base skips-test >/dev/null
lowered=$(s gate skips-test 2>&1 || true)
if grep -qF "a small change does not lower the bar: tests/test_old.py" <<<"$lowered" && grep -qF "it is a feature" <<<"$lowered" && [ "$(kept_in "$SMALL" skips-test gated)" = None ]; then
  pass "a small change that lowers the bar is refused at the gate, with the feature path named, since a small change has no plan to give the reason in"
else
  fail "a small change that lowers the bar: $(grep -v "^ \|^[{}]" <<<"$lowered")"
fi
project --repo "$SMALL" state skips-test dropped "the test is over" >/dev/null

finish
