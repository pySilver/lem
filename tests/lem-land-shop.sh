#!/usr/bin/env bash
# The landing: land.py takes one task from `ready` through the machine checks and one read to a pull
# request, or to a branch that is ready to land, and from there to the base branch. This block has
# a remote and no forge; lem-land-local.sh has no remote, lem-land-backlog.sh files what a review
# saw outside the change, and lem-land-github.sh has a forge.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

ORIGIN=$WORK/origin.git
SHOP=$WORK/shop
git init -q --bare -b main "$ORIGIN"
git clone -q "$ORIGIN" "$SHOP" 2>/dev/null
ident "$SHOP"
project --repo "$SHOP" init --base main --reviewer codex >/dev/null
shop_settings() {
  printf '%s\n' '[branch]' 'base = "main"' "land = \"$1\"" "history = \"$2\"" 'protected = ["release"]' \
    '[gate]' 'commands = ["test -f ok.txt", "echo 7 passed"]' 'ignores = ["docs/*"]' > "$SHOP/.lem/project.toml"
}
shop_settings owner keep
mkdir -p "$SHOP/docs" "$SHOP/.lem/styleguide" && echo guide > "$SHOP/docs/guide.md" && echo one > "$SHOP/app.txt"
printf '%s\n' '---' 'paths:' '  - "tests/**"' '---' 'A test names what it checks.' > "$SHOP/.lem/styleguide/tests.md"
printf '%s\n' '---' 'paths:' '  - "billing/**"' '---' 'Money is an integer.' > "$SHOP/.lem/styleguide/money.md"
git -C "$SHOP" add -A && git -C "$SHOP" commit -q -m "chore: start" && git -C "$SHOP" push -q origin main
open_task() { task_in "$SHOP" "$@"; }
status() { status_in "$SHOP" "$1"; }
kept() { kept_in "$SHOP" "$@"; }
# the three machine steps, a read that found nothing, and the proposal, for the tests that are about a later step
checked() { land --repo "$SHOP" start "$1" >/dev/null && land --repo "$SHOP" base "$1" >/dev/null && land --repo "$SHOP" gate "$1" >/dev/null; }
read_clean() { land --repo "$SHOP" read "$1" --record "$(clean "${2:-1}")" >/dev/null; }
propose() { land --repo "$SHOP" propose "$1" --title "fix: $1" --notes "$NOTES" >/dev/null; }

open_task first-change ok.txt yes
open_task second-change app.txt two
if [ "$(status_of land --repo "$SHOP" gate first-change)" = 1 ] && [ "$(status_of land --repo "$SHOP" base first-change)" = 1 ] \
  && [ "$(status_of land --repo "$SHOP" read first-change)" = 1 ] && [ "$(status_of land --repo "$SHOP" propose first-change --title x --notes "$NOTES")" = 1 ] \
  && [ "$(status_of land --repo "$SHOP" land first-change --by owner)" = 1 ] && [ "$(status first-change)" = ready ]; then
  pass "no step runs on a task that did not take the landing line, and the owner's word lands nothing that was not proposed"
else
  fail "land steps before start"
fi
out=$(land --repo "$SHOP" start first-change)
err=$(land --repo "$SHOP" start second-change 2>&1 || true)
if [ "$(field '(d["remote"], d["forge"])' <<<"$out")" = "(True, None)" ] && [ "$(status first-change)" = landing ] && [ "$(status_of land --repo "$SHOP" start second-change)" = 1 ] \
  && grep -q "first-change is in .landing." <<<"$err" && [ "$(status second-change)" = ready ]; then
  pass "start puts one task in landing, and a second task is refused while it is there"
else
  fail "land start: $out / $err"
fi
if [ "$(status_of land --repo "$SHOP" gate first-change)" = 1 ]; then pass "the gate refuses to run before the base was brought in"; else fail "gate before base"; fi
out=$(land --repo "$SHOP" base first-change)
if [ "$(field '(d["ahead"], d["moved"], d["onto"])' <<<"$out")" = "(1, False, 'origin/main')" ]; then
  pass "base rebases onto the remote's base branch and says how many commits the branch adds"
else
  fail "land base: $out"
fi
out=$(land --repo "$SHOP" gate first-change)
tip=$(git -C "$SHOP/.lem/worktrees/first-change" rev-parse HEAD)
if [ "$(field '(d["green"], [c["exit"] for c in d["commands"]], d["commands"][1]["last"])' <<<"$out")" = "(True, [0, 0], '7 passed')" ] \
  && [ "$(kept first-change gated)" = "$tip" ] && [ "$(cat "$SHOP/.git/lem/tasks/first-change/gate/02.log")" = "7 passed" ] \
  && [ "$(grep -c '"event": "gate", "task": "first-change"' "$SHOP/.git/lem/events.jsonl")" = 2 ]; then
  pass "gate runs every command with its output in a file, keeps the last line, logs each result and records the green tip"
else
  fail "land gate: $out"
fi
if [ "$(field '(d["stories"]["ok"], [(t["story"], t["problem"]) for t in d["stories"]["tests"]], d["bar"], d["size"]["files"], d["size"]["in_parts"])' <<<"$out")" \
  = "(True, [(1, None)], {'lowered': [], 'not_covered': [], 'own_patterns': 0}, 3, False)" ] && grep -q '"event": "task.red", "task": "first-change"' "$SHOP/.git/lem/events.jsonl"; then
  pass "after the commands the gate proves each story's test on the branch and on the base commit, looks for a lowered bar and counts the size"
else
  fail "the machine checks after the gate's commands: $out"
fi
# A review before anything is proposed: the script says the least it may be, and what a reviewer gets.
err=$(land --repo "$SHOP" propose first-change --title "fix: the file is there" --notes "$NOTES" 2>&1 || true)
out=$(land --repo "$SHOP" read first-change)
base=$(git -C "$SHOP" rev-parse origin/main)
if grep -q "a review is due before anything is proposed, one read at the least" <<<"$err" && [ "$(status first-change)" = landing ] \
  && [ "$(field '(d["due"], d["floor"], d["round"], d["in_parts"], sorted(d["inputs"]), d["inputs"]["range"], [r.split("/.lem/")[-1] for r in d["inputs"]["rules"]])' <<<"$out")" \
  = "('review', 'read', 1, False, ['bar', 'plan', 'range', 'review', 'rules', 'topics', 'words', 'worktree'], '$base..$tip', ['styleguide/tests.md'])" ] \
  && [ "$(cat "$(field 'd["inputs"]["words"]' <<<"$out")")" = "Put yes into ok.txt." ] && [ -f "$(field 'd["inputs"]["plan"]' <<<"$out")" ] \
  && [ "$(field 'd["inputs"]["review"]' <<<"$out")" = "$SHOP/.revmux" ]; then
  pass "nothing is proposed before its review; for a usual request the floor is one read, and a reviewer gets the owner's words, the plan, the range, the rule files of the changed files, the project's topics and the folder of the review tool"
else
  fail "the read that is due: $err / $out"
