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
small_task_in "$GRD" detached d.txt d
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
small_task_in "$GRD" no-gate n.txt n
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
# A gate that runs no command is never green: here the main checkout's settings lose their commands after start.
g base no-gate >/dev/null 2>&1 || true
grd_settings ''
empty=$(g gate no-gate 2>&1 || true)
grd_settings '"true"'
if grep -qF "the gate has no command to run" <<<"$empty" && [ "$(kept_in "$GRD" no-gate gated)" = None ] && ! grep -q '"event": "task.red", "task": "no-gate"' "$GRD/.git/lem/events.jsonl"; then
  pass "a gate with no command to run refuses, and records no green tip"
else
  fail "a gate of no command: $empty / $(kept_in "$GRD" no-gate gated)"
fi
project --repo "$GRD" state no-gate dropped "the test is over" >/dev/null

# A task whose worktree was removed by hand while it held the landing line: every message on the way names the step out.
small_task_in "$GRD" stuck s.txt s
g start stuck >/dev/null
stuck_tree=$(wt stuck)
rm -rf "$stuck_tree"
small_task_in "$GRD" waiting w.txt w
line=$(g start waiting 2>&1 || true)
gone=$(g base stuck 2>&1 || true)
git -C "$GRD" worktree prune && git -C "$GRD" worktree add -q "$stuck_tree" fix/stuck
back=$(g base stuck 2>/dev/null | field 'd["ahead"]' 2>/dev/null || true)
project --repo "$GRD" state stuck ready --start-over "the landing starts over" >/dev/null
g start waiting >/dev/null 2>&1 || true
if grep -qF "stuck is in \`landing\`" <<<"$line" && grep -qF "\`project.py state stuck ready --start-over \"WHY\"\`" <<<"$line" && grep -qF "\`project.py state stuck dropped \"WHY\"\`" <<<"$line" \
  && grep -qF "the task has no worktree at $stuck_tree" <<<"$gone" && grep -qF "\`git -C $GRD worktree prune\`" <<<"$gone" \
  && grep -qF "\`git -C $GRD worktree add $stuck_tree fix/stuck\`" <<<"$gone" && [ "$back" = 1 ] && [ "$(status_in "$GRD" waiting)" = landing ]; then
  pass "a landing task whose worktree is gone holds the line: the refusal of another start names the two states that give it back, the task's own step names the git commands that put the worktree back, and each works as named"
else
  fail "a landing task with no worktree: $line / $gone / $back / $(status_in "$GRD" waiting)"
fi
project --repo "$GRD" state stuck dropped "the test is over" >/dev/null
project --repo "$GRD" state waiting dropped "the test is over" >/dev/null

# A landing record that is not JSON stops every step with its path, and the way out land.py names starts the landing over.
small_task_in "$GRD" broken-record b.txt b
g start broken-record >/dev/null
printf '{"branch": "fix/broken-' > "$GRD/.git/lem/tasks/broken-record/landing.json"
broken=$(g base broken-record 2>&1 || true)
mv "$GRD/.git/lem/tasks/broken-record/landing.json" "$WORK/landing.json.broken"
project --repo "$GRD" state broken-record ready --start-over "the landing starts over" >/dev/null
g start broken-record >/dev/null 2>&1 || true
if grep -qF "$GRD/.git/lem/tasks/broken-record/landing.json does not read as JSON" <<<"$broken" && ! grep -q Traceback <<<"$broken" \
  && [ "$(status_in "$GRD" broken-record)" = landing ] && [ "$(kept_in "$GRD" broken-record branch)" = fix/broken-record ]; then
  pass "a landing record that is not JSON stops a step with its path and no traceback, and moving it aside, the state ready and start begin the landing again"
else
  fail "a broken landing record: $broken / $(status_in "$GRD" broken-record)"
fi
project --repo "$GRD" state broken-record dropped "the test is over" >/dev/null

