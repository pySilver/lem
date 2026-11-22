#!/usr/bin/env bash
# The landing, part two: the polish pass, a review of the change as it is, the bar, what makes a
# request careful, and who merges it, on an origin that the stand-in for `gh` answers for (lib.sh). tests/lem-land-local.sh is part one; the two are one block cut in
# two, so that each runs in about half the time, on a repository of its own with the same start.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

LOCAL=$WORK/local
git init -q -b main "$LOCAL" && ident "$LOCAL"
project --repo "$LOCAL" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' 'land = "agent"' '[checks]' 'commands = ["true"]' '[flow]' 'topics = ["a customer is charged the wrong price"]' > "$LOCAL/.lem/project.toml"
mkdir -p "$LOCAL/tests" "$LOCAL/docs" && printf '%s\n' 'def test_base():' '    assert 1 + 1 == 2' '    assert 2 + 2 == 4' > "$LOCAL/tests/test_base.py" && echo guide > "$LOCAL/docs/guide.md"
printf '%s\n' 'import plugin # noqa: F401' 'import other  # noqa: E402' > "$LOCAL/plug.py"
# app_py FIRST SECOND: two functions alike in every line but their names, each longer than the
# three lines of context a diff shows, so the same edit in either gives the same lines of a diff
app_py() {
  printf '%s\n' 'def first():' '    a = 1' '    b = 2' '    c = 3' "    return \"$1\"" '    # the end' '' '' \
    'def second():' '    a = 1' '    b = 2' '    c = 3' "    return \"$2\"" '    # the end' '' '' 'def third():' '    return 3'
}
app_py old old > "$LOCAL/app.py"
printf '%s\n' 'pub fn one() -> i32 { 1 }' '#[cfg(test)]' 'mod tests {' '    #[test]' '    fn it_is_one() { assert_eq!(super::one(), 1); }' '}' > "$LOCAL/lib.rs"
git -C "$LOCAL" add -A && git -C "$LOCAL" commit -q -m "chore: start" && on_github "$LOCAL"
local_land() { land --repo "$LOCAL" "$@"; }
lcriteria() { "$PY" -B "$CRITERIA" --repo "$LOCAL" "$@"; }

# The polish pass: after the task's own work and before the machine checks, a fresh builder takes out
# what the change left behind, and the script checks what it committed. Here the test is the builder.
task_in "$LOCAL" polish-me p.txt p
tree=$(project --repo "$LOCAL" worktree-dir polish-me)
pdir=$LOCAL/.lem/state/tasks/polish-me
# the lead's change leaves a false comment, a debug line and a name nothing uses
printf '%s\n' '# writes q into p.txt' 'echo "debug: here" >&2' 'unused=1' 'echo p > p.txt' > "$tree/tool.sh"
git -C "$tree" add -A && git -C "$tree" commit -q -m "feat: the tool"
lead_tip=$(git -C "$tree" rev-parse HEAD)
echo '- docs/guide.md: says nothing of p.txt' > "$pdir/outside.md"
echo '## Outside defects' > "$pdir/report.md"
local_land start polish-me >/dev/null && local_land base polish-me >/dev/null
no_pass=$(local_land checks polish-me 2>&1 || true)
first=$(local_land polish polish-me)
echo '# writes p into p.txt' > "$tree/tool.sh"
dirty=$(local_land polish polish-me --done 2>&1 || true)
echo 'echo p > p.txt' >> "$tree/tool.sh" && git -C "$tree" commit -q -am "refactor: the tool says what it writes, and nothing else"
started=$(local_land checks polish-me 2>&1 || true)
again=$(local_land polish polish-me)
if grep -qF "polish-me takes the standard track, and no polish pass is on record for this landing: \`lem land polish polish-me\` starts it" <<<"$no_pass" \
  && [ "$(field '(d["size"], d["done"], d["before"], d["range"].split("..")[1], d["commits"], d["plan"].endswith("docs/plans/2026-11-15-polish-me.md"), d["report"], d["outside"], d["backlog"], d["frozen"])' <<<"$first")" \
  = "('full', False, '$lead_tip', '$lead_tip', ['$(git -C "$tree" rev-parse --short "$lead_tip") feat: the tool', '$(git -C "$tree" log -1 --format='%h %s' "$lead_tip~1")'], True, '$pdir/report.md', '$pdir/outside.md', 'docs/backlog', ['tests/polish-me.sh', 'docs/plans/2026-11-15-polish-me.md'])" ] \
  && [ "$(field '(d["before"], d["range"])' <<<"$again")" = "$(field '(d["before"], d["range"])' <<<"$first")" ] && [ "$(kept_in "$LOCAL" polish-me polish)" = "{'before': '$lead_tip', 'done': False}" ]; then
  pass "a full change's checks waits for the polish pass; polish prints the range of the task's own commits from the base, the plan, the report, the interview's outside.md, the backlog folder and the files the pass may not change, and keeps the tip it starts at, also when it is started again after the builder's first commit"
else
  fail "polish: $no_pass / $first / $again"
fi
if [ "$(grep '"event": "polish.start", "task": "polish-me"' "$LOCAL/.lem/state/events.jsonl" | field 'd["before"]' 2>&1)" = "${lead_tip:0:9}" ]; then
  pass "polish logs polish.start once, with the tip the pass starts at, and not again when it is started a second time before --done"
else
  fail "polish.start: $(grep '"polish.start"' "$LOCAL/.lem/state/events.jsonl")"