fi
err=$(land --repo "$SHOP" read first-change --record "$(record 1 '{"kind": "read", "answered": [], "must_fix": 1}')" 2>&1 || true)
shape=$(land --repo "$SHOP" read first-change --record "$(record 1 '{"kind": "glance", "answered": ["codex"]}')" 2>&1 || true)
late=$(land --repo "$SHOP" read first-change --record "$(clean 2)" 2>&1 || true)
out=$(land --repo "$SHOP" read first-change --record "$(record 1 '{"kind": "read", "answered": ["codex"], "should": 1}')")
if grep -q "findings and no source that answered" <<<"$err" && grep -q ".kind. is one of read, round, full" <<<"$shape" \
  && grep -q "the record says attempt 2, and the next review of this task is attempt 1" <<<"$late" \
  && [ "$(field '(d["recorded"]["round"], d["recorded"]["kind"], d["recorded"]["verdict"], d["recorded"]["should"], d["next"])' <<<"$out")" = "(1, 'read', 'clean', 1, 'none')" ] \
  && [ "$(grep -c '"event": "review", "task": "first-change"' "$SHOP/.git/lem/events.jsonl")" = 1 ] && [ "$(status_of land --repo "$SHOP" read first-change --record "$(clean 2)")" = 1 ]; then
  pass "a review is written down from a file, with its round, its kind, who answered and its counts; a record that does not have the form or the number of this review is refused, and a change that was reviewed clean is not reviewed again"
else
  fail "recording a read: $err / $out"
fi
printf '%s\n' '## Decisions' '' 'none' > "$WORK/thin.md"
err=$(land --repo "$SHOP" propose first-change --title "fix: the file is there" --notes "$WORK/thin.md" 2>&1 || true)
out=$(land --repo "$SHOP" propose first-change --title "fix: the file is there" --notes "$NOTES")
text=$SHOP/.git/lem/tasks/first-change/pr.md
if grep -q "the notes lack ## Left open, ## Worth a look, ## Filed in the backlog, ## Not done" <<<"$err" && [ "$(field '(d["pull_request"], d["green"], d["not_green"], d["branch"])' <<<"$out")" = "(None, True, [], 'fix/first-change')" ] \
  && [ "$(status first-change)" = open ] && [ "$(kept first-change proposed)" = "$tip" ] && [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] && grep -q '^green$' "$SHOP/.git/lem/tasks/first-change/state.md" \
  && [ "$(grep '^## ' "$text" | tr '\n' '|')" = "## The request|## Stories|## Checks|## Decisions of the build|## Decisions|## Left open|## Worth a look|## Filed in the backlog|## Not done|" ] \
  && [ "$(sed -n '/^## Decisions of the build$/,/^## Decisions$/p' "$text" | sed -n 3p)" = none ] && head -1 "$text" | grep -qF 'no story changed, and no decision was taken by timeout or by the experts.' \
  && grep -q '^> Put yes into ok.txt\.$' "$text" && grep -q '^1\. The file holds the word the owner asked for\.$' "$text" \
  && grep -q 'sh tests/first-change.sh.: passes on the branch, fails on the base commit' "$text" && grep -q '^- gate, .echo 7 passed.: 7 passed$' "$text" \
  && grep -q "^- the stories' tests: 1 pass on the branch and fail on the base commit$" "$text" && grep -q '^- the bar: not lowered$' "$text" \
  && grep -q '^- the review, round 1 (one read; answered: codex): clean, 0 must-fix, 1 should, 0 nit$' "$text" && grep -qxF -- "- careful: no; the review says no: $NOT_CAREFUL" "$text" && grep -q '^- the one line of the file\.$' "$text" \
  && ! grep -q 'plan talk' "$text" && ! grep -q '"event": "plan.talk", "task": "first-change"' "$SHOP/.git/lem/events.jsonl"; then
  pass "with no forge the branch is marked ready: the task is open, and the text for the owner says green first, then holds his words, the stories with their tests, each check with what it returned, the decisions of the record (none here), then the notes; a plain request of one task needs no plan talk, and its text has no line of one"
else
  fail "propose: $err / $out / $(cat "$text" 2>/dev/null)"
fi
err=$(land --repo "$SHOP" land first-change --by agent 2>&1 || true)
if [ "$(status_of land --repo "$SHOP" land first-change --by agent)" = 1 ] && grep -q "a person merges" <<<"$err" \
  && [ "$(git -C "$ORIGIN" rev-parse main)" = "$(git -C "$SHOP" rev-parse main)" ] && [ "$(status first-change)" = open ]; then
  pass "an agent lands nothing when the settings say that a person merges"
else
  fail "land with branch.land = owner: $err"
fi
shop_settings agent keep
if [ "$(status_of land --repo "$SHOP" land first-change --by agent --message "fix: x")" = 1 ]; then
  pass "a commit subject is refused when the branch's own commits land"
else
  fail "land --message with history = keep"
fi
# The base moves after the gate ran: by a file the gate reads, then only by one it does not.
other=$WORK/other
git clone -q "$ORIGIN" "$other" && ident "$other"
echo late > "$other/late.txt" && git -C "$other" add -A && git -C "$other" commit -q -m "feat: late" && git -C "$other" push -q origin main
err=$(land --repo "$SHOP" land first-change --by agent 2>&1 || true)
if [ "$(status_of land --repo "$SHOP" land first-change --by agent)" = 1 ] && grep -q "moved after the gate ran, by files the gate reads (late.txt)" <<<"$err" \
  && grep -q "run .land.py start., .land.py base., .land.py gate. and .land.py propose. again" <<<"$err" && [ "$(status first-change)" = open ]; then
  pass "land refuses when the base moved by a file the gate reads, and says which steps run again"
else
  fail "land after the base moved: $err"
fi
land --repo "$SHOP" start first-change >/dev/null && land --repo "$SHOP" base first-change >/dev/null
if [ "$(status first-change)" = landing ] && [ "$(kept first-change gated)" = None ] && [ "$(status_of land --repo "$SHOP" land first-change --by agent)" = 1 ] \
  && [ "$(status_of land --repo "$SHOP" propose first-change --title x --notes "$NOTES")" = 1 ]; then
  pass "an open task takes the landing line again, and a new base forgets the gate's result, so nothing is proposed or landed before a new one"
else
  fail "base after a green gate keeps the result"
fi
land --repo "$SHOP" gate first-change >/dev/null
out=$(land --repo "$SHOP" read first-change)
if [ "$(field '(d["due"], d["why"])' <<<"$out")" = "('none', 'round 1 reviewed this change and left no must-fix')" ] && propose first-change && [ "$(status first-change)" = open ]; then
  pass "a rebase that changes nothing of the change does not undo its review"
else
  fail "the read after a rebase: $out"
fi
echo more >> "$other/docs/guide.md" && git -C "$other" add -A && git -C "$other" commit -q -m "docs: more" && git -C "$other" push -q origin main
out=$(land --repo "$SHOP" land first-change --by agent)
if [ "$(field '(d["pushed"], d["arrived"], d["left_behind"])' <<<"$out")" = "(True, ['docs/guide.md'], None)" ] && [ "$(status first-change)" = landed ] \
  && [ "$(git -C "$ORIGIN" log -1 --format=%s main)" = "fix: first-change" ] && [ "$(git -C "$SHOP" rev-parse main)" = "$(git -C "$ORIGIN" rev-parse main)" ] \
  && [ -f "$SHOP/ok.txt" ] && [ -f "$SHOP/late.txt" ]; then
  pass "where the settings allow it an agent lands a request that is green and not careful; a base that moved only by files the gate ignores still lands: pushed, the main checkout fast-forwarded, the state landed"
else
  fail "land: $out"