# What a gate command writes that git does not know, a cache of Python's bytecode in a repository
# with no ignore rule for it, is the run's output and not the tree it judged: the gate passes, removes
# those files and the folders they emptied, names them, and keeps a folder that holds a tracked file.
small_task_in "$GRD" gate-caches c.txt c
tree=$(wt gate-caches)
g start gate-caches >/dev/null && g base gate-caches >/dev/null
grd_settings '"mkdir -p shop/__pycache__ tests/__pycache__ && touch shop/__pycache__/c.pyc tests/__pycache__/t.pyc left.txt"'
cached=$(g gate gate-caches 2>&1 || true)
grd_settings '"true"'
if [ "$(field '(d["green"], d["removed_untracked"])' <<<"$cached" 2>/dev/null)" = "(True, ['left.txt', 'shop/__pycache__/c.pyc', 'tests/__pycache__/t.pyc'])" ] \
  && [ ! -e "$tree/shop" ] && [ ! -e "$tree/tests/__pycache__" ] && [ ! -e "$tree/left.txt" ] && [ -f "$tree/tests/gate-caches.sh" ] \
  && [ -z "$(git -C "$tree" status --porcelain --untracked-files=all)" ] && [ "$(kept_in "$GRD" gate-caches gated)" = "$(git -C "$tree" rev-parse HEAD)" ] \
  && [ "$(tail -n 1 "$GRD/.git/lem/tasks/gate-caches/gate/01.log")" = "land.py removed what the gate's commands left untracked: left.txt, shop/__pycache__/c.pyc, tests/__pycache__/t.pyc" ]; then
  pass "a gate command that writes a cache folder and a file git does not know passes: the gate removes them and the folders they emptied, keeps the tracked folder, names them in its output and in one line of its log, and records the tip"
else
  fail "a gate that leaves caches: $cached / $(git -C "$tree" status --porcelain --untracked-files=all)"
fi
# A file that was there before the run is someone's: the gate removes none, it refuses, and so does start.
echo mine > "$tree/mine.txt"
before_gate=$(g gate gate-caches 2>&1 || true)
project --repo "$GRD" state gate-caches ready --start-over "the landing starts over" >/dev/null
before_start=$(g start gate-caches 2>&1 || true)
if grep -qF "the worktree has changes nobody committed" <<<"$before_gate" && grep -qF "mine.txt" <<<"$before_gate" \
  && grep -qF "the worktree has changes nobody committed" <<<"$before_start" && [ "$(cat "$tree/mine.txt")" = mine ]; then
  pass "a file that was untracked before the gate is not removed: the gate refuses the worktree, and start refuses it as before"
else
  fail "an untracked file before the gate: $before_gate / $before_start"
fi
rm -f "$tree/mine.txt"
project --repo "$GRD" state gate-caches dropped "the test is over" >/dev/null

# The gate judges one tree: a command that changes a tracked file or makes a commit changed it, and a
# story's test that passes on the base commit too holds nothing. Each refusal records no green tip.
small_task_in "$GRD" gate-writes x.txt x
tree=$(wt gate-writes)
g start gate-writes >/dev/null && g base gate-writes >/dev/null
tip=$(git -C "$tree" rev-parse HEAD)
grd_settings '"echo y >> x.txt && touch left.txt"'
left=$(g gate gate-writes 2>&1 || true)
left_gated=$(kept_in "$GRD" gate-writes gated)
git -C "$tree" checkout -q -- x.txt
grd_settings '"echo x > made.txt && git add made.txt && git -c user.name=t -c user.email=t@t commit -q -m made"'
made=$(g gate gate-writes 2>&1 || true)
made_gated=$(kept_in "$GRD" gate-writes gated)
git -C "$tree" reset -q --hard "$tip"
grd_settings '"true"'
echo true > "$tree/tests/gate-writes.sh" && git -C "$tree" commit -q -am "test: one that holds nothing"
weak=$(g gate gate-writes 2>&1 || true)
weak_gated=$(kept_in "$GRD" gate-writes gated)
git -C "$tree" reset -q --hard "$tip"
green=$(g gate gate-writes | field '(d["green"], d["tip"])')
if grep -qF "a gate command changed what git tracks, so its result is about another tree" <<<"$left" && grep -qx "M x.txt" <<<"$left" && ! grep -qF "?? left.txt" <<<"$left" \
  && [ ! -e "$tree/left.txt" ] && [ "$left_gated" = None ] \
  && grep -qF "a gate command made a commit on the branch" <<<"$made" && grep -qF "git -C $tree reset --hard $tip" <<<"$made" && [ "$made_gated" = None ] \
  && grep -qF "passes on the base commit too" <<<"$weak" && [ "$weak_gated" = None ] \
  && [ "$green" = "(True, '$tip')" ] && [ "$(kept_in "$GRD" gate-writes tree)" = "$(git -C "$tree" rev-parse "$tip^{tree}")" ]; then
  pass "the gate refuses a command that edits a tracked file, one that makes a commit, and a story's test that passes on the base commit, and records no green tip for any; a green gate records the tip and that tip's tree"