fi
# What --done refuses: a worktree with changes, a criterion's test changed, tests of the criteria that no longer hold.
echo '# and a note' >> "$tree/tests/polish-me.sh" && git -C "$tree" commit -q -am "test: a note"
frozen=$(local_land polish polish-me --done 2>&1 || true)
git -C "$tree" revert --no-edit HEAD >/dev/null
echo q > "$tree/p.txt" && git -C "$tree" commit -q -am "refactor: the word"
broken=$(local_land polish polish-me --done 2>&1 || true)
git -C "$tree" revert --no-edit HEAD >/dev/null
mkdir -p "$tree/docs/backlog" && printf '%s\n' '---' 'worth: later' 'where: docs/guide.md' 'added: 2026-11-16' '---' '# The guide says nothing of p.txt' > "$tree/docs/backlog/the-guide-says-nothing-of-p-txt.md"
git -C "$tree" add -A && git -C "$tree" commit -q -m "docs(backlog): the guide says nothing of p.txt"
done_out=$(local_land polish polish-me --done)
after_tip=$(git -C "$tree" rev-parse HEAD)
twice=$(local_land polish polish-me --done 2>&1 || true)
if grep -qF "the worktree has changes nobody committed" <<<"$dirty" && grep -qF "the polish pass started at $(git -C "$tree" rev-parse --short=9 "$lead_tip") and is not done" <<<"$started" \
  && grep -qF "the polish pass changed what it may not: tests/polish-me.sh (by " <<<"$frozen" \
  && grep -qF "after the polish pass the tests of the criteria do not hold" <<<"$broken" \
  && [ "$(field '(d["before"], d["after"], len(d["commits"]), d["filed"], d["criteria"]["ok"])' <<<"$done_out")" = "('$lead_tip', '$after_tip', 6, ['docs/backlog/the-guide-says-nothing-of-p-txt.md'], True)" ] \
  && grep -qF '"event": "polish", "task": "polish-me", "before": "'"${lead_tip:0:9}"'", "after": "'"${after_tip:0:9}"'", "commits": 6, "filed": ["docs/backlog/the-guide-says-nothing-of-p-txt.md"]' "$LOCAL/.lem/state/events.jsonl" \
  && grep -qF "the polish pass of this landing is done already" <<<"$twice" && [ "$(head -1 "$tree/tool.sh")" = '# writes p into p.txt' ]; then
  pass "polish --done refuses a worktree with changes, a pass that changed a criterion's test file, and one after which the tests of the criteria no longer hold; otherwise it runs them, logs one polish event with the tips, the commits and the items filed, and a pass is done once"
else
  fail "polish --done: $dirty / $started / $frozen / $broken / $done_out / $twice"
fi
# The gate: the pass is on the tip it checks while the commits after it are on top, and a rebase by `base` keeps it.
# On the tip the pass ended on, the checks take the pass's run of the criteria's tests; after a commit on top, and
# after a rebase, they run the tests themselves.
gated=$(local_land checks polish-me | field 'd["polish"]["after"]')
taken_kept=$("$PY" -c 'import json, sys; print(json.load(open(sys.argv[1]))["checks"]["criteria"].get("taken"))' "$pdir/landing.json")
# The pull request of checks that took the pass's result says so, with one line from the pass; start then takes
# the open task into the landing again, for a fix on top.
digest=$(lcriteria digest polish-me 2>/dev/null | field 'd["digest"]' 2>/dev/null || true)
project --repo "$LOCAL" log polish-me criteria.read by=lead asked:=2 answered:=2 'families:=["opus"]' 'silent:=[]' criteria:=1 flagged:=0 split:=false "digest=$digest" >/dev/null 2>&1 || true
local_land read polish-me --record "$(clean polish-me 1)" >/dev/null 2>&1 && local_land propose polish-me --title "feat: p" --notes "$NOTES" >/dev/null 2>&1 || true
local_land start polish-me >/dev/null
echo '# a fix' >> "$tree/tool.sh" && git -C "$tree" commit -q -am "fix: what a review found"
fixed_tip=$(git -C "$tree" rev-parse HEAD)
on_top=$(status_of local_land checks polish-me)
git -C "$tree" reset -q --hard "$after_tip~1" && echo 'echo p > p.txt' > "$tree/tool.sh" && git -C "$tree" commit -q -am "refactor: written again"
rewritten=$(local_land checks polish-me 2>&1 || true)
git -C "$tree" reset -q --hard "$after_tip" && echo '# a fix' >> "$tree/tool.sh" && git -C "$tree" commit -q -am "fix: what a review found"
echo late > "$LOCAL/polish-late.txt" && git -C "$LOCAL" add polish-late.txt && git -C "$LOCAL" commit -q -m "chore: a late file" && git -C "$LOCAL" push -q origin main
local_land base polish-me >/dev/null
moved=$(local_land checks polish-me | field 'd["polish"]["after"]')
rebased_tip=$(git -C "$tree" rev-parse HEAD)
if [ "$gated" = "$after_tip" ] && [ "$on_top" = 0 ] && grep -qF "the tip does not hold the polish pass's last commit (${after_tip:0:9})" <<<"$rewritten" \
  && [ "$moved" = "$(git -C "$tree" rev-parse HEAD~1)" ] && [ "$moved" != "$after_tip" ] && [ "$(git -C "$tree" log -1 --format=%s "$moved")" = "docs(backlog): the guide says nothing of p.txt" ]; then
  pass "the gate finds the polish pass on its tip with a fix on top of it, refuses a branch rewritten under the pass, and after a rebase by base knows the pass's last commit by its new name"
else
  fail "the gate and the polish pass: $gated / $on_top / $rewritten / $moved"