fi
# A clean that was cut off after the worktree went: the next run still knows the branch.
git -C "$SHOP" worktree remove "$SHOP/.lem/worktrees/first-change"
out=$(land --repo "$SHOP" clean first-change)
if [ "$(field '(d["worktree"], d["branch"])' <<<"$out")" = "(False, 'fix/first-change')" ] && [ -z "$(git -C "$SHOP" branch --list fix/first-change)" ] \
  && [ -d "$SHOP/.git/lem/tasks/first-change" ] && [ "$(field '(d["worktree"], d["branch"])' <<<"$(land --repo "$SHOP" clean first-change)")" = "(False, None)" ]; then
  pass "clean removes the landed task's branch when its worktree is already gone, keeps the task's state, and a third run finds nothing left"
else
  fail "land clean after the worktree went: $out"
fi
if [ "$(status_of land --repo "$SHOP" clean second-change)" = 1 ] && [ -d "$SHOP/.lem/worktrees/second-change" ]; then
  pass "clean refuses a task that has not landed"
else
  fail "clean before the landing"
fi
# An answered task loses its worktree as a dropped one does, and its branch stays: it may hold the test that reproduced the bug.
AC=$WORK/answered-clean
git init -q -b main "$AC" && git -C "$AC" config user.name t && git -C "$AC" config user.email t@t
project --repo "$AC" init --base main --reviewer codex >/dev/null
git -C "$AC" add -A && git -C "$AC" commit -q -m "chore: start"
acd=$(project --repo "$AC" task-dir refund-shows-zero --ask "invoices show 0 after a refund")
act=$(project --repo "$AC" worktree-dir refund-shows-zero)
git -C "$AC" worktree add -q -b fix/refund-shows-zero "$act" main
# shellcheck disable=SC2016 # the test file's own text, with its quotes
mkdir -p "$act/tests" && echo 'test "$(cat total)" = 0' > "$act/tests/refund.sh"
git -C "$act" add -A && git -C "$act" commit -q -m "test: an invoice after a refund shows what is left to pay"
project --repo "$AC" state refund-shows-zero building "a builder reproduces the bug and finds its cause" "investigation: bug" "kind: bug, because the ask says the total is wrong today" >/dev/null
printf '%s\n' '# Investigation' '' 'Reproduced: yes.' > "$acd/investigation.md"
project --repo "$AC" log refund-shows-zero investigation kind=bug call=not-a-bug "line=the invoice shows what is left to pay" where=billing/invoice.py:total reproduced:=true >/dev/null
project --repo "$AC" state refund-shows-zero answered "not a bug: the invoice shows what is left to pay" >/dev/null
out=$(land --repo "$AC" clean refund-shows-zero 2>&1 || true)
if [ "$(field '(d["worktree"], d["branch"])' <<<"$out" 2>&1 || true)" = "(True, None)" ] && [ ! -e "$act" ] \
  && grep -qF "fix/refund-shows-zero holds the answered task's commits, the test that reproduced its bug among them when it has one" <<<"$out" \
  && git -C "$AC" rev-parse -q --verify fix/refund-shows-zero >/dev/null && [ -f "$acd/investigation.md" ]; then
  pass "clean removes an answered task's worktree and leaves its branch, which may hold the test that reproduced the bug, with how to delete it; the report stays"
else
  fail "land clean of an answered task: $out"
fi

# A conflict with the base is reported and undone, never resolved here.
git -C "$other" pull -q origin main
echo other > "$other/app.txt" && git -C "$other" add -A && git -C "$other" commit -q -m "feat: other" && git -C "$other" push -q origin main
# The owner said that this task is careful: that word is in its brief, and it decides the read and who merges.
task_dir=$(project --repo "$SHOP" task-dir second-change)
printf '%s\n' 'slug: second-change' 'lead: session' 'careful: the owner says so' > "$task_dir/brief.md"
land --repo "$SHOP" start second-change >/dev/null
out=$(land --repo "$SHOP" base second-change 2>/dev/null || true)
if [ "$(status_of land --repo "$SHOP" base second-change)" = 1 ] && [ "$(field '(d["conflict"], d["branch"])' <<<"$out")" = "(['app.txt'], 'fix/second-change')" ] \
  && [ -z "$(git -C "$SHOP/.lem/worktrees/second-change" status --porcelain)" ] && [ ! -d "$SHOP/.git/worktrees/second-change/rebase-merge" ]; then
  pass "a conflict with the base names its files and leaves the worktree as it was"
else
  fail "land base with a conflict: $out"
fi
# The builder resolves it; here the test does. Then a red gate, then a round that finds a must-fix, then one commit for the whole branch.
tree=$SHOP/.lem/worktrees/second-change
git -C "$tree" rebase -q origin/main >/dev/null 2>&1 || true
echo both > "$tree/app.txt" && echo 'grep -qx both app.txt' > "$tree/tests/second-change.sh" && git -C "$tree" add -A && GIT_EDITOR=true git -C "$tree" rebase --continue >/dev/null 2>&1
git -C "$tree" rm -q ok.txt && git -C "$tree" commit -q -m "fix: lose the file the gate wants"
land --repo "$SHOP" base second-change >/dev/null
out=$(land --repo "$SHOP" gate second-change 2>/dev/null || true)
if [ "$(status_of land --repo "$SHOP" gate second-change)" = 1 ] && [ "$(field '(d["green"], [c["exit"] for c in d["commands"]], "stories" in d)' <<<"$out")" = "(False, [1, 0], False)" ] \
  && [ "$(kept second-change gated)" = None ] && [ "$(status_of land --repo "$SHOP" read second-change)" = 1 ] && [ "$(status_of land --repo "$SHOP" propose second-change --title x --notes "$NOTES")" = 1 ]; then
  pass "a red gate exits 1 with each command's result, the later checks do not run, and nothing is read or proposed on it"
else
  fail "red gate: $out"
fi
git -C "$tree" revert --no-edit HEAD >/dev/null
shop_settings agent squash
land --repo "$SHOP" gate second-change >/dev/null
out=$(land --repo "$SHOP" read second-change)
under=$(land --repo "$SHOP" read second-change --record "$(record 1 '{"kind": "round", "ran": [{"name": "correctness", "why": "a line of the app changes"}], "answered": ["codex"]}')" 2>&1 || true)
dropped=$(land --repo "$SHOP" read second-change --record "$(record 1 '{"kind": "full", "ran": [{"name": "default", "why": "the request is careful"}], "left_out": [{"name": "security", "why": "no input is read"}], "answered": ["codex"]}')" 2>&1 || true)
next=$(land --repo "$SHOP" read second-change --record "$(record 1 '{"kind": "full", "ran": [{"name": "default", "why": "the request is careful"}], "answered": ["codex", "claude"], "silent": [{"name": "gemini", "why": "at capacity"}], "must_fix": 1}')" | field '(d["recorded"]["verdict"], d["next"])')
err=$(land --repo "$SHOP" propose second-change --title x --notes "$NOTES" 2>&1 || true)
if [ "$(field '(d["due"], d["floor"], d["why"])' <<<"$out")" = "('review', 'full', 'the request is careful: the owner says so')" ] \
  && grep -q "this change gets the project's full set at the least (the request is careful: the owner says so), and the record says a review round with the profiles that fit" <<<"$under" \
  && grep -q "the project's full set leaves no profile out" <<<"$dropped" && [ "$next" = "('must-fix', 'review')" ] \
  && grep -q "a review is due before anything is proposed, the project's full set at the least" <<<"$err"; then
  pass "a request the owner called careful gets the project's full set: a record of less is refused, one that leaves a profile out too; a round in which one source did not answer counts, and a must-fix is followed by another round"