else
  fail "what the gate judges: $left / $made / $weak / $green"
fi
project --repo "$GRD" state gate-writes dropped "the test is over" >/dev/null

# What lands is what was proposed and gated: the record of the tip, of the gate and of its tree, each
# checked by land. The record is edited here; a run of the steps the refusal names lands the new tip.
small_task_in "$GRD" guarded y.txt y
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
small_task_in "$GRD" squashed z.txt z
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

# The bar: a test file moved out of the tests is one the tests lose, and a focus mark runs one test alone.
small_task_in "$GRD" bar-moves m.txt m
tree=$(wt bar-moves)
mkdir -p "$tree/attic" && git -C "$tree" mv tests/test_old.py attic/old.py
printf '%s\n' 'it.only("runs alone", () => {});' 'fit("runs alone too", () => {});' 'fdescribe("a group alone", () => {});' \
  'test.only("one test", () => {});' 'describe.only("one group", () => {});' 'profit(1);' > "$tree/tests/focus.test.js"
git -C "$tree" add -A && git -C "$tree" commit -q -m "test: moved and focused"
g start bar-moves >/dev/null && g base bar-moves >/dev/null
moved=$(g gate bar-moves 2>/dev/null || true)
moved_err=$(g gate bar-moves 2>&1 >/dev/null || true)
if [ "$(field 'sorted((e["file"], e["what"]) for e in d["bar"]["lowered"])' <<<"$moved" 2>/dev/null)" \
  = "[('tests/focus.test.js', 'describe.only'), ('tests/focus.test.js', 'fdescribe'), ('tests/focus.test.js', 'fit'), ('tests/focus.test.js', 'it.only'), ('tests/focus.test.js', 'test.only'), ('tests/test_old.py', 'a test file is moved out of the tests, to attic/old.py')]" ] \
  && grep -qF "tests/focus.test.js (it.only);" <<<"$moved_err" && ! grep -qF "only()" <<<"$moved_err" && [ "$(kept_in "$GRD" bar-moves gated)" = None ]; then
  pass "a test file moved out of the tests lowers the bar as a deleted one does, and so does a mark that runs one test or group alone, named without the call's parenthesis; a word that only ends the same way is none"
else
  fail "the bar of a move and of focus marks: $moved"
fi
project --repo "$GRD" state bar-moves dropped "the test is over" >/dev/null

# One start at a time: three starts at one moment, and one of them takes the landing line while the others are refused.
for slug in race-one race-two race-three; do small_task_in "$GRD" "$slug" "$slug.txt" r; done
for slug in race-one race-two race-three; do "$PY" -B "$LAND" --repo "$GRD" start "$slug" > "$WORK/$slug.start" 2>&1 & done
wait
raced=$(project --repo "$GRD" tasks | field 'sorted(t["status"] for t in d if t["slug"].startswith("race-"))')
refused=$(grep -l "is in \`landing\`: one branch lands at a time" "$WORK"/race-*.start | grep -c '' || true)
if [ "$raced" = "['landing', 'ready', 'ready']" ] && [ "$refused" = 2 ]; then
  pass "two starts at one moment take turns under a lock: one task takes the landing line, and each other start finds it there and is refused"
else
  fail "starts at one moment: $raced, $refused refused / $(cat "$WORK"/race-*.start)"
fi
for slug in race-one race-two race-three; do project --repo "$GRD" state "$slug" dropped "the test is over" >/dev/null; done