fi
# The tips of the task.red events of each run of the checks, between its gate.start and its gate.end: the refused
# pass's run and the pass's own lie outside every run.
reds=$("$PY" -c '
import json, sys
runs, inside = [], False
for line in open(sys.argv[1], encoding="utf-8"):
    event = json.loads(line)
    if event.get("task") != "polish-me":
        continue
    if event["event"] == "gate.start":
        runs.append([])
        inside = True
    elif event["event"] == "gate.end":
        inside = False
    elif event["event"] == "task.red" and inside:
        runs[-1].append(event["tip"])
print(runs)' "$LOCAL/.lem/state/events.jsonl")
project --repo "$LOCAL" state polish-me dropped "the test is over" >/dev/null
if [ "$reds" = "[[], ['${fixed_tip:0:9}'], ['${rebased_tip:0:9}']]" ] && [ "$taken_kept" = "{'from': 'polish', 'at': '$after_tip'}" ] && [ "$fixed_tip" != "$rebased_tip" ]; then
  pass "the checks on the tip the polish pass ended on run no test of the criteria and keep the pass's result with the pass and its commit; after a fix on top, and after a rebase by base, they run the tests themselves once, on the new tip"
else
  fail "the criteria's tests in the checks after the polish pass: $reds / $taken_kept / fix ${fixed_tip:0:9} / rebased ${rebased_tip:0:9}"
fi
if grep -qxF -- "- the polish pass: 6 commits, 1 item filed in the backlog" "$pdir/pr.md" \
  && grep -qxF -- "- the tests of the criteria: 1 pass on the branch and fail on the base commit, taken from the polish pass at ${after_tip:0:9}, and not run again" "$pdir/pr.md"; then
  pass "the pull request's checks say how many commits the polish pass made and how many items it filed, and that the tests of the criteria were taken from the pass at its commit and not run again"
else
  fail "the polish pass in the pull request: $(cat "$pdir/pr.md" 2>/dev/null)"
fi
# The pass runs once for a task: a red base that held the task, and its start again on a base that moved, keep it.
task_in "$LOCAL" polish-stays ps.txt ps
stree=$(project --repo "$LOCAL" worktree-dir polish-stays)
local_land start polish-stays >/dev/null && local_land base polish-stays >/dev/null && polish_in "$LOCAL" polish-stays
passed_at=$(kept_in "$LOCAL" polish-stays polish)
project --repo "$LOCAL" state polish-stays blocked "the base is red" >/dev/null
echo green > "$LOCAL/base-green.txt" && git -C "$LOCAL" add base-green.txt && git -C "$LOCAL" commit -q -m "fix: the base is green" && git -C "$LOCAL" push -q origin main
project --repo "$LOCAL" state polish-stays ready "the base is green again" >/dev/null
local_land start polish-stays >/dev/null && local_land base polish-stays >/dev/null
kept_pass=$(local_land polish polish-stays 2>&1 | field '(d["done"], d["before"])' 2>&1 || true)
gated_again=$(local_land checks polish-stays 2>&1 | field 'd["polish"]["after"]' 2>&1 || true)
starts=$(grep -c '"event": "polish.start", "task": "polish-stays"' "$LOCAL/.lem/state/events.jsonl" || true)
if grep -qF "'done': True" <<<"$passed_at" && [ "$kept_pass" = "(True, '$(git -C "$stree" rev-parse HEAD)')" ] && [ "$gated_again" = "$(git -C "$stree" rev-parse HEAD)" ] && [ "$starts" = 1 ]; then
  pass "a polish pass that was done stays done when a red base held the task and it starts again on a base that moved: polish says done, the checks find the pass by its new name, and no second pass starts"
else
  fail "the polish pass after a red base: $passed_at / $kept_pass / $gated_again / starts $starts"
fi
project --repo "$LOCAL" state polish-stays dropped "the test is over" >/dev/null

# No path rule lets a change skip its review: documentation gets one read at the least. A review that no
# source answered is none; it is started once more, and then the request goes on as not reviewed.
project --repo "$LOCAL" task-dir guide-change --ask "Say more in the guide." >/dev/null
tree=$(project --repo "$LOCAL" worktree-dir guide-change)
git -C "$LOCAL" worktree add -q "$tree" -b docs/guide-change main
plan_in "$tree" guide-change "no test: a sentence of the guide, which a person reads"
echo more >> "$tree/docs/guide.md" && git -C "$tree" add -A && git -C "$tree" commit -q -m "docs: more"
project --repo "$tree" state guide-change ready "the report is written" >/dev/null
read_in "$LOCAL" guide-change
local_land start guide-change >/dev/null && local_land base guide-change >/dev/null && polish_in "$LOCAL" guide-change
gate=$(local_land checks guide-change)
out=$(local_land read guide-change)
early=$(status_of local_land propose guide-change --title "docs: more" --notes "$NOTES")
quiet='{"kind": "read", "answered": [], "silent": [{"name": "codex", "why": "the model was at capacity"}]}'
once=$(local_land read guide-change --record "$(record guide-change 1 "$quiet")" | field '(d["recorded"]["verdict"], d["next"])')
# the second time the review agent itself ended with no files: the session writes the record of the attempt, which makes no careful call
printf '%s\n' '{"attempt": 2, "tip": "'"$(tip_of guide-change)"'", "kind": "read", "answered": [], "silent": [{"name": "the review agent", "why": "it ended with no files"}]}' > "$WORK/died.json"
twice=$(local_land read guide-change --record "$WORK/died.json" | field 'd["next"]')
local_land propose guide-change --title "docs: more" --notes "$NOTES" >/dev/null
text=$LOCAL/.lem/state/tasks/guide-change/pr.md
agent=$(local_land merge guide-change --by merger 2>&1 || true)
if [ "$(field '(d["criteria"]["ok"], [w["criterion"] for w in d["criteria"]["without_a_test"]])' <<<"$gate")" = "(True, [1])" ] \
  && [ "$(field '(d["due"], d["floor"])' <<<"$out")" = "('review', 'read')" ] && [ "$early" = 1 ] && [ "$once" = "('not reviewed', 'review')" ] && [ "$twice" = owner ] \
  && [ "$(sed -n 1p "$text")" = '**Not green.**' ] && [ "$(sed -n 3p "$text")" = '- not reviewed: the review was started twice and no source answered' ] \
  && grep -q '^- the review, round 1 (one read; no source answered; no answer from codex (the model was at capacity)): not reviewed$' "$text" \
  && grep -q '^   - no test: a sentence of the guide, which a person reads$' "$text" \
  && grep -q "^- the tests of the criteria: 0 pass on the branch and fail on the base commit; 1 criterion has no test$" "$text" \
  && grep -q "the request is not green (not reviewed" <<<"$agent"; then
  pass "a change of documentation only is not proposed without a review; a review that nobody answered is started once more, and after the second the request is proposed as not reviewed, which the merge agent does not merge; the record of a review agent that ended with no files is the session's, with no careful call"
else
  fail "a documentation change and a review with no answer: $gate / $out / $once / $twice / $agent / $(cat "$text" 2>/dev/null)"
fi
local_land merge guide-change --by owner >/dev/null && local_land clean guide-change >/dev/null

# A review is of the change as it is, and the change is known by its id, which land.change takes from
# git: on real commits of one repository, a change of one space is another change, and so is the same
# edit in another place of a file; a change that came back to what was reviewed is the same. Which review
# that makes due, and the floor that rises when the owner says careful after a review, are cases of
# tests/unit/test_land_text.py (`due_of`).
SPACES=$WORK/spaces
git init -q -b main "$SPACES" && ident "$SPACES"
app_py old old > "$SPACES/app.py" && git -C "$SPACES" add -A && git -C "$SPACES" commit -q -m "chore: start"
git -C "$SPACES" switch -q -c fix/spaces
echo 'value = "a b"' > "$SPACES/v.py" && app_py new old > "$SPACES/app.py" && git -C "$SPACES" add -A && git -C "$SPACES" commit -q -m "fix: a value"
# change_id: the id land.change gives the change of the branch from main, as it is now
change_id() {
  "$PY" -B -c 'import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); import land
task = land.Task.__new__(land.Task); task.worktree, task.onto = Path(sys.argv[2]), "main"; print(land.change(task)["patch"])' "$(dirname "$LAND")" "$SPACES"
}
reviewed=$(change_id)
# the same edit in the next function of the file: every line of the diff is the same, with its context, and only its place is not
app_py old new > "$SPACES/app.py" && git -C "$SPACES" commit -q -am "fix: the other function"
moved=$(change_id)
git -C "$SPACES" revert --no-edit HEAD >/dev/null
back=$(change_id)
echo 'value = "ab"' > "$SPACES/v.py" && git -C "$SPACES" commit -q -am "fix: no space"
spaced=$(change_id)
if [ -n "$reviewed" ] && [ "$moved" != "$reviewed" ] && [ "$back" = "$reviewed" ] && [ "$spaced" != "$reviewed" ] && [ "$spaced" != "$moved" ]; then
  pass "a change of one space, or the same edit in another place of the file, is another change by its id, and a change that came back to what was reviewed is the same change"
else
  fail "the id of a change: $reviewed / $moved / $back / $spaced"
fi

# The bar, through the real commands: a change that adds a suppression is refused at the checks until the
# plan gives the file's reason, and then the request is still not green. What lowers the bar, and which
# reason a file gets, are cases of tests/unit/test_land.py.
task_in "$LOCAL" bar-change calc.py one
read_in "$LOCAL" bar-change
tree=$(project --repo "$LOCAL" worktree-dir bar-change)
echo 'import os  # noqa: F401' > "$tree/calc.py" && echo 'test -f calc.py' > "$tree/tests/bar-change.sh" && echo 'puts 1 # rubocop:disable Style/X' > "$tree/x.rb"
git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: with a mark"
local_land start bar-change >/dev/null && local_land base bar-change >/dev/null && polish_in "$LOCAL" bar-change
refused=$(local_land checks bar-change 2>&1 || true)
# shellcheck disable=SC2016  # the backticks are the refusal's own marks around the plan's section
if grep -qF "calc.py (# noqa)" <<<"$refused" && grep -qF '`## The bar`' <<<"$refused" && [ "$(kept_in "$LOCAL" bar-change gated)" = None ] \
  && [ "$(status_of local_land read bar-change)" = 1 ]; then
  pass "a change that adds a suppression is refused at the checks, which name the file, its mark and the plan's section for the reason, and no review starts"
else
  fail "the bar: $refused"
fi
plan=$tree/docs/plans/2026-11-15-bar-change.md
# shellcheck disable=SC2016  # the backticks are the plan's own marks around a path
printf '%s\n' '' '## The bar' '' '- calc.py: the import registers a plugin.' >> "$plan"
git -C "$tree" commit -q -am "docs: why the bar is lower"
out=$(local_land checks bar-change)
small=$(local_land read bar-change | field 'd["floor"]')
unsaid=$(local_land read bar-change --record "$(clean bar-change 1)" 2>&1 || true)
local_land read bar-change --record "$(record bar-change 1 '{"kind": "read", "answered": ["codex"], "bar": [{"name": "calc.py", "why": "the plugin is loaded by that import."}]}')" >/dev/null
proposed=$(local_land propose bar-change --title "fix: marks" --notes "$NOTES")
agent=$(local_land merge bar-change --by merger 2>&1 || true)
text=$LOCAL/.lem/state/tasks/bar-change/pr.md
# shellcheck disable=SC2016
if [ "$(field '[(e["file"], e["reason"]) for e in d["bar"]["lowered"]]' <<<"$out")" = "[('calc.py', 'the import registers a plugin.')]" ] \
  && [ "$small" = read ] && grep -qF "the change lowers the bar in calc.py and the record says nothing of it" <<<"$unsaid" \
  && [ "$(field '(d["green"], len(d["not_green"]))' <<<"$proposed")" = "(False, 1)" ] && [ "$(sed -n 1p "$text")" = '**Not green.**' ] \
  && grep -q '^- the bar is lower in `calc.py` (# noqa)\. The builder: the import registers a plugin\. The review: the plugin is loaded by that import\.$' "$text" \
  && grep -q '^- the bar is lowered, with these reasons:$' "$text" && grep -q '^  - `calc.py` (# noqa): the import registers a plugin\.$' "$text" \
  && grep -q "^- the bar has no marks of its own for files of these kinds: .rb$" "$text" \
  && grep -q "the request is not green (the bar is lower in" <<<"$agent" \
  && [ "$(grep -c '"event": "proposed", "task": "bar-change", "green": false' "$LOCAL/.lem/state/events.jsonl")" = 1 ]; then
  pass "with a reason for each file in the plan the gate passes, and the request is still not green: the review says what it thinks of each reason, the text opens with each lowered bar, its reason and the review's word, the event log counts it, and no agent merges it"
else
  fail "the bar with reasons: $out / $unsaid / $proposed / $agent / $(cat "$text" 2>/dev/null)"
fi
# What makes a request large or careful, read from its plan: its own call stands under its title,
# where `stages/plan.md` puts it, never in a line the plan quotes further down, and a later commit
# that takes a yes back leaves the request careful, since the talk was due when the plan said it.
local_land start bar-change >/dev/null
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("1. The change.", "1. The change.\n2. Its test.\n3. Its page.\n4. Its note."))' "$plan"
git -C "$tree" commit -q -am "docs: four tasks" && local_land checks bar-change >/dev/null
large=$(local_land read bar-change | field '(d["floor"], d["why"])')
# shellcheck disable=SC2016  # the backticks are the plan's own fence
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read().replace("\n2. Its test.\n3. Its page.\n4. Its note.", "").replace("\n## Acceptance criteria", "careful: no, nothing here reaches a price.\n\n## Acceptance criteria", 1)
open(p, "w").write(s + "\n## Plan talk\n\nThe reviewer asked whether the plan should open with this line:\n\n```\ncareful: yes\n```\n")' "$plan"
git -C "$tree" commit -q -am "docs: one task, not careful, and a talk that quotes the line" && local_land checks bar-change >/dev/null
quoted=$(local_land read bar-change | field '(d["floor"], d["careful"])')
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("careful: no, nothing here reaches a price.", "careful: yes, a price is rounded here."))' "$plan"
git -C "$tree" commit -q -am "docs: careful" && local_land checks bar-change >/dev/null
said=$(local_land read bar-change | field '(d["floor"], d["why"])')
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("careful: yes, a price is rounded here.", "careful: no, the price is not rounded after all."))' "$plan"
git -C "$tree" commit -q -am "docs: not careful after all" && local_land checks bar-change >/dev/null
taken_back=$(local_land read bar-change | field '(d["floor"], d["why"])')
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("## Tasks\n\n1. The change.\n", ""))' "$plan"
git -C "$tree" commit -q -am "docs: no tasks" && local_land checks bar-change >/dev/null
err=$(local_land read bar-change 2>&1 || true)
if [ "$large" = "('round', 'the plan has 4 tasks, more than three')" ] && [ "$quoted" = "('read', [])" ] && [ "$said" = "('full', 'the request is careful: the plan says so')" ] \
  && [ "$taken_back" = "('full', 'the request is careful: the plan says so')" ] && grep -q "has no .## Tasks. section with numbered tasks" <<<"$err"; then
  pass "a plan of more than three tasks gets a round at the least; the plan's careful call is read under its title only, never from a line its plan talk quotes, a yes gets the full set, and a later commit that takes the yes back leaves it; a plan with no task list is refused, not taken for a small one"