else
  fail "the read of a careful request: $out / $next / $err"
fi
echo '# and no other word' >> "$tree/tests/second-change.sh" && git -C "$tree" commit -q -am "fix: what the round found"
err=$(land --repo "$SHOP" read second-change 2>&1 || true)
land --repo "$SHOP" gate second-change >/dev/null
out=$(land --repo "$SHOP" read second-change)
land --repo "$SHOP" read second-change --record "$(record 2 '{"kind": "full", "ran": [{"name": "default", "why": "the request is careful"}], "answered": ["codex", "claude", "gemini"], "nit": 2}')" >/dev/null
if grep -q "no check is on record for this tip" <<<"$err" && [ "$(field '(d["due"], d["floor"], d["round"], len(d["reads"]))' <<<"$out")" = "('review', 'full', 2, 1)" ]; then
  pass "a fix is reviewed only after the machine checks ran on it, and the second round knows the first"
else
  fail "the second round: $err / $out"
fi
# Careful only by the owner's word, given after its plan: no talk was due, so none is asked for, and the text says why it had none.
err=$(land --repo "$SHOP" propose second-change --title "fix(app): both lines stay" --notes "$NOTES" 2>&1 || true)
printf '%s\n' '' '## Migration' '' 'none' >> "$NOTES"
land --repo "$SHOP" propose second-change --title "fix(app): both lines stay" --notes "$NOTES" >/dev/null
text=$SHOP/.git/lem/tasks/second-change/pr.md
if grep -q "^- no plan talk: the request became careful after its plan, by the owner's word$" "$text" \
  && [ "$(sed -n '/^## Checks$/,/^## Decisions of the build$/p' "$text" | grep -c 'plan talk')" = 1 ] && [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] \
  && ! grep -q '"event": "careful.missed", "task": "second-change"' "$SHOP/.git/lem/events.jsonl"; then
  pass "a request the owner called careful after its plan is proposed with no plan talk, its checks say in words that it had none and why, and that is no cause of not green"
else
  fail "a request careful by the owner's later word: $(cat "$text" 2>/dev/null)"
fi
agent=$(land --repo "$SHOP" land second-change --by agent --message "fix(app): both lines stay" 2>&1 || true)
if grep -q "the notes lack ## Migration" <<<"$err" && grep -qxF -- "- careful: yes, the owner says so; the review says no: $NOT_CAREFUL" "$text" && [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] \
  && grep -q "^- the review, round 1 (the project's full set; answered: codex, claude; no answer from gemini (at capacity)): must-fix, 1 must-fix, 0 should, 0 nit$" "$text" \
  && grep -q '^  - ran default: the request is careful$' "$text" \
  && grep -q "^- the review, round 2 (the project's full set; answered: codex, claude, gemini): clean, 0 must-fix, 0 should, 2 nit$" "$text" \
  && grep -q "a careful request is merged by a person, whatever the settings say" <<<"$agent" && [ "$(status second-change)" = open ]; then
  pass "the notes of a careful request say whether it holds a migration, its text shows both rounds with who answered and who did not, and no agent merges it though it is green"
else
  fail "a careful request at the proposal: $err / $agent / $(cat "$text" 2>/dev/null)"
fi
if [ "$(status_of land --repo "$SHOP" land second-change --by owner)" = 1 ]; then pass "one commit for the branch needs its subject"; else fail "squash without a message"; fi
before=$(git -C "$ORIGIN" rev-parse main)
# A commit hook that changes a tracked file makes the one commit another tree than the gate saw.
gated=$(git -C "$tree" rev-parse HEAD)
printf '%s\n' '#!/bin/sh' 'echo stamped >> app.txt && git add app.txt' > "$SHOP/.git/hooks/pre-commit"
chmod +x "$SHOP/.git/hooks/pre-commit"
err=$(land --repo "$SHOP" land second-change --by owner --message "fix(app): both lines stay" 2>&1 || true)
rm "$SHOP/.git/hooks/pre-commit"
if grep -q "a commit hook changed the files" <<<"$err" && [ "$(git -C "$ORIGIN" rev-parse main)" = "$before" ] && [ "$(git -C "$tree" rev-parse HEAD)" = "$gated" ] \
  && [ -z "$(git -C "$tree" status --porcelain)" ] && [ "$(status second-change)" = open ]; then
  pass "a commit hook that changes the one commit's files stops the landing, and the branch is put back as the gate saw it"
else
  fail "squash with a hook that changes the tree: $err"
fi
out=$(land --repo "$SHOP" land second-change --by owner --message "fix(app): both lines stay")
if [ "$(git -C "$ORIGIN" rev-list --count "$before..main")" = 1 ] && [ "$(git -C "$ORIGIN" log -1 --format=%s main)" = "fix(app): both lines stay" ] \
  && [ "$(git -C "$ORIGIN" show main:app.txt)" = both ] && [ "$(git -C "$ORIGIN" rev-parse 'main^{tree}')" = "$(kept second-change tree)" ] && [ "$(status second-change)" = landed ]; then
  pass "on the owner's word, with history = squash, the branch lands as one commit, and its tree is the tree the gate passed on"
else
  fail "squash landing: $out"
fi
land --repo "$SHOP" clean second-change >/dev/null
printf '%s\n' '## Decisions' '' 'none' '' '## Left open' '' 'none' '' '## Worth a look' '' '- the one line of the file.' '' '## Filed in the backlog' '' 'none' '' '## Not done' '' 'none' > "$NOTES"

# A plan of four tasks is large: it needs a plan talk too, and the talk's event has one form. The
# event log already holds the talk of another task, which does not count for this one.
shop_settings agent keep
open_task four-tasks five.txt five
tree=$(project --repo "$SHOP" worktree-dir four-tasks)
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("1. The change.", "1. The change.\n2. Its test.\n3. Its page.\n4. Its note."))' "$tree/docs/plans/20261115-four-tasks.md"
git -C "$tree" commit -q -am "docs: four tasks"
checked four-tasks
land --repo "$SHOP" read four-tasks --record "$(record 1 '{"kind": "round", "ran": [{"name": "correctness", "why": "four tasks change the app"}], "answered": ["codex"]}')" >/dev/null
# the talk of another task, landed before: a valid event that is not this task's
project --repo "$SHOP" log second-change plan.talk reviewer=codex turns:=4 questions:=1 settled:=1 open:=0 repaired:=1 design:=0 unargued:=0 root:=1 layer:=0 shared:=0 >/dev/null
talkless=$(land --repo "$SHOP" propose four-tasks --title "fix: five" --notes "$NOTES" 2>&1 || true)
typed=$(project --repo "$SHOP" log four-tasks plan.talk reviewer=codex turns=5 questions:=3 settled:=2 open:=1 repaired:=1 design:=1 unargued:=0 root:=1 layer:=0 shared:=0 2>&1 || true)
missing=$(project --repo "$SHOP" log four-tasks plan.talk reviewer=codex turns:=5 questions:=3 settled:=2 repaired:=1 design:=1 unargued:=0 root:=1 layer:=0 shared:=0 2>&1 || true)
self_bound=$(project --repo "$SHOP" log four-tasks plan.talk reviewer=codex bound:=5 turns:=5 questions:=0 settled:=0 open:=0 repaired:=0 design:=0 unargued:=0 root:=0 layer:=0 shared:=0 2>&1 || true)
if grep -q "the plan has 4 tasks, more than three, so its defender and the reviewer talk its plan through in the plan talk's companion before any code" <<<"$talkless" \
  && grep -q "the event log has no .plan.talk. of four-tasks" <<<"$talkless" && [ "$(status four-tasks)" = landing ] \
  && grep -q "each N is a whole number, written with :=" <<<"$typed" && grep -q "and nothing else; this one has design, layer, questions, repaired, reviewer, root, settled, shared, turns, unargued" <<<"$missing" \
  && grep -qF "and nothing else; this one has bound, design," <<<"$self_bound" \
  && ! grep -q '"event": "plan.talk", "task": "four-tasks"' "$SHOP/.git/lem/events.jsonl" \
  && [ "$(grep -c '"event": "plan.talk", "task": "second-change", "reviewer": "codex", "turns": 4' "$SHOP/.git/lem/events.jsonl")" = 1 ]; then
  pass "a plan of four tasks with no plan talk is not proposed, though another task's talk is in the log; a talk's event without its form is refused, the bound among its fields too, which the log adds itself, and nothing is written for it"
