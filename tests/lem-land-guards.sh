#!/usr/bin/env bash
# The landing's guards and refusals: what keeps a tree the checks did not pass on off the base
# branch, and each refusal that names the step after it, run as it names it. No remote here, but
# for the one check that needs a base that moves.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

GRD=$WORK/guards
git init -q -b main "$GRD" && ident "$GRD"
project --repo "$GRD" init --base main >/dev/null
# grd_settings COMMANDS: the settings with these gate commands, a TOML list's items; HISTORY=squash for one commit
grd_settings() { printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' "history = \"${HISTORY:-keep}\"" '[gate]' "commands = [$1]" > "$GRD/.lem/project.toml"; }
grd_settings '"true"'
mkdir -p "$GRD/tests" && printf '%s\n' 'def test_old():' '    assert 1 + 1 == 2' > "$GRD/tests/test_old.py"
git -C "$GRD" add -A && git -C "$GRD" commit -q -m "chore: start"
g() { land --repo "$GRD" "$@"; }
wt() { project --repo "$GRD" worktree-dir "$1"; }
# set_kept SLUG KEY JSON: one value of the landing's record, as a hand or a bug of another tool would write it
set_kept() {
  "$PY" -c 'import json, sys; p = sys.argv[1]; d = json.load(open(p)); d[sys.argv[2]] = json.loads(sys.argv[3]); json.dump(d, open(p, "w"))' \
    "$GRD/.git/lem/tasks/$1/landing.json" "$2" "$3"
}
to_proposed() {
  g start "$1" >/dev/null && g base "$1" >/dev/null && g gate "$1" >/dev/null && g read "$1" --record "$(clean 1)" >/dev/null \
    && g propose "$1" --title "fix: $1" --notes "$NOTES" >/dev/null
}

# A worktree on no branch: the landing needs the branch, which `clean` deletes after the merge.
task_in "$GRD" detached d.txt d
tree=$(wt detached)
git -C "$tree" switch -q --detach
no_branch=$(g start detached 2>&1 || true)
no_branch_status=$(status_in "$GRD" detached)
git -C "$tree" switch -q fix/detached
g start detached >/dev/null 2>&1 || true
if grep -qF "the task's worktree is on no branch" <<<"$no_branch" && grep -qF "git -C $tree switch fix/detached" <<<"$no_branch" \
  && [ "$no_branch_status" = ready ] && [ "$(status_in "$GRD" detached)" = landing ] && [ "$(kept_in "$GRD" detached branch)" = fix/detached ]; then
  pass "start refuses a worktree on no branch and names the switch that puts it back on the task's branch; after it, start takes the task"
else
  fail "start on a detached worktree: $no_branch / $no_branch_status / $(status_in "$GRD" detached)"
fi
project --repo "$GRD" state detached dropped "the test is over" >/dev/null

# No gate command: start blocks the task, and once the commands are there, the same start takes it back.
grd_settings ''
task_in "$GRD" no-gate n.txt n
blocked=$(g start no-gate 2>&1 || true)
was=$(status_in "$GRD" no-gate)
again=$(g start no-gate 2>&1 || true)
grd_settings '"true"'
g start no-gate >/dev/null 2>&1 || true
if grep -qF "the project has no gate command" <<<"$blocked" && grep -qF "then run \`land.py start no-gate\` again" <<<"$blocked" && [ "$was" = blocked ] \
  && grep -qF "the project has no gate command" <<<"$again" && [ "$(status_in "$GRD" no-gate)" = landing ]; then
  pass "with no gate command start blocks the task and says to add the commands and run start again, which then takes the task it blocked"
else
  fail "start after the gate commands were added: $blocked / $was / $again / $(status_in "$GRD" no-gate)"
fi
project --repo "$GRD" state no-gate dropped "the test is over" >/dev/null

# A task whose worktree was removed by hand while it held the landing line: every message on the way names the step out.
task_in "$GRD" stuck s.txt s
g start stuck >/dev/null
stuck_tree=$(wt stuck)
rm -rf "$stuck_tree"
task_in "$GRD" waiting w.txt w
line=$(g start waiting 2>&1 || true)
gone=$(g base stuck 2>&1 || true)
git -C "$GRD" worktree prune && git -C "$GRD" worktree add -q "$stuck_tree" fix/stuck
back=$(g base stuck 2>/dev/null | field 'd["ahead"]' 2>/dev/null || true)
project --repo "$GRD" state stuck ready "the landing starts over" >/dev/null
g start waiting >/dev/null 2>&1 || true
if grep -qF "stuck is in \`landing\`" <<<"$line" && grep -qF "\`project.py state stuck ready \"WHY\"\`" <<<"$line" && grep -qF "\`project.py state stuck dropped \"WHY\"\`" <<<"$line" \
  && grep -qF "the task has no worktree at $stuck_tree" <<<"$gone" && grep -qF "\`git -C $GRD worktree prune\`" <<<"$gone" \
  && grep -qF "\`git -C $GRD worktree add $stuck_tree fix/stuck\`" <<<"$gone" && [ "$back" = 1 ] && [ "$(status_in "$GRD" waiting)" = landing ]; then
  pass "a landing task whose worktree is gone holds the line: the refusal of another start names the two states that give it back, the task's own step names the git commands that put the worktree back, and each works as named"
else
  fail "a landing task with no worktree: $line / $gone / $back / $(status_in "$GRD" waiting)"
fi
project --repo "$GRD" state stuck dropped "the test is over" >/dev/null
project --repo "$GRD" state waiting dropped "the test is over" >/dev/null

# A landing record that is not JSON stops every step with its path, and the way out land.py names starts the landing over.
task_in "$GRD" broken-record b.txt b
g start broken-record >/dev/null
printf '{"branch": "fix/broken-' > "$GRD/.git/lem/tasks/broken-record/landing.json"
broken=$(g base broken-record 2>&1 || true)
mv "$GRD/.git/lem/tasks/broken-record/landing.json" "$WORK/landing.json.broken"
project --repo "$GRD" state broken-record ready "the landing starts over" >/dev/null
g start broken-record >/dev/null 2>&1 || true
if grep -qF "$GRD/.git/lem/tasks/broken-record/landing.json does not read as JSON" <<<"$broken" && ! grep -q Traceback <<<"$broken" \
  && [ "$(status_in "$GRD" broken-record)" = landing ] && [ "$(kept_in "$GRD" broken-record branch)" = fix/broken-record ]; then
  pass "a landing record that is not JSON stops a step with its path and no traceback, and moving it aside, the state ready and start begin the landing again"
else
  fail "a broken landing record: $broken / $(status_in "$GRD" broken-record)"
fi
project --repo "$GRD" state broken-record dropped "the test is over" >/dev/null

# What lands is what was proposed and gated: the record of the tip, of the gate and of its tree, each
# checked by land. The record is edited here; a run of the steps the refusal names lands the new tip.
task_in "$GRD" guarded y.txt y
tree=$(wt guarded)
g start guarded >/dev/null && g base guarded >/dev/null && g gate guarded >/dev/null && g read guarded --record "$(clean 1)" >/dev/null
no_notes=$(g propose guarded --title "fix: y" --notes "$WORK/no-such-notes.md" 2>&1 || true)
two_lines=$(g propose guarded --title $'fix: y\nand more' --notes "$NOTES" 2>&1 || true)
unwritten=$([ -e "$GRD/.git/lem/tasks/guarded/pr.md" ] && echo written || echo none)
g propose guarded --title "fix: y" --notes "$NOTES" >/dev/null
gated_was=$(kept_in "$GRD" guarded gated)
tree_was=$(kept_in "$GRD" guarded tree)
set_kept guarded tree "\"$(git -C "$GRD" rev-parse 'main^{tree}')\""
c1=$(g land guarded --by owner 2>&1 || true)
set_kept guarded tree "\"$tree_was\""
set_kept guarded gated "\"$(git -C "$GRD" rev-parse main)\""
c3=$(g land guarded --by owner 2>&1 || true)
set_kept guarded gated null
ungated=$(g land guarded --by owner 2>&1 || true)
set_kept guarded gated "\"$gated_was\""
echo more > "$tree/y2.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: after the proposal"
main_was=$(git -C "$GRD" rev-parse main)
c2=$(g land guarded --by owner 2>&1 || true)
unlanded=$(git -C "$GRD" rev-parse main)
g start guarded >/dev/null && g base guarded >/dev/null && g gate guarded >/dev/null && g read guarded --record "$(clean 2)" >/dev/null \
  && g propose guarded --title "fix: y" --notes "$NOTES" >/dev/null && g land guarded --by owner >/dev/null || true
if grep -qF "is not a file; --notes names the notes" <<<"$no_notes" && grep -qF -- "--title is one line" <<<"$two_lines" && [ "$unwritten" = none ] \
  && grep -qF "the tree that would land differs from the tree the gate passed on" <<<"$c1" \
  && grep -qF "the branch's tip is not the commit the gate passed on" <<<"$c3" \
  && grep -qF "no green check is on record for this tip" <<<"$ungated" \
  && grep -qF "the branch's tip is not the tip that was proposed" <<<"$c2" \
  && grep -qF "run \`land.py start\`, \`land.py base\`, \`land.py gate\` and \`land.py propose\` again" <<<"$c2" \
  && [ "$unlanded" = "$main_was" ] \
  && [ "$(status_in "$GRD" guarded)" = landed ] && [ "$(git -C "$GRD" show main:y2.txt)" = more ]; then
  pass "propose refuses notes that are no file and a title of two lines before it writes anything; land refuses a tree, a gated commit and a tip other than the ones on record, and no record of a gate; after a commit past the proposal the steps the refusal names land the new tip"
else
  fail "the guards of land: $no_notes / $two_lines / $unwritten / $c1 / $c3 / $ungated / $c2 / $(status_in "$GRD" guarded)"
fi
land --repo "$GRD" clean guarded >/dev/null 2>&1 || true

# One commit for the branch, refused by a commit hook: the branch stays as it was, and the next run lands it.
HISTORY=squash grd_settings '"true"'
task_in "$GRD" squashed z.txt z
tree=$(wt squashed)
to_proposed squashed
before=$(git -C "$tree" rev-parse HEAD)
printf '%s\n' '#!/bin/sh' 'echo "no commit here" >&2' 'exit 1' > "$GRD/.git/hooks/pre-commit" && chmod +x "$GRD/.git/hooks/pre-commit"
hooked=$(g land squashed --by owner --message "fix: z" 2>&1 || true)
hooked_tip=$(git -C "$tree" rev-parse HEAD)
rm "$GRD/.git/hooks/pre-commit"
g land squashed --by owner --message "fix: z" >/dev/null 2>&1 || true
grd_settings '"true"'
if grep -qF "the one commit was refused, and the branch is as it was: no commit here" <<<"$hooked" && grep -qF "another --message to \`land.py land squashed\`" <<<"$hooked" \
  && [ "$hooked_tip" = "$before" ] && [ -z "$(git -C "$tree" status --porcelain)" ] && [ "$(status_in "$GRD" squashed)" = landed ] \
  && [ "$(git -C "$GRD" log -1 --format=%s main)" = "fix: z" ]; then
  pass "a commit hook that refuses the one commit leaves the branch as the gate saw it, and the run after it lands"
else
  fail "a refused one commit: $hooked / $hooked_tip / $before / $(status_in "$GRD" squashed)"
fi
land --repo "$GRD" clean squashed >/dev/null 2>&1 || true

# The base moved by a file the gate ignores, and the rebase onto it stops: nothing changes, and the refusal names the steps.
GO=$WORK/guards-origin.git
GC=$WORK/guards-clone
git init -q --bare -b main "$GO"
git clone -q "$GO" "$GC" 2>/dev/null && ident "$GC"
project --repo "$GC" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' '[gate]' 'commands = ["true"]' 'ignores = ["docs/*"]' > "$GC/.lem/project.toml"
mkdir -p "$GC/docs" && echo one > "$GC/docs/note.md"
git -C "$GC" add -A && git -C "$GC" commit -q -m "chore: start" && git -C "$GC" push -q origin main
task_in "$GC" docs-meet q.txt q
tree=$(project --repo "$GC" worktree-dir docs-meet)
echo branch > "$tree/docs/note.md" && git -C "$tree" commit -q -am "docs: the branch's note"
land --repo "$GC" start docs-meet >/dev/null && land --repo "$GC" base docs-meet >/dev/null && land --repo "$GC" gate docs-meet >/dev/null \
  && land --repo "$GC" read docs-meet --record "$(clean 1)" >/dev/null && land --repo "$GC" propose docs-meet --title "fix: q" --notes "$NOTES" >/dev/null
proposed=$(git -C "$tree" rev-parse HEAD)
gother=$WORK/guards-other
git clone -q "$GO" "$gother" && ident "$gother"
echo base > "$gother/docs/note.md" && git -C "$gother" commit -q -am "docs: the base's note" && git -C "$gother" push -q origin main
stopped=$(land --repo "$GC" land docs-meet --by owner 2>&1 || true)
if grep -qF "origin/main moved after the gate ran and the rebase onto it stopped, and the branch is as it was" <<<"$stopped" \
  && grep -qF "run \`land.py start\`, \`land.py base\`, \`land.py gate\` and \`land.py propose\` again, where \`base\` names the files that meet" <<<"$stopped" \
  && [ "$(git -C "$tree" rev-parse HEAD)" = "$proposed" ] && [ -z "$(git -C "$tree" status --porcelain)" ] && [ "$(status_in "$GC" docs-meet)" = open ] \
  && [ "$(git -C "$GO" log -1 --format=%s main)" = "docs: the base's note" ]; then
  pass "a base that moved only by ignored files and whose rebase stops is refused by land with the branch as it was proposed, and the steps that run again"
else
  fail "the rebase in land stops: $stopped / $(status_in "$GC" docs-meet)"
fi

# The stories' check needs a change: a branch the base holds whole has no commit for a test to hold.
task_in "$GRD" on-base o.txt o
git -C "$GRD" merge -q --ff-only fix/on-base
on_base=$("$PY" -B "$STORIES" --repo "$GRD" red on-base 2>&1 || true)
if grep -qF "the branch has no commit beyond main, so there is no change for a test to hold" <<<"$on_base"; then
  pass "the stories' check refuses a branch with no commit beyond the base"
else
  fail "stories red with no commit beyond the base: $on_base"
fi

finish