else
  fail "large and careful: $large / $quoted / $said / $taken_back / $err"
fi
project --repo "$LOCAL" state bar-change dropped "the test is over" >/dev/null

# Careful by its review: the plan called the request plain, and the fresh agent that read the diff
# against the topics calls it careful. A record with no call is refused, and so is a careful call
# with less than the full set. No talk was due, the text says why it had none and why it is
# careful, the miss of the plan's call is one event for the retro, and no agent merges it.
task_in "$LOCAL" price-change seven.txt seven
read_in "$LOCAL" price-change
tree=$(project --repo "$LOCAL" worktree-dir price-change)
mkdir -p "$tree/billing" && echo 'PRICE = 7' > "$tree/billing/price.py" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: a price"
local_land start price-change >/dev/null && local_land base price-change >/dev/null && polish_in "$LOCAL" price-change && local_land checks price-change >/dev/null
printf '%s\n' '{"attempt": 1, "tip": "'"$(tip_of price-change)"'", "kind": "full", "ran": [{"name": "default", "why": "a price changes"}], "answered": ["codex"]}' > "$WORK/no-call.json"
nocall=$(local_land read price-change --record "$WORK/no-call.json" 2>&1 || true)
priced="billing/price.py:PRICE is what a customer pays, so a customer is charged the wrong price"
# the review's call, as JSON: the same record as a round and as the full set
called() { printf '{"kind": "%s", "ran": [{"name": "default", "why": "a price changes"}], "answered": ["codex"], "careful": true, "careful_why": "%s"}' "$1" "$priced"; }
less=$(local_land read price-change --record "$(record price-change 1 "$(called round)")" 2>&1 || true)
local_land read price-change --record "$(record price-change 1 "$(called full)")" >/dev/null
local_land propose price-change --title "fix: seven" --notes "$MIG" >/dev/null
text=$LOCAL/.lem/state/tasks/price-change/pr.md
first=$(grep -c '"event": "careful.missed", "task": "price-change"' "$LOCAL/.lem/state/events.jsonl" || true)
agent=$(local_land merge price-change --by merger 2>&1 || true)
local_land start price-change >/dev/null && local_land base price-change >/dev/null && local_land checks price-change >/dev/null && local_land propose price-change --title "fix: seven" --notes "$MIG" >/dev/null
if grep -qF "the record makes the careful call" <<<"$nocall" && grep -qF '"careful": true or false' <<<"$nocall" && grep -qF '"careful_why"' <<<"$nocall" \
  && grep -qF "a change the review calls careful gets the project's full set" <<<"$less" \
  && grep -q '^- no plan talk: the request became careful after its plan, by its review$' "$text" && grep -qxF -- "- careful: yes, the review says so: $priced" "$text" \
  && [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] && [ "$(sed -n 3p "$text")" = "**Careful**, so the owner merges it: the review says so: $priced." ] && [ "$first" = 1 ] \
  && [ "$(grep -c '"event": "careful.missed", "task": "price-change"' "$LOCAL/.lem/state/events.jsonl")" = 1 ] \
  && grep -qF "\"event\": \"careful.missed\", \"task\": \"price-change\", \"round\": 1, \"why\": \"$priced\"" "$LOCAL/.lem/state/events.jsonl" \
  && grep -qF "a careful request is merged by the owner, whatever the settings say (the review says so: $priced)" <<<"$agent" && [ "$(status_in "$LOCAL" price-change)" = open ]; then
  pass "a request the review calls careful and its plan did not gets the full set, its text says first that a person merges it and why, says in its checks that it had no plan talk and why, the plan's miss is one event with the review's reason, and no agent merges it; a record with no careful call is refused"