else
  fail "a large request with no plan talk: $talkless / $typed / $missing / $self_bound"
fi
# The talk's counts agree with each other. A talk that ran over the bound its rules give (the reviewer's
# list, two answers of the defender and two of the reviewer on each question, and the close) is a fact,
# and its record is taken with that bound beside it; so is one whose second question on a decision did not close as a design choice.
talk_log() { project --repo "$SHOP" log four-tasks plan.talk reviewer=codex "$@" 2>&1 || true; }
lost=$(talk_log turns:=6 questions:=3 settled:=1 open:=1 repaired:=1 design:=0 unargued:=0 root:=0 layer:=0 shared:=0)
undesigned=$(talk_log turns:=6 questions:=3 settled:=2 open:=1 repaired:=1 design:=2 unargued:=0 root:=0 layer:=0 shared:=0)
overrepaired=$(talk_log turns:=6 questions:=3 settled:=3 open:=0 repaired:=4 design:=0 unargued:=0 root:=0 layer:=0 shared:=0)
endless=$(talk_log turns:=11 questions:=2 settled:=1 open:=1 repaired:=1 design:=1 unargued:=3 root:=0 layer:=0 shared:=0)
unshared=$(talk_log turns:=6 questions:=3 settled:=2 open:=1 repaired:=1 design:=0 unargued:=0 root:=0 layer:=0 shared:=1)
raised_late=$(talk_log turns:=3 questions:=0 settled:=0 open:=0 repaired:=0 design:=0 unargued:=1 root:=0 layer:=0 shared:=0)
bounded=$(talk_log turns:=10 questions:=2 settled:=1 open:=1 repaired:=2 design:=1 unargued:=3 root:=1 layer:=1 shared:=1)
# a reviewer who found nothing: its first turn says it has no question, and the defender closes
lone=$(talk_log turns:=1 questions:=0 settled:=0 open:=0 repaired:=0 design:=0 unargued:=0 root:=0 layer:=0 shared:=0)
quiet_raised=$(talk_log turns:=2 questions:=0 settled:=0 open:=0 repaired:=0 design:=0 unargued:=1 root:=0 layer:=0 shared:=0)
quiet=$(talk_log turns:=2 questions:=0 settled:=0 open:=0 repaired:=0 design:=0 unargued:=0 root:=0 layer:=0 shared:=0)
startless=$(project --repo "$SHOP" log four-tasks plan.talk.start 2>&1 || true)
overstarted=$(project --repo "$SHOP" log four-tasks plan.talk.start reviewer=codex turns:=2 2>&1 || true)
started=$(project --repo "$SHOP" log four-tasks plan.talk.start reviewer=codex 2>&1 || true)
if grep -qF "settled and open add up to questions" <<<"$lost" && grep -qF "design is at most open" <<<"$undesigned" \
  && grep -qF "repaired is at most questions" <<<"$overrepaired" \
  && [ "$(field 'd["turns"], d["questions"], d["bound"]' <<<"$endless")" = "(11, 2, 10)" ] && [ "$(field 'd["shared"], d["design"]' <<<"$unshared")" = "(1, 0)" ] \
  && [ "$(field 'd["turns"], d["questions"], d["design"], d["unargued"], d["bound"]' <<<"$bounded")" = "(10, 2, 1, 3, 10)" ] \
  && grep -qF "a talk has two turns at the least" <<<"$lone" && grep -qF "a talk of no question and two turns has no turn after the list, so unargued is 0" <<<"$quiet_raised" \
  && [ "$(field 'd["turns"], d["unargued"], d["bound"]' <<<"$raised_late")" = "(3, 1, 2)" ] \
  && [ "$(field 'd["turns"], d["questions"], d["settled"], d["open"], d["bound"]' <<<"$quiet")" = "(2, 0, 0, 0, 2)" ] \
  && grep -qF "plan.talk.start takes reviewer=AGENT, and nothing else" <<<"$startless" && grep -qF "plan.talk.start takes reviewer=AGENT, and nothing else" <<<"$overstarted" \
  && [ "$(field 'd["event"], d["reviewer"]' <<<"$started")" = "('plan.talk.start', 'codex')" ] \
  && [ "$(grep -c '"event": "plan.talk", "task": "four-tasks"' "$SHOP/.git/lem/events.jsonl")" = 5 ] \
  && [ "$(grep -c '"event": "plan.talk.start", "task": "four-tasks"' "$SHOP/.git/lem/events.jsonl")" = 1 ]; then
  pass "a talk's counts agree: each question of the list ends settled or open, a design choice is an open one, and a question gets one repair at most; a talk over its bound of 4 × questions + 2 turns, or with more decisions two questions named than design choices, is written as it ran, with the bound the log adds; a talk of no question and two turns has nothing raised after its list; the start of a talk names its reviewer and nothing else, and a refused record writes nothing"
else
  fail "the counts of a plan talk: $lost / $undesigned / $overrepaired / $endless / $unshared / $bounded / $lone / $quiet_raised / $raised_late / $quiet / $startless / $overstarted / $started"
fi
project --repo "$SHOP" log four-tasks plan.talk reviewer=claude turns:=3 questions:=1 settled:=1 open:=0 repaired:=0 design:=0 unargued:=0 root:=0 layer:=0 shared:=0 >/dev/null
project --repo "$SHOP" log four-tasks plan.talk reviewer=codex turns:=23 questions:=5 settled:=4 open:=1 repaired:=3 design:=1 unargued:=2 root:=2 layer:=1 shared:=0 >/dev/null
# the same event with one count more, which Lem has no words for: a count added to the event later needs no change of the landing
"$PY" -c 'import json, sys; p = sys.argv[1]; talk = json.loads(open(p).read().splitlines()[-1]); talk["rounds"] = 2; open(p, "a").write(json.dumps(talk) + "\n")' "$SHOP/.git/lem/events.jsonl"
out=$(land --repo "$SHOP" propose four-tasks --title "fix: five" --notes "$NOTES")
text=$SHOP/.git/lem/tasks/four-tasks/pr.md
if [ "$(field 'd["green"]' <<<"$out")" = True ] && [ "$(status four-tasks)" = open ] \
  && grep -qxF -- "- the plan talk: codex argued the plan with its defender, 23 turns, over the bound of 22 for its 5 questions; 4 positions settled by the two, 1 left open; 5 questions in the reviewer's first list, 3 repaired by the defender, 1 of the open ones a design choice, 2 raised after the list and not argued, 2 repaired at the cause, 1 layer over a cited decision, 0 decisions two questions named, rounds: 2" "$text" \
  && [ "$(grep -c 'plan talk' "$text")" = 1 ] && grep -qxF -- "- careful: no; the review says no: $NOT_CAREFUL" "$text"; then
  pass "after its plan talk a plan of four tasks is proposed, and its text holds one line of the talk, from the newest event, with its turns over the bound when they are, each of its counts in words, and a count Lem has no words for by its name"