# A gate command runs in a process group of its own: what it leaves running ends with it, and a gate that is
# stopped ends the command it runs, with what that command started, and keeps no result.
small_task_in "$GRD" gate-group g.txt g
# gone_soon PID: wait three seconds at most for the process to end; the sleeps here last a minute, so only an end the gate made counts
gone_soon() { local tries=15; while kill -0 "$1" 2>/dev/null && [ "$tries" -gt 0 ]; do sleep 0.2; tries=$((tries - 1)); done; }
g start gate-group >/dev/null && g base gate-group >/dev/null
grd_settings "\"sleep 61 > /dev/null 2>&1 & echo \$! > $WORK/left.pid\""
g gate gate-group >/dev/null 2>&1 || true
left=$(cat "$WORK/left.pid")
gone_soon "$left"
left_state=$(kill -0 "$left" 2>/dev/null && echo alive || echo ended)
grd_settings "\"sleep 62 > /dev/null 2>&1 & echo \$! > $WORK/held.pid; wait\""
"$PY" -B "$LAND" --repo "$GRD" gate gate-group > "$WORK/stopped.out" 2>&1 &
gate_pid=$!
soon test -s "$WORK/held.pid"
kill -TERM "$gate_pid" 2>/dev/null || true
wait "$gate_pid" || true
held=$(cat "$WORK/held.pid")
gone_soon "$held"
held_state=$(kill -0 "$held" 2>/dev/null && echo alive || echo ended)
grd_settings '"true"'
if [ "$left_state" = ended ] && [ "$held_state" = ended ] && grep -qF "the gate was stopped, and the command that ran is ended" "$WORK/stopped.out" \
  && [ "$(kept_in "$GRD" gate-group gated)" = None ]; then
  pass "a gate command's process group ends with it, so a process it left behind is ended; a gate that is stopped ends the command that runs and what it started, says so, and keeps no result"
else
  fail "a gate command's processes: left $left_state, held $held_state / $(cat "$WORK/stopped.out")"
fi
kill "$left" "$held" 2>/dev/null || true
project --repo "$GRD" state gate-group dropped "the test is over" >/dev/null

# A branch with nothing of its own: base says so with the step that ends the task, and clean deletes the branch
# of a dropped task that holds no commit of its own, while one with commits stays.
project --repo "$GRD" task-dir empty-branch --ask "Nothing." >/dev/null
etree=$(wt empty-branch)
git -C "$GRD" worktree add -q "$etree" -b fix/empty-branch main
project --repo "$etree" state empty-branch ready "the report is written" >/dev/null
g start empty-branch >/dev/null
nothing=$(g base empty-branch 2>&1 || true)
project --repo "$GRD" state empty-branch dropped "nothing to land" >/dev/null
emptied=$(g clean empty-branch 2>&1 || true)
kept_branch=$(g clean detached 2>&1 || true)
if grep -qF "the branch has no commit that main lacks: there is nothing to land" <<<"$nothing" && grep -qF "\`project.py state empty-branch dropped \"WHY\"\`" <<<"$nothing" \
  && [ "$(field '(d["worktree"], d["branch"], d["branch_left"])' <<<"$emptied" 2>/dev/null)" = "(True, 'fix/empty-branch', None)" ] \
  && ! git -C "$GRD" rev-parse -q --verify fix/empty-branch >/dev/null \
  && [ "$(field '(d["worktree"], d["branch"])' <<<"$kept_branch" 2>/dev/null)" = "(True, None)" ] \
  && grep -qF "fix/detached holds the dropped task's commits" <<<"$kept_branch" && git -C "$GRD" rev-parse -q --verify fix/detached >/dev/null; then
  pass "a branch with no commit of its own is refused by base with the step that ends the task; clean deletes a dropped task's branch the base holds, and keeps one with commits of its own, with how to delete it"
else
  fail "an empty branch: $nothing / $emptied / $kept_branch"
fi

# The base moved by a file the gate ignores, and the rebase onto it stops: nothing changes, and the refusal names the steps.
GO=$WORK/guards-origin.git
GC=$WORK/guards-clone
git init -q --bare -b main "$GO"
git clone -q "$GO" "$GC" 2>/dev/null && ident "$GC"
project --repo "$GC" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' '[gate]' 'commands = ["true"]' 'ignores = ["docs/*"]' > "$GC/.lem/project.toml"
mkdir -p "$GC/docs" && echo one > "$GC/docs/note.md"
git -C "$GC" add -A && git -C "$GC" commit -q -m "chore: start" && git -C "$GC" push -q origin main
small_task_in "$GC" docs-meet q.txt q
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
small_task_in "$GRD" on-base o.txt o
git -C "$GRD" merge -q --ff-only fix/on-base
on_base=$("$PY" -B "$STORIES" --repo "$GRD" red on-base 2>&1 || true)
if grep -qF "the branch has no commit beyond main, so there is no change for a test to hold" <<<"$on_base"; then
  pass "the stories' check refuses a branch with no commit beyond the base"
else
  fail "stories red with no commit beyond the base: $on_base"
fi

finish