else
  fail "a request careful by its review: $nocall / $less / first $first / $agent / $(grep careful.missed "$LOCAL/.lem/state/events.jsonl") / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state price-change dropped "the test is over" >/dev/null

# The owner's careful on a task whose pull request is open (`stages/correct.md`): the line in its brief, then `start`
# takes it into the landing again, the review is due again with the full set over the one read it had, and propose
# writes the text again, careful, so the owner merges it.
task_in "$LOCAL" late-care late.txt late
read_in "$LOCAL" late-care
local_land start late-care >/dev/null && local_land base late-care >/dev/null && polish_in "$LOCAL" late-care && local_land checks late-care >/dev/null
local_land read late-care --record "$(clean late-care 1)" >/dev/null
local_land propose late-care --title "fix: late" --notes "$NOTES" >/dev/null
text=$LOCAL/.lem/state/tasks/late-care/pr.md
before=$(head -1 "$text" | cut -c1-10)
echo "careful: the owner says so" >> "$LOCAL/.lem/state/tasks/late-care/brief.md"
restarted=$(local_land start late-care | field 'd["task"]' 2>&1 || true)
local_land base late-care >/dev/null && polish_in "$LOCAL" late-care && local_land checks late-care >/dev/null
again=$(local_land read late-care | field '(d["due"], d["floor"], d["why"])' 2>&1 || true)
local_land read late-care --record "$(record late-care 2 '{"kind": "full", "ran": [{"name": "default", "why": "the owner says it is careful"}], "answered": ["codex"]}')" >/dev/null
local_land propose late-care --title "fix: late" --notes "$MIG" >/dev/null
if [ "$before" = '**Green.**' ] && [ "$restarted" = late-care ] \
  && [ "$again" = "('review', 'full', 'the request is careful: the owner says so')" ] \
  && grep -qxF '**Careful**, so the owner merges it: the owner says so.' "$text" && [ "$(status_in "$LOCAL" late-care)" = open ]; then
  pass "the owner's careful on a task whose pull request is open: start takes it into the landing again, the review is due again with the full set, and propose writes the text again, careful, so the owner merges it"