else
  fail "a large request after its plan talk: $out / $(cat "$text" 2>/dev/null)"
fi
project --repo "$SHOP" state four-tasks dropped "the test is over" >/dev/null

# A plan that says careful calls for a plan talk: the request is not proposed without one, and with one its text holds the talk's line.
open_task careful-plan six.txt six
tree=$(project --repo "$SHOP" worktree-dir careful-plan)
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("\n## Stories", "careful: yes, a price is rounded here.\n\n## Stories", 1))' "$tree/docs/plans/20261115-careful-plan.md"
git -C "$tree" commit -q -am "docs: the plan is careful"
checked careful-plan
land --repo "$SHOP" read careful-plan --record "$(record 1 '{"kind": "full", "ran": [{"name": "default", "why": "the plan says careful"}], "answered": ["codex"]}')" >/dev/null
talkless=$(land --repo "$SHOP" propose careful-plan --title "fix: six" --notes "$MIG" 2>&1 || true)
if grep -q "the plan says that the request is careful, so its defender and the reviewer talk its plan through in the plan talk's companion before any code (.stages/talk.md.)" <<<"$talkless" \
  && grep -q "the event log has no .plan.talk. of careful-plan. The defender writes it after the talk" <<<"$talkless" \
  && grep -qF "project.py log careful-plan plan.talk reviewer=AGENT turns:=N questions:=N settled:=N open:=N repaired:=N design:=N unargued:=N root:=N layer:=N shared:=N\`" <<<"$talkless" \
  && grep -qF "for a plan that had no talk, Lem opens the companion first, as for \`needs a session\`" <<<"$talkless" \
  && [ ! -f "$SHOP/.git/lem/tasks/careful-plan/pr.md" ] && [ "$(status careful-plan)" = landing ]; then
  pass "a request whose plan says careful is not proposed while its event log has no plan talk, and the refusal names the plan stage's step, the companion Lem opens for the talk, and the event its defender writes in the form project.py takes"
else
  fail "a careful plan with no plan talk: $talkless"
fi
# an event of the older form, with no counts but the turns and the positions, as a log written before the counts holds it
printf '%s\n' '{"ts": "2026-11-15T10:00:00Z", "event": "plan.talk", "task": "careful-plan", "reviewer": "codex", "turns": 6, "settled": 2, "open": 1}' >> "$SHOP/.git/lem/events.jsonl"
land --repo "$SHOP" propose careful-plan --title "fix: six" --notes "$MIG" >/dev/null
text=$SHOP/.git/lem/tasks/careful-plan/pr.md
if [ "$(grep 'plan talk' "$text" || true)" = "- the plan talk: codex argued the plan with its defender, 6 turns; 2 positions settled by the two, 1 left open" ] \
  && [ "$(sed -n '/^## Checks$/,/^## Decisions of the build$/p' "$text" | grep -c 'plan talk')" = 1 ] && grep -qxF -- "- careful: yes, the plan says so; the review says no: $NOT_CAREFUL" "$text" \
  && [ "$(status careful-plan)" = open ]; then
  pass "after its plan talk a request whose plan says careful is proposed, and the checks of its text say who argued the plan with its defender, the turns, and the positions settled and left open; an event of the older form, with no other count, reads as before"
else
  fail "the plan talk in the text of a careful plan: $(cat "$text" 2>/dev/null)"
fi
project --repo "$SHOP" state careful-plan dropped "the test is over" >/dev/null

# A correction or a feature that came from a bug names, in its checks, the cause the investigation
# before the build found and where; a question's answer, or no investigation, gives no such line.
open_task bug-cause seven.txt seven
project --repo "$SHOP" log bug-cause investigation kind=bug call=correction "line=the total adds the refund as a payment" where=billing/invoice.py:total reproduced:=true >/dev/null
checked bug-cause && read_clean bug-cause && propose bug-cause
open_task question-cause eight.txt eight
project --repo "$SHOP" log question-cause investigation kind=investigation call=answer "line=the export reads the totals of the night before" >/dev/null
checked question-cause && read_clean question-cause && propose question-cause
text=$SHOP/.git/lem/tasks/bug-cause/pr.md
if grep -qxF -- "- the cause, as the investigation before the build found it: the total adds the refund as a payment (billing/invoice.py:total); its report: \`$SHOP/.git/lem/tasks/bug-cause/investigation.md\`" "$text" \
  && [ "$(sed -n '/^## Checks$/,/^## Decisions of the build$/p' "$text" | grep -c '^- the cause, as the investigation')" = 1 ] \
  && ! grep -q 'the cause, as the investigation' "$SHOP/.git/lem/tasks/question-cause/pr.md" \
  && ! grep -q 'the cause, as the investigation' "$SHOP/.git/lem/tasks/careful-plan/pr.md"; then
  pass "a correction that came from a bug names in its checks the cause its investigation found, with its place and the report; one after a question's answer, or with no investigation, has no such line"
else
  fail "the cause of a bug in the text: $(cat "$text" 2>/dev/null) / $(grep 'cause' "$SHOP/.git/lem/tasks/question-cause/pr.md" 2>/dev/null)"
fi
project --repo "$SHOP" state bug-cause dropped "the test is over" >/dev/null
project --repo "$SHOP" state question-cause dropped "the test is over" >/dev/null

# A file that moves into an ignored folder also leaves a folder the gate reads.
open_task moved-file extra.txt four
checked moved-file && read_clean moved-file && propose moved-file
git -C "$other" pull -q origin main && git -C "$other" mv late.txt docs/late.txt && git -C "$other" commit -q -m "docs: move late" && git -C "$other" push -q origin main
err=$(land --repo "$SHOP" land moved-file --by agent 2>&1 || true)
if [ "$(status_of land --repo "$SHOP" land moved-file --by agent)" = 1 ] && grep -q "files the gate reads (.*late.txt" <<<"$err" && [ "$(status moved-file)" = open ]; then
  pass "a file moved into an ignored folder still counts as a change of the path it left"
else
  fail "a rename across gate.ignores: $err"
fi
checked moved-file && propose moved-file
# The landing is cut off after the push and before its last state write: a copy of the scripts whose
# project.py refuses to write `landed` stands in for the kill. The main checkout also has a commit of
# its own, so it cannot follow the remote.
LATE=$WORK/late
cp -R "$PWD/skills/lem/scripts" "$LATE"
printf '%s\n' 'import runpy, sys' 'if "landed" in sys.argv: sys.exit("project.py: cut off")' \
  "sys.argv[0] = '$PWD/skills/lem/scripts/project.py'" "runpy.run_path(sys.argv[0], run_name='__main__')" > "$LATE/project.py"
git -C "$SHOP" commit -q --allow-empty -m "chore: only here"
before=$(git -C "$ORIGIN" rev-parse main)
if [ "$(status_of "$PY" -B "$LATE/land.py" --repo "$SHOP" land moved-file --by agent)" = 1 ] && [ "$(git -C "$ORIGIN" rev-list --count "$before..main")" = 1 ] \
  && [ "$(status moved-file)" = open ] && [ "$(kept moved-file intent)" != None ]; then
  pass "a landing cut off after the push leaves the commit on the base, the task open and the record the next run needs"
else
  fail "a landing cut off before the landed state: status $(status moved-file), intent $(kept moved-file intent)"
fi
landed_tip=$(git -C "$ORIGIN" rev-parse main)
out=$(land --repo "$SHOP" land moved-file --by agent)
if [ "$(status moved-file)" = landed ] && [ "$(git -C "$ORIGIN" rev-parse main)" = "$landed_tip" ] && [ "$(field 'd["tip"]' <<<"$out")" = "$landed_tip" ] \
  && [ "$(kept moved-file intent)" = None ] \
  && [ "$(field '"did not follow origin/main" in d["left_behind"] and "brings it up" not in d["left_behind"]' <<<"$out")" = True ]; then
  pass "the next run finishes it: the state is landed, nothing is pushed twice, and a main checkout that cannot follow is reported with git's own reason"
else
  fail "finishing a cut-off landing: $out"
fi
out=$(land --repo "$SHOP" land moved-file --by agent 2>&1 || true)
if grep -q "is 'landed', not .open." <<<"$out"; then pass "a landed task does not land again"; else fail "land twice: $out"; fi
git -C "$SHOP" reset -q --hard origin/main
out=$(land --repo "$SHOP" clean moved-file)
if [ "$(field '(d["worktree"], d["branch"])' <<<"$out")" = "(True, 'fix/moved-file')" ] && [ ! -e "$SHOP/.lem/worktrees/moved-file" ] && [ -z "$(git -C "$SHOP" branch --list fix/moved-file)" ]; then
  pass "clean removes a landed task's worktree and its branch in one run"
else
  fail "land clean: $out"
fi

# A landing cut off after the push, and then more work on the branch: what was pushed is written
# down, and the new tip lands only through its own base, checks and review.
shop_settings agent keep
open_task more-work m.txt five
checked more-work && read_clean more-work && propose more-work
"$PY" -B "$LATE/land.py" --repo "$SHOP" land more-work --by agent >/dev/null 2>&1 || true
git -C "$SHOP" merge -q --ff-only origin/main
tree=$SHOP/.lem/worktrees/more-work
# the first half is on the base now, so its test no longer fails there: the story is held by a test of the second half
echo six > "$tree/n.txt" && echo 'grep -qx six n.txt' > "$tree/tests/more-work-n.sh"
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("tests/more-work.sh", "tests/more-work-n.sh"))' "$tree/docs/plans/20261115-more-work.md"
git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: more-work, the second half"
err=$(land --repo "$SHOP" land more-work --by agent 2>&1 || true)
if grep -q "from a landing that was cut off, and the branch has more work since" <<<"$err" && [ "$(status more-work)" = open ] && ! git -C "$ORIGIN" cat-file -e main:n.txt 2>/dev/null \
  && [ "$(kept more-work intent)" = None ] && [ "$(kept more-work landed_before | grep -c '\.\.')" = 1 ]; then
  pass "after a cut-off landing and more work, the pushed range is written down and the new tip is refused until its own checks ran"
else
  fail "a stale landing record with more work: $err"
fi
checked more-work
out=$(land --repo "$SHOP" read more-work)
read_clean more-work 2 && propose more-work
landed=$(land --repo "$SHOP" land more-work --by agent)
if [ "$(field '(d["due"], d["floor"], d["round"])' <<<"$out")" = "('review', 'read', 2)" ] && [ "$(git -C "$ORIGIN" show main:n.txt)" = six ] && [ "$(status more-work)" = landed ] \
  && [ "$(field 'd["tip"]' <<<"$landed")" = "$(git -C "$ORIGIN" rev-parse main)" ]; then
  pass "then the second half gets a review of its own and lands as its own range"
else
  fail "landing the work added after a cut-off landing: $out / $landed"
fi
land --repo "$SHOP" clean more-work >/dev/null

# Two rounds at most. A usual request whose read found a must-fix gets a round after the fix, and one
# that is not clean after the second round goes to the owner as not green.
open_task not-clean nc.txt seven
checked not-clean
# A run that is cut off before the review is written down leaves nothing, the next run writes it
# down once, and the same record sent again is refused: one review never takes two rounds. A copy
# of the scripts whose project.py refuses the `review` event stands in for the kill.
CUT=$WORK/cut
cp -R "$PWD/skills/lem/scripts" "$CUT"
printf '%s\n' 'import runpy, sys' 'if "review" in sys.argv: sys.exit("project.py: cut off")' \
  "sys.argv[0] = '$PWD/skills/lem/scripts/project.py'" "runpy.run_path(sys.argv[0], run_name='__main__')" > "$CUT/project.py"
first=$(record 1 '{"kind": "read", "answered": ["codex"], "must_fix": 2}')
cut_off=$(status_of "$PY" -B "$CUT/land.py" --repo "$SHOP" read not-clean --record "$first")
nothing=$(kept not-clean reads)
land --repo "$SHOP" read not-clean --record "$first" >/dev/null
twice=$(land --repo "$SHOP" read not-clean --record "$first" 2>&1 || true)
if [ "$cut_off" = 1 ] && [ "$nothing" = None ] && grep -q "attempt 1, and the next review of this task is attempt 2: that review is written down already" <<<"$twice" \
  && [ "$(land --repo "$SHOP" read not-clean | field '(d["round"], d["attempt"], len(d["reads"]))')" = "(2, 2, 1)" ]; then
  pass "a review whose record is sent again, after a cut-off run or by mistake, is written down once and takes one round"
else
  fail "a record sent twice: $cut_off / $nothing / $twice"
fi
tree=$SHOP/.lem/worktrees/not-clean
echo eight > "$tree/nc2.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: the first read's findings"
land --repo "$SHOP" gate not-clean >/dev/null
out=$(land --repo "$SHOP" read not-clean)
again=$(land --repo "$SHOP" read not-clean --record "$(clean 2)" 2>&1 || true)
land --repo "$SHOP" read not-clean --record "$(record 2 '{"kind": "round", "ran": [{"name": "correctness", "why": "a file of the app changes"}], "left_out": [{"name": "security", "why": "no input from outside is read"}], "answered": ["codex"], "must_fix": 1}')" >/dev/null
echo nine > "$tree/nc3.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: the round's finding"
land --repo "$SHOP" gate not-clean >/dev/null
third=$(land --repo "$SHOP" read not-clean)
fourth=$(land --repo "$SHOP" read not-clean --record "$(record 3 '{"kind": "round", "ran": [{"name": "correctness", "why": "a file of the app changes"}], "answered": ["codex"]}')" 2>&1 || true)
proposed=$(land --repo "$SHOP" propose not-clean --title "fix: not-clean" --notes "$NOTES")
text=$SHOP/.git/lem/tasks/not-clean/pr.md
agent=$(land --repo "$SHOP" land not-clean --by agent 2>&1 || true)
why="two rounds reviewed it: the last one left 1 must-fix, and nobody reviewed what changed after it"
if [ "$(field '(d["due"], d["floor"], d["why"])' <<<"$out")" = "('review', 'round', 'an earlier review found a must-fix: after its fix a round reviews the change')" ] && grep -q "this change gets a review round with the profiles that fit at the least" <<<"$again" \
  && [ "$(field '(d["due"], d["why"])' <<<"$third")" = "('owner', '$why')" ] && grep -q "no review is due: two rounds reviewed it" <<<"$fourth" \
  && [ "$(field '(d["green"], d["not_green"])' <<<"$proposed")" = "(False, ['$why'])" ] && [ "$(kept not-clean title)" = "fix: not-clean" ] \
  && [ "$(sed -n 1p "$text")" = '**Not green.**' ] && [ "$(sed -n 3p "$text")" = "- $why" ] && grep -q '^  - left out security: no input from outside is read$' "$text" \
  && grep -q "^not green: $why$" "$SHOP/.git/lem/tasks/not-clean/state.md" \
  && grep -q "the request is not green ($why), so a person merges it" <<<"$agent"; then
  pass "a usual request with a must-fix gets a round after its fix, with each profile it ran or left out and why; after two rounds no third is taken, the request is proposed as not green, which its first lines say with the reason, and no agent merges it"