else
  fail "careful on an open task: $before / $restarted / $again / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state late-care dropped "the test is over" >/dev/null

# An agent merges a green request only on the newest review's "not careful": a record that holds no
# call, as a review written down before the call was asked holds none, leaves the merge to a person.
task_in "$LOCAL" call-kept eight.txt eight
read_in "$LOCAL" call-kept
local_land start call-kept >/dev/null && local_land base call-kept >/dev/null && polish_in "$LOCAL" call-kept && local_land checks call-kept >/dev/null && local_land read call-kept --record "$(clean call-kept 1)" >/dev/null
local_land propose call-kept --title "fix: eight" --notes "$NOTES" >/dev/null
text=$LOCAL/.lem/state/tasks/call-kept/pr.md
kept_file=$LOCAL/.lem/state/tasks/call-kept/landing.json
cp "$kept_file" "$WORK/call-kept.json"
"$PY" -c 'import json, sys; p = sys.argv[1]; d = json.load(open(p))
for read in d["reads"]:
    read.pop("careful"); read.pop("careful_why")
json.dump(d, open(p, "w"))' "$kept_file"
uncalled=$(local_land merge call-kept --by merger 2>&1 || true)
cp "$WORK/call-kept.json" "$kept_file"
merge_read "$LOCAL" call-kept >/dev/null
merged=$(local_land merge call-kept --by merger 2>&1 || true)
if grep -qxF -- "- careful: no; the review says no: $NOT_CAREFUL" "$text" && [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] && ! grep -q '^\*\*Careful\*\*' "$text" \
  && grep -qF "no review that answered made the careful call for this change, so the owner merges it" <<<"$uncalled" \
  && [ "$(status_in "$LOCAL" call-kept)" = landed ] && [ "$(git -C "$LOCAL" show main:eight.txt)" = eight ]; then
  pass "the merge agent merges a green request whose newest review says not careful, and its text says the review's call with its reason; a newest review with no call leaves the merge to the owner"
else
  fail "the agent's merge and the review's call: $uncalled / $merged / $(cat "$text" 2>/dev/null)"
fi
local_land clean call-kept >/dev/null

# A task that ran without the owner: green when nothing of his was decided without him, with the line that says when it
# ran so, and a decision the gate or the personas settled stays green, its line with the votes and the model families. The
# merge agent merges it as any other. Here the owner says that he is away.
ldecide() { "$PY" -B "$DECISIONS" --repo "$LOCAL" "$@"; }
task_in "$LOCAL" quiet-run quiet.txt quiet
read_in "$LOCAL" quiet-run
ldecide log quiet-run --what "The file's name" --chose quiet.txt --by gate --why "docs/rulings.md, Names: A file is named for what it holds." >/dev/null
ldecide log quiet-run --what "The word's case" --chose "lower case" --by personas --vote "the merchant, opus=lower case" --vote "the merchant, sol=lower case" --vote "the clerk, opus=lower case" \
  --why "the importer reads lower case" >/dev/null
project --repo "$LOCAL" owner away --words "I'm away" >/dev/null
local_land start quiet-run >/dev/null && local_land base quiet-run >/dev/null && polish_in "$LOCAL" quiet-run && local_land checks quiet-run >/dev/null && local_land read quiet-run --record "$(clean quiet-run 1)" >/dev/null
local_land propose quiet-run --title "fix: quiet" --notes "$NOTES" >/dev/null
text=$LOCAL/.lem/state/tasks/quiet-run/pr.md
read_alone=$(merge_read "$LOCAL" quiet-run 2>&1 || true)
merged=$(local_land merge quiet-run --by merger 2>&1 || true)
project --repo "$LOCAL" owner back --words "/lem im-back" >/dev/null
if [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] && grep -qE '^It ran without the owner from 20[0-9-]+ [0-9:]+ UTC \(the owner: "I'"'"'m away"\)\.$' "$text" \
  && grep -qxF -- '- The word'"'"'s case: "lower case", by the personas: 3 votes of 2 personas, two model families, all for it. the importer reads lower case' "$text" \
  && grep -qxF -- '- The file'"'"'s name: "quiet.txt", by the gate. docs/rulings.md, Names: A file is named for what it holds.' "$text" \
  && [ "$(field '(d["verdict"], d["calls"])' <<<"$read_alone")" = "('merge', False)" ] && [ "$(field 'd["pull_request"]["url"].startswith("https://github.com/acme/local/pull/")' <<<"$merged")" = True ] \
  && [ "$(status_in "$LOCAL" quiet-run)" = landed ]; then
  pass "a task that ran without the owner with nothing of his decided without him is green, and says when it ran so and on whose words; the gate's and the personas' decisions stay green, with the cite and the count of votes and families; the merge agent reads it and merges it while he is away, as any other"
else
  fail "a green task that ran without the owner: $read_alone / $merged / $(cat "$text" 2>/dev/null)"
fi
local_land clean quiet-run >/dev/null
# Not green when something of his was decided without him: criteria approved without him, and a decision past the
# personas or that no level settled, taken at once whether he is there or away; each is a line of its own.
task_in "$LOCAL" loud-run loud.txt loud
read_in "$LOCAL" loud-run
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the ticket names the word and the file.' '' '1. The file holds the word the owner asked for.' > "$WORK/loud.md"
ldecide log loud-run "${CASE[@]}" --what "Where the word goes" --chose "the last line" --by experts --why "both experts picked it" --level "personas=1 to 1" --level "dialectic=one break" >/dev/null
ldecide log loud-run "${CASE[@]}" --what "The word's font" --chose plain --by lead --unsettled --why "the export has no fonts" >/dev/null
ldecide log loud-run "${CASE[@]}" --what "The line ending" --option "a line break" --option "none" --chose "a line break" --by dialectic --why "every file ends so" --level "personas=split" >/dev/null
project --repo "$LOCAL" owner away --words "I'm away" >/dev/null
lcriteria approve loud-run --file "$WORK/loud.md" --alone >/dev/null
ldir=$LOCAL/.lem/state/tasks/loud-run
printf '%s\n' '# The loud word' '' '## Outcome' '' 'The importer finds the word on its own line.' '' '## Out of scope' '' '- the quiet word' > "$ldir/task.md"
printf '%s\n' '## What the owner gets' '' 'loud.txt holds the word.' '' '```sh' '# see it' 'cat loud.txt' '```' '' '## Not verified' '' 'nothing' > "$ldir/report.md"
echo '- "keep the word in lower case"' > "$ldir/directions.md"
local_land start loud-run >/dev/null && local_land base loud-run >/dev/null && polish_in "$LOCAL" loud-run && local_land checks loud-run >/dev/null && local_land read loud-run --record "$(clean loud-run 1)" >/dev/null
local_land propose loud-run --title "fix: loud" --notes "$NOTES" >/dev/null
project --repo "$LOCAL" owner back --words "/lem im-back" >/dev/null
text=$LOCAL/.lem/state/tasks/loud-run/pr.md
day=$(date -u +%Y-%m-%d)
if [ "$(sed -n 1p "$text")" = '**Not green.**' ] \
  && [ "$(sed -n 3p "$text")" = "- the owner did not approve the criteria: they were approved on $day while the task ran without the owner" ] \
  && [ "$(sed -n 4p "$text")" = '- decision 1 was taken without the owner (Where the word goes): "the last line", by the experts' ] \
  && [ "$(sed -n 5p "$text")" = "- decision 2 was taken without the owner (The word's font): \"plain\", the lead's pick, which no level of the ladder settled" ] \
  && [ "$(sed -n 6p "$text")" = '- decision 3 was taken without the owner (The line ending): "a line break", by the dialectic' ] \
  && grep -qE '^It ran without the owner from ' "$text" && grep -qF 'Each level: personas: 1 to 1; dialectic: one break.' "$text" \
  && grep -qF "approved on $day while the task ran without the owner" <<<"$(grep '^- the criteria were read' "$text")"; then
  pass "a task that ran without the owner is not green for each thing of his decided without him, one line each: criteria approved without him, a decision of the experts or of the dialectic, and one no level settled"
else
  fail "a task that ran without the owner, not green: $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state loud-run dropped "the test is over" >/dev/null

# A branch cannot lift what guards it: one that edits the flow table of its own .lem/project.toml is
# careful by the script, which says why, and the landing reads the topics of the main checkout's
# settings, also when it runs from the task's worktree.
task_in "$LOCAL" lift-topics nine.txt nine
read_in "$LOCAL" lift-topics
tree=$(project --repo "$LOCAL" worktree-dir lift-topics)
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("topics = [\"a customer is charged the wrong price\"]", "topics = []"))' "$tree/.lem/project.toml"
git -C "$tree" commit -q -am "chore: no topics"
local_land start lift-topics >/dev/null && local_land base lift-topics >/dev/null && polish_in "$LOCAL" lift-topics && local_land checks lift-topics >/dev/null
lifted=$(local_land read lift-topics | field '(d["floor"], d["why"], d["inputs"]["topics"])')
from_tree=$(land --repo "$tree" read lift-topics | field '(d["floor"], d["inputs"]["topics"])')
local_land read lift-topics --record "$(record lift-topics 1 '{"kind": "full", "ran": [{"name": "default", "why": "the settings change"}], "answered": ["codex"]}')" >/dev/null
local_land propose lift-topics --title "chore: no topics" --notes "$MIG" >/dev/null
agent=$(local_land merge lift-topics --by merger 2>&1 || true)
text=$LOCAL/.lem/state/tasks/lift-topics/pr.md
settings_why="the change edits [flow] of .lem/project.toml, Lem's own settings, which say for every later task what is careful, what the checks run, who merges and where a task lands"
# the reason holds an apostrophe, so Python's repr of it is in double quotes
if [ "$lifted" = "('full', \"the request is careful: $settings_why\", ['a customer is charged the wrong price'])" ] \
  && [ "$from_tree" = "('full', ['a customer is charged the wrong price'])" ] \
  && grep -qxF -- "- careful: yes, $settings_why; the review says no: $NOT_CAREFUL" "$text" \
  && grep -qF "a careful request is merged by the owner, whatever the settings say ($settings_why)" <<<"$agent" && [ "$(status_in "$LOCAL" lift-topics)" = open ]; then
  pass "a branch that edits the flow table of its own settings is careful by the script, which says why, gets the full set and a person's merge, and the landing reads the main checkout's topics, also when it runs from the task's worktree"
else
  fail "a branch that lifts its own topics: $lifted / $from_tree / $agent / $(cat "$text" 2>/dev/null)"
fi
project --repo "$LOCAL" state lift-topics dropped "the test is over" >/dev/null