else
  fail "two rounds at most: $out / $again / $third / $fourth / $proposed / $agent / $(sed -n 1,4p "$text" 2>/dev/null)"
fi
land --repo "$SHOP" land not-clean --by owner >/dev/null
if [ "$(status not-clean)" = landed ] && [ "$(git -C "$ORIGIN" show main:nc3.txt)" = nine ]; then pass "the owner's word lands a request that is not green"; else fail "the owner lands a request that is not green"; fi
land --repo "$SHOP" clean not-clean >/dev/null

# No gate command, a protected branch, and a repository with no remote.
open_task third-change note.txt three
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' > "$SHOP/.lem/project.toml"
err=$(land --repo "$SHOP" start third-change 2>&1 || true)
if [ "$(status_of land --repo "$SHOP" start third-change)" = 1 ] && grep -q "no gate command" <<<"$err" && [ "$(status third-change)" = blocked ]; then
  pass "a project with no gate command lands nothing, and the task is blocked instead of holding the landing line"
else
  fail "start with no gate: $err"
fi
printf '%s\n' '[branch]' 'base = "release"' 'land = "agent"' 'protected = ["release"]' > "$SHOP/.lem/project.toml"
if [ "$(status_of land --repo "$SHOP" start third-change)" = 1 ]; then pass "no step runs toward a branch the settings refuse"; else fail "land toward a protected base"; fi
# The first task of a new repository sets up the checks: the main checkout's settings have no gate
# command, and the task's branch adds them to its own .lem/project.toml. That gate gates the task,
# and its pull request is not green for it, so that a person reads the checks once. A branch that
# changes a gate the main checkout already has is gated by the main checkout's, as before.
FG=$WORK/first-gate
git init -q -b main "$FG" && ident "$FG"
project --repo "$FG" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' > "$FG/.lem/project.toml"
git -C "$FG" add -A && git -C "$FG" commit -q -m "chore: start"
task_in "$FG" set-up-checks c.txt checked
tree=$(project --repo "$FG" worktree-dir set-up-checks)
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[gate]' 'commands = ["echo 3 passed"]' > "$tree/.lem/project.toml"
git -C "$tree" commit -q -am "chore: the checks"
brought_start=$(land --repo "$FG" start set-up-checks 2>&1 || true)
brought_gate=$(land --repo "$FG" base set-up-checks >/dev/null 2>&1 && land --repo "$FG" gate set-up-checks 2>&1 || true)
brought_floor=$(land --repo "$FG" read set-up-checks | field '(d["floor"], d["why"])' 2>&1 || true)
land --repo "$FG" read set-up-checks --record "$(record 1 '{"kind": "full", "ran": [{"name": "default", "why": "the checks come with it"}], "answered": ["codex"]}')" >/dev/null 2>&1 || true
land --repo "$FG" propose set-up-checks --title "chore: the checks" --notes "$MIG" >/dev/null 2>&1 || true
brought_agent=$(land --repo "$FG" land set-up-checks --by agent 2>&1 || true)
text=$FG/.git/lem/tasks/set-up-checks/pr.md
FG2=$WORK/kept-gate
git init -q -b main "$FG2" && ident "$FG2"
project --repo "$FG2" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[gate]' 'commands = ["echo main passed"]' > "$FG2/.lem/project.toml"
git -C "$FG2" add -A && git -C "$FG2" commit -q -m "chore: start"
task_in "$FG2" other-checks k.txt kept
tree=$(project --repo "$FG2" worktree-dir other-checks)
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' '[gate]' 'commands = ["false"]' > "$tree/.lem/project.toml"
git -C "$tree" commit -q -am "chore: other checks"
kept_gate=$(land --repo "$FG2" start other-checks >/dev/null 2>&1 && land --repo "$FG2" base other-checks >/dev/null 2>&1 && land --repo "$FG2" gate other-checks 2>&1 || true)
kept_floor=$(land --repo "$FG2" read other-checks | field '(d["floor"], d["why"])' 2>&1 || true)
land --repo "$FG2" read other-checks --record "$(record 1 '{"kind": "full", "ran": [{"name": "default", "why": "the checks change"}], "answered": ["codex"]}')" >/dev/null 2>&1 || true
land --repo "$FG2" propose other-checks --title "chore: other checks" --notes "$MIG" >/dev/null 2>&1 || true
gate_why="the change edits [gate] of .lem/project.toml, the settings that say what is careful and what the gate runs"
if [ "$(status_in "$FG" set-up-checks)" = open ] && ! grep -q "no gate command" <<<"$brought_start" \
  && [ "$(field '[(c["command"], c["last"]) for c in d["commands"]]' <<<"$brought_gate" 2>/dev/null)" = "[('echo 3 passed', '3 passed')]" ] \
  && [ "$(sed -n 1p "$text" 2>/dev/null)" = '**Not green.**' ] \
  && [ "$(sed -n 3p "$text")" = "- the gate came with this change: the main checkout's settings name no gate command, and the branch's .lem/project.toml brings \`echo 3 passed\`. Read the checks once: every later task is gated on them" ] \
  && grep -qF "a careful request is merged by a person, whatever the settings say ($gate_why)" <<<"$brought_agent" \
  && [ "$brought_floor" = "('full', 'the request is careful: $gate_why')" ] && [ "$kept_floor" = "('full', 'the request is careful: $gate_why')" ] \
  && [ "$(field '[(c["command"], c["last"]) for c in d["commands"]]' <<<"$kept_gate" 2>/dev/null)" = "[('echo main passed', 'main passed')]" ] \
  && [ "$(sed -n 1p "$FG2/.git/lem/tasks/other-checks/pr.md" 2>/dev/null | cut -c1-10)" = '**Green.**' ] \
  && grep -qxF -- "- careful: yes, $gate_why; the review says no: $NOT_CAREFUL" "$FG2/.git/lem/tasks/other-checks/pr.md"; then
  pass "a first task that brings the gate on its own branch, while the main checkout's settings have none, is gated by it and is not green for it; a branch that changes a gate the main checkout has is gated by the main checkout's; either is careful by the script, which says why, so it gets the full set and a person merges it"
else
  fail "a gate that comes with the change: $brought_start / $brought_gate / $brought_floor / $brought_agent / $kept_gate / $kept_floor / $(cat "$text" 2>/dev/null)"
fi
project --repo "$FG" state set-up-checks dropped "the test is over" >/dev/null
project --repo "$FG2" state other-checks dropped "the test is over" >/dev/null

finish