# Every edit of Lem's own settings is careful by the script, not only one of [flow] or [checks]: a branch that
# changes how its tasks land, and one that changes no value and only the file's text, each get the full set,
# with the tables named, and a person's merge.
task_in "$LOCAL" lands-alone ten.txt ten
read_in "$LOCAL" lands-alone
tree=$(project --repo "$LOCAL" worktree-dir lands-alone)
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("history = \"keep\"", "history = \"squash\""))' "$tree/.lem/project.toml"
git -C "$tree" commit -q -am "chore: one commit for each task"
local_land start lands-alone >/dev/null && local_land base lands-alone >/dev/null && polish_in "$LOCAL" lands-alone && local_land checks lands-alone >/dev/null
branch_floor=$(local_land read lands-alone | field '(d["floor"], d["why"])')
local_land read lands-alone --record "$(record lands-alone 1 '{"kind": "full", "ran": [{"name": "default", "why": "the settings change"}], "answered": ["codex"]}')" >/dev/null
local_land propose lands-alone --title "chore: squash" --notes "$MIG" >/dev/null
branch_agent=$(local_land merge lands-alone --by merger 2>&1 || true)
project --repo "$LOCAL" state lands-alone dropped "the test is over" >/dev/null
task_in "$LOCAL" settings-note eleven.txt eleven
tree=$(project --repo "$LOCAL" worktree-dir settings-note)
printf '%s\n' '# the owner keeps the topics short' >> "$tree/.lem/project.toml"
git -C "$tree" commit -q -am "docs: a note in the settings"
local_land start settings-note >/dev/null && local_land base settings-note >/dev/null && polish_in "$LOCAL" settings-note && local_land checks settings-note >/dev/null
note_floor=$(local_land read settings-note | field '(d["floor"], d["why"])')
project --repo "$LOCAL" state settings-note dropped "the test is over" >/dev/null
branch_why="the change edits [branch] of .lem/project.toml, Lem's own settings, which say for every later task what is careful, what the checks run, who merges and where a task lands"
note_why="the change edits the text of .lem/project.toml, and no value in it, Lem's own settings, which say for every later task what is careful, what the checks run, who merges and where a task lands"
if [ "$branch_floor" = "('full', \"the request is careful: $branch_why\")" ] && grep -qF "a careful request is merged by the owner, whatever the settings say ($branch_why)" <<<"$branch_agent" \
  && grep -qxF -- "- careful: yes, $branch_why; the review says no: $NOT_CAREFUL" "$LOCAL/.lem/state/tasks/lands-alone/pr.md" \
  && [ "$note_floor" = "('full', \"the request is careful: $note_why\")" ]; then
  pass "every edit of Lem's own settings is careful by the script: one of [branch] gets the full set, a line of the pull request with the table named and a person's merge, and one of the file's text alone is careful too"
else
  fail "an edit of the settings beyond flow and gate: $branch_floor / $branch_agent / $note_floor / $(grep careful "$LOCAL/.lem/state/tasks/lands-alone/pr.md" 2>/dev/null)"
fi

# A branch that removes Lem's own settings is careful, and the reason says it removes the file, not which tables it edits.
task_in "$LOCAL" settings-gone twelve.txt twelve
tree=$(project --repo "$LOCAL" worktree-dir settings-gone)
git -C "$tree" rm -q .lem/project.toml && git -C "$tree" commit -q -m "chore: no settings"
local_land start settings-gone >/dev/null && local_land base settings-gone >/dev/null && polish_in "$LOCAL" settings-gone && local_land checks settings-gone >/dev/null
gone_floor=$(local_land read settings-gone | field '(d["floor"], d["why"])')
project --repo "$LOCAL" state settings-gone dropped "the test is over" >/dev/null
gone_why="the change removes .lem/project.toml, Lem's own settings, which say for every later task what is careful, what the checks run, who merges and where a task lands"
if [ "$gone_floor" = "('full', \"the request is careful: $gone_why\")" ]; then
  pass "a branch that removes Lem's own settings is careful by the script, and the reason says that it removes the file"
else
  fail "a branch that removes the settings: $gone_floor"
fi

# The machine's own settings are untracked by design: a branch that commits .lem/project.local.toml, or changes or
# removes a tracked one, is careful by the script, with a reason that says the file is one machine's own.
task_in "$LOCAL" local-tracked thirteen.txt thirteen
read_in "$LOCAL" local-tracked
tree=$(project --repo "$LOCAL" worktree-dir local-tracked)
printf '%s\n' '[seats]' 'reviewer = "claude/opus:high"' > "$tree/.lem/project.local.toml"
git -C "$tree" add -f .lem/project.local.toml && git -C "$tree" commit -q -m "chore: my asker"
local_land start local-tracked >/dev/null && local_land base local-tracked >/dev/null && polish_in "$LOCAL" local-tracked && local_land checks local-tracked >/dev/null
local_floor=$(local_land read local-tracked | field '(d["floor"], d["why"])')
local_land read local-tracked --record "$(record local-tracked 1 '{"kind": "full", "ran": [{"name": "default", "why": "the settings change"}], "answered": ["codex"]}')" >/dev/null
local_land propose local-tracked --title "chore: my asker" --notes "$MIG" >/dev/null
local_agent=$(local_land merge local-tracked --by merger 2>&1 || true)
project --repo "$LOCAL" state local-tracked dropped "the test is over" >/dev/null
local_why="the change adds .lem/project.local.toml, one machine's own settings, which git does not track: tracked, that machine's seats, corrections and naps become every machine's"
if [ "$local_floor" = "('full', \"the request is careful: $local_why\")" ] && grep -qF "a careful request is merged by the owner, whatever the settings say ($local_why)" <<<"$local_agent" \
  && grep -qxF -- "- careful: yes, $local_why; the review says no: $NOT_CAREFUL" "$LOCAL/.lem/state/tasks/local-tracked/pr.md"; then
  pass "a branch that commits the machine's own settings file is careful by the script: the full set, a line of the pull request that says the file is one machine's own, and a person's merge"
else
  fail "a branch that tracks the machine's own settings: $local_floor / $local_agent / $(grep careful "$LOCAL/.lem/state/tasks/local-tracked/pr.md" 2>/dev/null)"
fi

finish
