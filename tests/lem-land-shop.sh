#!/usr/bin/env bash
# The landing: land.py takes one task from `ready` through the machine checks and one read to a pull
# request on GitHub, the merge agent's read, and from there to the base branch. This block's origin is
# on GitHub through the stand-in for `gh` (lib.sh); lem-land-backlog.sh holds what a review saw outside
# the change, judged by the bar (an item, a fix or a line of the pull request), a task's own item and
# the items in the merge agent's brief, and lem-land-github.sh holds the forge's own cases.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

ORIGIN=$WORK/origin.git
SHOP=$WORK/shop
git init -q --bare -b main "$ORIGIN"
git clone -q "$ORIGIN" "$SHOP" 2>/dev/null
ident "$SHOP"
git -C "$SHOP" config remote.origin.url https://github.com/acme/shop.git
git -C "$SHOP" config "url.$ORIGIN.insteadOf" https://github.com/acme/shop.git
project --repo "$SHOP" init --base main >/dev/null
# shop_settings LAND HISTORY: the settings, an edit of the owner's in the main checkout; shop_lines LINE...: any other settings so
shop_lines() { printf '%s\n' "$@" > "$SHOP/.lem/settings.toml"; }
shop_settings() {
  shop_lines '[branch]' 'base = "main"' "land = \"$1\"" "history = \"$2\"" 'protected = ["release"]' \
    '[checks]' 'commands = ["test -f ok.txt", "echo 7 passed"]'
}
shop_settings owner keep
mkdir -p "$SHOP/docs" "$SHOP/.claude/rules" && echo guide > "$SHOP/docs/guide.md" && echo one > "$SHOP/app.txt"
printf '%s\n' '---' 'paths:' '  - "tests/**"' '---' 'A test names what it checks.' > "$SHOP/.claude/rules/tests.md"
printf '%s\n' '---' 'paths:' '  - "billing/**"' '---' 'Money is an integer.' > "$SHOP/.claude/rules/money.md"
git -C "$SHOP" add -A && git -C "$SHOP" commit -q -m "chore: start" && git -C "$SHOP" push -q origin main
# open_task SLUG FILE TEXT: a full change of the shop, with the lead's read of its criteria
open_task() { task_in "$SHOP" "$@" && read_in "$SHOP" "$1"; }
status() { status_in "$SHOP" "$1"; }
kept() { kept_in "$SHOP" "$@"; }
# the machine steps with the polish pass, a read that found nothing, and the proposal, for the tests that are about a later step
checked() { land --repo "$SHOP" start "$1" >/dev/null && land --repo "$SHOP" base "$1" >/dev/null && polish_in "$SHOP" "$1" && land --repo "$SHOP" checks "$1" >/dev/null; }
read_clean() { land --repo "$SHOP" read "$1" --record "$(clean "$1" "${2:-1}")" >/dev/null; }
propose() { land --repo "$SHOP" propose "$1" --title "fix: $1" --notes "$NOTES" >/dev/null; }

open_task first-change ok.txt yes
# first-change began on the release before this one (lem_release.BEFORE): its open wrote this Lem's own release as its
# mark, the one Claude Code's list of this run gives (lib.sh), and the mark now says the release before. It lands below.
version=$("$PY" -c 'import json; print(json.load(open(".claude-plugin/plugin.json"))["version"])')
prior=$("$PY" -B -c 'import sys; sys.path.insert(0, "src"); from lem import release as lem_release; print(lem_release.BEFORE)' 2>/dev/null || true)
began=$(cat "$SHOP/.lem/state/tasks/first-change/release.txt" 2>/dev/null || true)
printf '%s\n' "$prior" > "$SHOP/.lem/state/tasks/first-change/release.txt"
open_task second-change app.txt two
if [ "$(status_of land --repo "$SHOP" checks first-change)" = 1 ] && [ "$(status_of land --repo "$SHOP" base first-change)" = 1 ] \
  && [ "$(status_of land --repo "$SHOP" read first-change)" = 1 ] && [ "$(status_of land --repo "$SHOP" propose first-change --title x --notes "$NOTES")" = 1 ] \
  && [ "$(status_of land --repo "$SHOP" merge first-change --by owner)" = 1 ] && [ "$(status first-change)" = ready ]; then
  pass "no step runs on a task that did not take the landing line, and the owner's word lands nothing that was not proposed"
else
  fail "land steps before start"
fi
out=$(land --repo "$SHOP" start first-change)
err=$(land --repo "$SHOP" start second-change 2>&1 || true)
if [ "$(field '(d["remote"], d["forge"])' <<<"$out")" = "(True, 'github')" ] && [ "$(status first-change)" = landing ] \
  && [ "$(field 'd["task"]' <<<"$err")" = second-change ] && [ "$(status second-change)" = landing ]; then
  pass "start puts a task in landing, and a second task starts its landing while the first is there"
else
  fail "land start: $out / $err"
fi
err=$(land --repo "$SHOP" checks first-change 2>&1) && code=0 || code=$?
if [ "$code" = 1 ] && grep -qF "\`lem land base first-change\` comes first" <<<"$err"; then pass "the gate refuses to run before the base was brought in"; else fail "gate before base: $code $err"; fi
out=$(land --repo "$SHOP" base first-change)
if [ "$(field '(d["ahead"], d["moved"], d["onto"])' <<<"$out")" = "(1, False, 'origin/main')" ]; then
  pass "base rebases onto the remote's base branch and says how many commits the branch adds"
else
  fail "land base: $out"
fi
polish_in "$SHOP" first-change
out=$(land --repo "$SHOP" checks first-change)
tip=$(git -C "$SHOP/.lem/worktrees/first-change" rev-parse HEAD)
if [ "$(field '(d["green"], [c["exit"] for c in d["commands"]], d["commands"][1]["last"])' <<<"$out")" = "(True, [0, 0], '7 passed')" ] \
  && [ "$(kept first-change gated)" = "$tip" ] && [ "$(cat "$SHOP/.lem/state/tasks/first-change/gate/02.log")" = "7 passed" ] \
  && [ "$(grep -c '"event": "gate", "task": "first-change"' "$SHOP/.lem/state/events.jsonl")" = 2 ]; then
  pass "gate runs every command with its output in a file, keeps the last line, logs each result and records the green tip"
else
  fail "land gate: $out"
fi
if [ "$(field '(d["criteria"]["ok"], [(t["criterion"], t["problem"]) for t in d["criteria"]["tests"]], d["bar"], d["size"]["files"], d["size"]["in_parts"])' <<<"$out")" \
  = "(True, [(1, None)], {'lowered': [], 'not_covered': [], 'edited': []}, 3, False)" ] && grep -q '"event": "task.red", "task": "first-change"' "$SHOP/.lem/state/events.jsonl"; then
  pass "after the commands the gate proves each criterion's test on the branch and on the base commit, looks for a lowered bar and counts the size"
else
  fail "the machine checks after the gate's commands: $out"
fi
# A review before anything is proposed: the script says the least it may be, and what a reviewer gets.
err=$(land --repo "$SHOP" propose first-change --title "fix: the file is there" --notes "$NOTES" 2>&1 || true)
out=$(land --repo "$SHOP" read first-change)
base=$(git -C "$SHOP" rev-parse origin/main)
if grep -q "a review is due before anything is proposed, one read at the least" <<<"$err" && [ "$(status first-change)" = landing ] \
  && [ "$(field '(d["due"], d["floor"], d["round"], d["in_parts"], sorted(d["inputs"]), d["inputs"]["range"], [r.split("/.claude/")[-1] for r in d["inputs"]["rules"]], d["inputs"]["filed"], d["inputs"]["backlog"])' <<<"$out")" \
  = "('review', 'read', 1, False, ['backlog', 'bar', 'filed', 'plan', 'range', 'review', 'rules', 'topics', 'words', 'worktree'], '$base..$tip', ['rules/tests.md'], [], [])" ] \
  && [ "$(cat "$(field 'd["inputs"]["words"]' <<<"$out")")" = "Put yes into ok.txt." ] && [ -f "$(field 'd["inputs"]["plan"]' <<<"$out")" ] \
  && [ "$(field 'd["inputs"]["review"]' <<<"$out")" = "$SHOP/.revmux" ]; then
  pass "nothing is proposed before its review; for a request that is not careful the floor is one read, and a reviewer gets the owner's words, the plan, the range, the rule files of the changed files, the project's topics, the items of the backlog and the folder of the review tool"
else
  fail "the read that is due: $err / $out"
fi
err=$(land --repo "$SHOP" read first-change --record "$(record first-change 1 '{"kind": "read", "answered": [], "must_fix": 1}')" 2>&1 || true)
shape=$(land --repo "$SHOP" read first-change --record "$(record first-change 1 '{"kind": "glance", "answered": ["codex"]}')" 2>&1 || true)
late=$(land --repo "$SHOP" read first-change --record "$(clean first-change 2)" 2>&1 || true)
# a review of another tip than the branch's now carries the same attempt: its record names the tip it read, and is refused
stale=$(land --repo "$SHOP" read first-change --record "$(record first-change 1 '{"kind": "read", "answered": ["codex"], "tip": "'"$base"'"}')" 2>&1 || true)
out=$(land --repo "$SHOP" read first-change --record "$(record first-change 1 '{"kind": "read", "answered": ["codex"], "should": 1}')")
if grep -q "findings and no source that answered" <<<"$err" && grep -q ".kind. is one of read, round, full" <<<"$shape" \
  && grep -q "the record says attempt 2, and the next review of this task is attempt 1" <<<"$late" \
  && grep -qF "the record is of the review of ${base:0:12}, and the branch is at ${tip:0:12} now" <<<"$stale" \
  && [ "$(field '(d["recorded"]["round"], d["recorded"]["kind"], d["recorded"]["verdict"], d["recorded"]["should"], d["next"])' <<<"$out")" = "(1, 'read', 'clean', 1, 'none')" ] \
  && [ "$(grep -c '"event": "review", "task": "first-change"' "$SHOP/.lem/state/events.jsonl")" = 1 ] && [ "$(status_of land --repo "$SHOP" read first-change --record "$(clean first-change 2)")" = 1 ]; then
  pass "a review is written down from a file, with its round, its kind, who answered and its counts; a record that does not have the form, the number of this review or the tip it is of is refused, and a change that was reviewed clean is not reviewed again"
else
  fail "recording a read: $err / $stale / $out"
fi
printf '%s\n' '## Decisions' '' 'none' > "$WORK/thin.md"
err=$(land --repo "$SHOP" propose first-change --title "fix: the file is there" --notes "$WORK/thin.md" 2>&1 || true)
out=$(land --repo "$SHOP" propose first-change --title "fix: the file is there" --notes "$NOTES")
text=$SHOP/.lem/state/tasks/first-change/pr.md
if grep -q "the notes lack ## Left open, ## Worth a look, ## Filed in the backlog, ## Not done" <<<"$err" && [ "$(field '(d["pull_request"], d["green"], d["not_green"], d["branch"])' <<<"$out")" = "({'number': 1, 'url': 'https://github.com/acme/shop/pull/1'}, True, [], 'fix/first-change')" ] \
  && [ "$(status first-change)" = open ] && [ "$(kept first-change proposed)" = "$tip" ] && [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] && grep -q '^green$' "$SHOP/.lem/state/tasks/first-change/state.md" \
  && [ "$(grep '^## ' "$text" | tr '\n' '|')" = "## The request|## Acceptance criteria|## Checks|## Decisions of the build|## Decisions|## Left open|## Worth a look|## Filed in the backlog|## Not done|" ] \
  && [ "$(sed -n '/^## Decisions of the build$/,/^## Decisions$/p' "$text" | sed -n 3p)" = none ] && [ "$(head -1 "$text")" = '**Green.** The checks passed with the bar where it was, the review left no must-fix, no criterion changed, and no decision past the personas was taken without an answer.' ] \
  && grep -q '^> Put yes into ok.txt\.$' "$text" && grep -q '^1\. The file holds the word the owner asked for\.$' "$text" \
  && grep -q 'sh tests/first-change.sh.: passes on the branch, fails on the base commit' "$text" && grep -q '^- check, .echo 7 passed.: 7 passed$' "$text" \
  && grep -q "^- the tests of the criteria: 1 pass on the branch and fail on the base commit$" "$text" && grep -q '^- the bar: no mark of a lowered bar found$' "$text" \
  && grep -q '^- the review, round 1 (one read; answered: codex): clean, 0 must-fix, 1 should, 0 nit$' "$text" && grep -qxF -- "- careful: no; the review says no: $NOT_CAREFUL" "$text" && grep -q '^- the one line of the file\.$' "$text" \
  && ! grep -q 'plan talk' "$text" && ! grep -q '"event": "plan.talk", "task": "first-change"' "$SHOP/.lem/state/events.jsonl"; then
  pass "the pull request is opened on GitHub: the task is open, and the text for the owner says green first, then holds his words, the criteria with their tests, each check with what it returned, the decisions of the record (none here), then the notes; a plain request of one task needs no plan talk, and its text has no line of one"
else
  fail "propose: $err / $out / $(cat "$text" 2>/dev/null)"
fi
# The merge agent reads it: its brief, then its reply written down. With branch.land = "owner" the review still calls him.
brief=$(land --repo "$SHOP" merge-review first-change)
unread=$(printf '%s\n' 'A fine change.' > "$WORK/no-verdict.md"; land --repo "$SHOP" merge-review first-change --file "$WORK/no-verdict.md" --tip "$tip" --base "$base" 2>&1 || true)
# the answer of a brief of another tip (an earlier proposal) is not written down, and each tip has its own answer file
superseded=$(printf '%s\n' 'Verdict: merge. A fine change.' > "$WORK/old-answer.md"; land --repo "$SHOP" merge-review first-change --file "$WORK/old-answer.md" --tip "$base" --base "$base" 2>&1 || true)
# an answer whose base no brief named is not written down either: the read covers the base its brief named
unnamed=$(land --repo "$SHOP" merge-review first-change --file "$WORK/old-answer.md" --tip "$tip" --base "$tip" 2>&1 || true)
called=$(merge_read "$SHOP" first-change)
err=$(land --repo "$SHOP" merge first-change --by merger 2>&1 || true)
# shellcheck disable=SC2016  # the backticks are the message's own marks
if [ "$(field '(d["seat"]["agent"], d["seat"]["from"], d["facts"]["pull_request"]["number"], d["facts"]["green"], d["facts"]["land"], d["facts"]["time"]["seconds"] is not None)' <<<"$brief")" = "('claude', \"Lem's default\", 1, True, 'owner', True)" ] \
  && [ "$(field '(d["facts"]["pictures"], d["facts"]["try"])' <<<"$brief")" = "([], {'worktree': '.lem/worktrees/first-change', 'checkout': 'gh pr checkout 1'})" ] \
  && [ "$(head -n 1 "$(field 'd["brief"]' <<<"$brief")")" = 'Read `skills/lem/prompts/merge.md` in the folder that `lem version` prints as `root`, and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, with `lem doctor` as the check. Your reply is the review, in the form that file gives, and nothing else.' ] \
  && ! grep -qF "$PWD/skills/lem" "$(field 'd["brief"]' <<<"$brief")" && grep -qF '"owner_merges": "branch.land is' "$(field 'd["brief"]' <<<"$brief")" \
  && grep -qF 'gives no verdict: it is `Verdict: merge.` or `Verdict: call.`' <<<"$unread" \
  && grep -qF "the merge agent's answer is of ${base:0:12}, and the proposal is ${tip:0:12} now" <<<"$superseded" \
  && [ "$(field '(d["tip"], d["base"], d["facts"]["base"], d["facts"]["moved"], d["brief"].rsplit("/", 1)[-1], d["answer"].rsplit("/", 1)[-1])' <<<"$brief")" \
    = "('$tip', '$base', '$base', None, 'merge-brief-${tip:0:12}-${base:0:12}.md', 'merge-answer-${tip:0:12}-${base:0:12}.md')" ] \
  && grep -qF "\"tip\": \"$tip\"" "$(field 'd["brief"]' <<<"$brief")" && grep -qF "no brief of ${tip:0:12} on that base was written" <<<"$unnamed" \
  && [ "$(field '(d["verdict"], d["calls"], d["by"])' <<<"$called")" = "('merge', True, 'claude/opus:high')" ] && grep -q '^Verdict: merge\.' "$SHOP/.lem/state/tasks/first-change/merge-review.md" \
  && grep -q '"event": "merge.review", "task": "first-change", "verdict": "merge", "calls": true, "by": "claude/opus:high"' "$SHOP/.lem/state/events.jsonl" \
  && grep -qF 'branch.land is "owner"' <<<"$err" && [ "$(git -C "$ORIGIN" rev-parse main)" = "$(git -C "$SHOP" rev-parse main)" ] && [ "$(status first-change)" = open ]; then
  pass "the merge agent's brief names its standing text by its place in the plugin, found through lem version, and no folder of the Lem that wrote it, the seat that starts it, the tip, the base and their own brief and answer files, and the facts of the task, with nothing moved, no picture of a task that took none and the two ways the owner tries the branch; a reply with no verdict, of a brief of another tip or of a base no brief named, is refused, one with it is merge-review.md and an event; where the settings say that the owner merges, the review calls him and the merge agent merges nothing"
else
  fail "the merge review with branch.land = owner: $brief / $unread / $superseded / $unnamed / $called / $err"
fi
shop_settings agent keep
err=$(land --repo "$SHOP" merge first-change --by owner --message "fix: x" 2>&1) && code=0 || code=$?
if [ "$code" = 1 ] && grep -qF 'branch.history is "keep": the branch'"'"'s own commits land, so --message has nothing to name' <<<"$err"; then
  pass "a commit subject is refused when the branch's own commits land"
else
  fail "land --message with history = keep: $code $err"
fi
# The base moves after the gate ran: by any file, the merge waits for the merge agent's read of what moved.
other=$WORK/other
git clone -q "$ORIGIN" "$other" && ident "$other"
echo late > "$other/late.txt" && git -C "$other" add -A && git -C "$other" commit -q -m "feat: late" && git -C "$other" push -q origin main
err=$(land --repo "$SHOP" merge first-change --by owner 2>&1 || true)
if [ "$(status_of land --repo "$SHOP" merge first-change --by owner)" = 1 ] && grep -q "moved after the checks ran, by files (late.txt)" <<<"$err" \
  && grep -q "A fresh merge agent reads what moved: .lem land merge-review first-change. writes its brief" <<<"$err" && ! grep -q "lem land start" <<<"$err" && [ "$(status first-change)" = open ]; then
  pass "merge refuses when the base moved by a file, and names the merge agent's read of what moved as the next step"
else
  fail "land after the base moved: $err"
fi
# landed again, as after a read that says another round
land --repo "$SHOP" start first-change >/dev/null && land --repo "$SHOP" base first-change >/dev/null
if [ "$(status first-change)" = landing ] && [ "$(kept first-change gated)" = None ] && [ "$(status_of land --repo "$SHOP" merge first-change --by owner)" = 1 ] \
  && [ "$(status_of land --repo "$SHOP" propose first-change --title x --notes "$NOTES")" = 1 ]; then
  pass "an open task takes the landing line again, and a new base forgets the gate's result, so nothing is proposed or landed before a new one"
else
  fail "base after a green gate keeps the result"
fi
land --repo "$SHOP" checks first-change >/dev/null
out=$(land --repo "$SHOP" read first-change)
if [ "$(field '(d["due"], d["why"])' <<<"$out")" = "('none', 'round 1 reviewed this change and left no must-fix')" ] && propose first-change && [ "$(status first-change)" = open ]; then
  pass "a rebase that changes nothing of the change does not undo its review"
else
  fail "the read after a rebase: $out"
fi
echo more >> "$other/docs/guide.md" && git -C "$other" add -A && git -C "$other" commit -q -m "docs: more" && git -C "$other" push -q origin main
docs_err=$(land --repo "$SHOP" merge first-change --by owner 2>&1 || true)
land --repo "$SHOP" start first-change >/dev/null && land --repo "$SHOP" base first-change >/dev/null && land --repo "$SHOP" checks first-change >/dev/null
land --repo "$SHOP" read first-change >/dev/null
again=$(land --repo "$SHOP" propose first-change --title "fix: first-change" --notes "$NOTES")
# the merge review of the tip before carries onto the new tip, with its call of the owner as the settings say now,
# and the owner's merge that the moved base refused stands for it: the server's merge runs it after the re-check
review=$(kept first-change merge_review | "$PY" -c 'import ast, sys; d = ast.literal_eval(sys.stdin.read()); print((d["verdict"], d["calls"], d["tip"] == sys.argv[1], "carried_from" in d))' "$(kept first-change proposed)")
out=$(land --repo "$SHOP" merge first-change --by owner --via server --standing)
if grep -q "moved after the checks ran, by files (docs/guide.md)" <<<"$docs_err" && grep -qF "the owner's merge stands, and goes through after a read that says \`Base: safe.\`" <<<"$docs_err" \
  && [ "$(field '(d["merge_review"], d["owner_merge"].startswith("stands"))' <<<"$again")" = "('carried', True)" ] && [ "$review" = "('merge', False, True, True)" ] \
  && [ "$(kept first-change relands)" = 2 ] && grep -q '"event": "merge.stands", "task": "first-change", "by": "owner"' "$SHOP/.lem/state/events.jsonl" \
  && [ "$(field '(d["pull_request"]["number"], d["left_behind"])' <<<"$out")" = "(1, None)" ] && [ "$(status first-change)" = landed ] \
  && [ "$(kept first-change merged_by)" = "{'by': 'owner', 'via': 'server', 'after': 'a re-check'}" ] \
  && [ "$(git -C "$ORIGIN" log -1 --format=%s main)" = "fix: first-change" ] && [ "$(git -C "$SHOP" rev-parse main)" = "$(git -C "$ORIGIN" rev-parse main)" ] \
  && [ -f "$SHOP/ok.txt" ] && [ -f "$SHOP/late.txt" ] \
  && [ "$began" = "$version" ] && [ -n "$prior" ] && [ "$(cat "$SHOP/.lem/state/tasks/first-change/release.txt")" = "$prior" ] \
  && ! grep -q '"event": "release.stop", "task": "first-change"' "$SHOP/.lem/state/events.jsonl"; then
  pass "a base that moved by a document is refused too; landed again, the merge review carries onto the new tip and the owner's merge that the base refused stands, so it merges through GitHub after the re-check: the main checkout fast-forwarded, the state landed; the task began on the release before this one, as its mark says, and Lem stopped none of its steps"
else
  fail "land: $again / $review / $out / began on $began, the release before is $prior"
fi
# A clean that was cut off after the worktree went: the next run still knows the branch.
git -C "$SHOP" worktree remove "$SHOP/.lem/worktrees/first-change"
out=$(land --repo "$SHOP" clean first-change)
if [ "$(field '(d["worktree"], d["branch"])' <<<"$out")" = "(False, 'fix/first-change')" ] && [ -z "$(git -C "$SHOP" branch --list fix/first-change)" ] \
  && [ -d "$SHOP/.lem/state/tasks/first-change" ] && [ "$(field '(d["worktree"], d["branch"])' <<<"$(land --repo "$SHOP" clean first-change)")" = "(False, None)" ]; then
  pass "clean removes the landed task's branch when its worktree is already gone, keeps the task's state, and a third run finds nothing left"
else
  fail "land clean after the worktree went: $out"
fi
err=$(land --repo "$SHOP" clean second-change 2>&1) && code=0 || code=$?
if [ "$code" = 1 ] && grep -qF "only a landed, dropped or answered task loses its worktree" <<<"$err" && [ -d "$SHOP/.lem/worktrees/second-change" ]; then
  pass "clean refuses a task that has not landed"
else
  fail "clean before the landing: $code $err"
fi
# An answered task loses its worktree as a dropped one does, and its branch stays: it may hold the test that reproduced the bug.
AC=$WORK/answered-clean
git init -q -b main "$AC" && git -C "$AC" config user.name t && git -C "$AC" config user.email t@t
project --repo "$AC" init --base main >/dev/null
git -C "$AC" add -A && git -C "$AC" commit -q -m "chore: start"
acd=$(project --repo "$AC" task-dir refund-shows-zero --ask "invoices show 0 after a refund")
act=$(project --repo "$AC" worktree-dir refund-shows-zero)
git -C "$AC" worktree add -q -b fix/refund-shows-zero "$act" main
# shellcheck disable=SC2016 # the test file's own text, with its quotes
mkdir -p "$act/tests" && echo 'test "$(cat total)" = 0' > "$act/tests/refund.sh"
git -C "$act" add -A && git -C "$act" commit -q -m "test: an invoice after a refund shows what is left to pay"
project --repo "$AC" state refund-shows-zero building "an investigator reproduces the bug and finds its cause" "investigation: bug" "type: fix, because the ask says the total is wrong today" >/dev/null
printf '%s\n' '# Investigation' '' 'Reproduced: yes.' > "$acd/investigation.md"
project --repo "$AC" log refund-shows-zero investigation type=fix call=not-a-bug "line=the invoice shows what is left to pay" where=billing/invoice.py:total reproduced:=true >/dev/null
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
land --repo "$SHOP" base second-change >/dev/null && polish_in "$SHOP" second-change
out=$(land --repo "$SHOP" checks second-change 2>/dev/null || true)
if [ "$(status_of land --repo "$SHOP" checks second-change)" = 1 ] && [ "$(field '(d["green"], [c["exit"] for c in d["commands"]], "criteria" in d)' <<<"$out")" = "(False, [1, 0], False)" ] \
  && [ "$(kept second-change gated)" = None ] && [ "$(status_of land --repo "$SHOP" read second-change)" = 1 ] && [ "$(status_of land --repo "$SHOP" propose second-change --title x --notes "$NOTES")" = 1 ]; then
  pass "a red gate exits 1 with each command's result, the later checks do not run, and nothing is read or proposed on it"
else
  fail "red gate: $out"
fi
git -C "$tree" revert --no-edit HEAD >/dev/null
shop_settings agent squash
land --repo "$SHOP" checks second-change >/dev/null
out=$(land --repo "$SHOP" read second-change)
under=$(land --repo "$SHOP" read second-change --record "$(record second-change 1 '{"kind": "round", "ran": [{"name": "correctness", "why": "a line of the app changes"}], "answered": ["codex"]}')" 2>&1 || true)
dropped=$(land --repo "$SHOP" read second-change --record "$(record second-change 1 '{"kind": "full", "ran": [{"name": "default", "why": "the request is careful"}], "left_out": [{"name": "security", "why": "no input is read"}], "answered": ["codex"]}')" 2>&1 || true)
next=$(land --repo "$SHOP" read second-change --record "$(record second-change 1 '{"kind": "full", "ran": [{"name": "default", "why": "the request is careful"}], "answered": ["codex", "claude"], "silent": [{"name": "gemini", "why": "at capacity"}], "must_fix": 1}')" | field '(d["recorded"]["verdict"], d["next"])')
err=$(land --repo "$SHOP" propose second-change --title x --notes "$NOTES" 2>&1 || true)
if [ "$(field '(d["due"], d["floor"], d["why"])' <<<"$out")" = "('review', 'full', 'the request is careful: the owner says so')" ] \
  && grep -q "this change gets the project's full set at the least (the request is careful: the owner says so), and the record says a review round with the profiles that fit" <<<"$under" \
  && grep -q "the project's full set leaves no profile out" <<<"$dropped" && grep -qF 'write "left_out": [] on a full review' <<<"$dropped" \
  && [ "$next" = "('must-fix', 'review')" ] \
  && grep -q "a review is due before anything is proposed, the project's full set at the least" <<<"$err"; then
  pass "a request the owner called careful gets the project's full set: a record of less is refused, one that leaves a profile out too; a round in which one source did not answer counts, and a must-fix is followed by another round"
else
  fail "the read of a careful request: $out / $next / $err"
fi
echo '# and no other word' >> "$tree/tests/second-change.sh" && git -C "$tree" commit -q -am "fix: what the round found"
err=$(land --repo "$SHOP" read second-change 2>&1 || true)
land --repo "$SHOP" checks second-change >/dev/null
out=$(land --repo "$SHOP" read second-change)
land --repo "$SHOP" read second-change --record "$(record second-change 2 '{"kind": "full", "ran": [{"name": "default", "why": "the request is careful"}], "answered": ["codex", "claude", "gemini"], "nit": 2}')" >/dev/null
if grep -q "no green check is on record for this tip" <<<"$err" && [ "$(field '(d["due"], d["floor"], d["round"], len(d["reads"]))' <<<"$out")" = "('review', 'full', 2, 1)" ]; then
  pass "a fix is reviewed only after the machine checks ran on it, and the second round knows the first"
else
  fail "the second round: $err / $out"
fi
# Careful only by the owner's word, given after its plan: no talk was due, so none is asked for, and the text says why it had none.
err=$(land --repo "$SHOP" propose second-change --title "fix(app): both lines stay" --notes "$NOTES" 2>&1 || true)
printf '%s\n' '' '## Migration' '' 'none' >> "$NOTES"
land --repo "$SHOP" propose second-change --title "fix(app): both lines stay" --notes "$NOTES" >/dev/null
text=$SHOP/.lem/state/tasks/second-change/pr.md
if grep -q "^- no plan talk: the request became careful after its plan, by the owner's word$" "$text" \
  && [ "$(sed -n '/^## Checks$/,/^## Decisions of the build$/p' "$text" | grep -c 'plan talk')" = 1 ] && [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] \
  && ! grep -q '"event": "careful.missed", "task": "second-change"' "$SHOP/.lem/state/events.jsonl"; then
  pass "a request the owner called careful after its plan is proposed with no plan talk, its checks say in words that it had none and why, and that is no cause of not green"
else
  fail "a request careful by the owner's later word: $(cat "$text" 2>/dev/null)"
fi
agent=$(land --repo "$SHOP" merge second-change --by merger --message "fix(app): both lines stay" 2>&1 || true)
if grep -q "the notes lack ## Migration" <<<"$err" && grep -qxF -- "- careful: yes, the owner says so; the review says no: $NOT_CAREFUL" "$text" && [ "$(head -1 "$text" | cut -c1-10)" = '**Green.**' ] \
  && grep -q "^- the review, round 1 (the project's full set; answered: codex, claude; no answer from gemini (at capacity)): must-fix, 1 must-fix, 0 should, 0 nit$" "$text" \
  && grep -q '^  - ran default: the request is careful$' "$text" \
  && grep -q "^- the review, round 2 (the project's full set; answered: codex, claude, gemini): clean, 0 must-fix, 0 should, 2 nit$" "$text" \
  && grep -q "a careful request is merged by the owner, whatever the settings say" <<<"$agent" && [ "$(status second-change)" = open ]; then
  pass "the notes of a careful request say whether it holds a migration, its text shows both rounds with who answered and who did not, and the merge agent does not merge it though it is green"
else
  fail "a careful request at the proposal: $err / $agent / $(cat "$text" 2>/dev/null)"
fi
err=$(land --repo "$SHOP" merge second-change --by owner 2>&1) && code=0 || code=$?
if [ "$code" = 1 ] && grep -qF 'branch.history is "squash": pass --message' <<<"$err"; then pass "one commit for the branch needs its subject"; else fail "squash without a message: $code $err"; fi
before=$(git -C "$ORIGIN" rev-parse main)
# GitHub refuses the merge by a rule of its own: its line is kept for the owner, and the task waits as open
refused=$(GH_REFUSE="Pull request is not mergeable: the base branch policy prohibits the merge" land --repo "$SHOP" merge second-change --by owner --message "fix(app): both lines stay" 2>&1 || true)
waits=$(project --repo "$SHOP" waiting | field 'next(p["merge_refused"]["said"] for p in d["pull_requests"] if p["task"] == "second-change")')
out=$(land --repo "$SHOP" merge second-change --by owner --message "fix(app): both lines stay")
if [ "$(git -C "$ORIGIN" rev-list --count "$before..main")" = 1 ] && [ "$(git -C "$ORIGIN" log -1 --format=%s main)" = "fix(app): both lines stay" ] \
  && [ "$(git -C "$ORIGIN" show main:app.txt)" = both ] && [ "$(git -C "$ORIGIN" rev-parse 'main^{tree}')" = "$(kept second-change tree)" ] && [ "$(status second-change)" = landed ] \
  && grep -qF "GitHub refused the merge of https://github.com/acme/shop/pull/2: Pull request is not mergeable: the base branch policy prohibits the merge" <<<"$refused" \
  && [ "$waits" = "Pull request is not mergeable: the base branch policy prohibits the merge" ] \
  && grep -q '"event": "merge.refused", "task": "second-change", "by": "owner"' "$SHOP/.lem/state/events.jsonl"; then
  pass "a merge GitHub refuses says GitHub's line, keeps it for the list of what waits for the owner, and lands nothing; on his word, with history = squash, the branch then lands as one commit, and its tree is the tree the gate passed on"
else
  fail "squash landing: $refused / $waits / $out"
fi
land --repo "$SHOP" clean second-change >/dev/null
printf '%s\n' '## Decisions' '' 'none' '' '## Left open' '' 'none' '' '## Worth a look' '' '- the one line of the file.' '' '## Filed in the backlog' '' 'none' '' '## Not done' '' 'none' > "$NOTES"

# A plan of four tasks is large: it needs a plan talk too, and the talk's event has one form. The
# event log already holds the talk of another task, which does not count for this one.
shop_settings agent keep
open_task four-tasks five.txt five
tree=$(project --repo "$SHOP" worktree-dir four-tasks)
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("1. The change.", "1. The change.\n2. Its test.\n3. Its page.\n4. Its note."))' "$tree/docs/plans/2026-11-15-four-tasks.md"
git -C "$tree" commit -q -am "docs: four tasks"
checked four-tasks
land --repo "$SHOP" read four-tasks --record "$(record four-tasks 1 '{"kind": "round", "ran": [{"name": "correctness", "why": "four tasks change the app"}], "answered": ["codex"]}')" >/dev/null
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
  && ! grep -q '"event": "plan.talk", "task": "four-tasks"' "$SHOP/.lem/state/events.jsonl" \
  && [ "$(grep -c '"event": "plan.talk", "task": "second-change", "reviewer": "codex", "turns": 4' "$SHOP/.lem/state/events.jsonl")" = 1 ]; then
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
  && [ "$(grep -c '"event": "plan.talk", "task": "four-tasks"' "$SHOP/.lem/state/events.jsonl")" = 5 ] \
  && [ "$(grep -c '"event": "plan.talk.start", "task": "four-tasks"' "$SHOP/.lem/state/events.jsonl")" = 1 ]; then
  pass "a talk's counts agree: each question of the list ends settled or open, a design choice is an open one, and a question gets one repair at most; a talk over its bound of 4 × questions + 2 turns, or with more decisions two questions named than design choices, is written as it ran, with the bound the log adds; a talk of no question and two turns has nothing raised after its list; the start of a talk names its reviewer and nothing else, and a refused record writes nothing"
else
  fail "the counts of a plan talk: $lost / $undesigned / $overrepaired / $endless / $unshared / $bounded / $lone / $quiet_raised / $raised_late / $quiet / $startless / $overstarted / $started"
fi
project --repo "$SHOP" log four-tasks plan.talk reviewer=claude turns:=3 questions:=1 settled:=1 open:=0 repaired:=0 design:=0 unargued:=0 root:=0 layer:=0 shared:=0 >/dev/null
project --repo "$SHOP" log four-tasks plan.talk reviewer=codex turns:=23 questions:=5 settled:=4 open:=1 repaired:=3 design:=1 unargued:=2 root:=2 layer:=1 shared:=0 >/dev/null
# the same event with one count more, which Lem has no words for: a count added to the event later needs no change of the landing
"$PY" -c 'import json, sys; p = sys.argv[1]; talk = json.loads(open(p).read().splitlines()[-1]); talk["rounds"] = 2; open(p, "a").write(json.dumps(talk) + "\n")' "$SHOP/.lem/state/events.jsonl"
out=$(land --repo "$SHOP" propose four-tasks --title "fix: five" --notes "$NOTES")
text=$SHOP/.lem/state/tasks/four-tasks/pr.md
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
"$PY" -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("\n## Acceptance criteria", "careful: yes, a price is rounded here.\n\n## Acceptance criteria", 1))' "$tree/docs/plans/2026-11-15-careful-plan.md"
git -C "$tree" commit -q -am "docs: the plan is careful"
checked careful-plan
land --repo "$SHOP" read careful-plan --record "$(record careful-plan 1 '{"kind": "full", "ran": [{"name": "default", "why": "the plan says careful"}], "answered": ["codex"]}')" >/dev/null
talkless=$(land --repo "$SHOP" propose careful-plan --title "fix: six" --notes "$MIG" 2>&1 || true)
if grep -q "the plan says that the request is careful, so its defender and the reviewer talk its plan through in the plan talk's companion before any code (.stages/talk.md.)" <<<"$talkless" \
  && grep -q "the event log has no .plan.talk. of careful-plan. The defender writes it after the talk" <<<"$talkless" \
  && grep -qF "lem project log careful-plan plan.talk reviewer=AGENT turns:=N questions:=N settled:=N open:=N repaired:=N design:=N unargued:=N root:=N layer:=N shared:=N\`" <<<"$talkless" \
  && grep -qF "for a plan that had no talk, the task's lead opens the talk first, as \`stages/talk.md\` says" <<<"$talkless" \
  && [ ! -f "$SHOP/.lem/state/tasks/careful-plan/pr.md" ] && [ "$(status careful-plan)" = landing ]; then
  pass "a request whose plan says careful is not proposed while its event log has no plan talk, and the refusal names the plan stage's step, the talk the task's lead opens, and the event its defender writes in the form project.py takes"
else
  fail "a careful plan with no plan talk: $talkless"
fi
project --repo "$SHOP" log careful-plan plan.talk reviewer=codex turns:=6 questions:=3 settled:=2 open:=1 repaired:=1 design:=0 unargued:=0 root:=1 layer:=0 shared:=0 >/dev/null
# the request came from a bug: its investigation before the build found the cause and its place
project --repo "$SHOP" log careful-plan investigation type=fix call=full "line=the total adds the refund as a payment" where=billing/invoice.py:total reproduced:=true >/dev/null
land --repo "$SHOP" propose careful-plan --title "fix: six" --notes "$MIG" >/dev/null
text=$SHOP/.lem/state/tasks/careful-plan/pr.md
if [ "$(grep 'plan talk' "$text" || true)" = "- the plan talk: codex argued the plan with its defender, 6 turns; 2 positions settled by the two, 1 left open; 3 questions in the reviewer's first list, 1 repaired by the defender, 0 of the open ones a design choice, 0 raised after the list and not argued, 1 repaired at the cause, 0 layers over a cited decision, 0 decisions two questions named" ] \
  && [ "$(sed -n '/^## Checks$/,/^## Decisions of the build$/p' "$text" | grep -c 'plan talk')" = 1 ] && grep -qxF -- "- careful: yes, the plan says so; the review says no: $NOT_CAREFUL" "$text" \
  && [ "$(status careful-plan)" = open ]; then
  pass "after its plan talk a request whose plan says careful is proposed, and the checks of its text say who argued the plan with its defender, the turns, the positions settled and left open, and the other counts of the talk"
else
  fail "the plan talk in the text of a careful plan: $(cat "$text" 2>/dev/null)"
fi
# A request that came from a bug names, in its checks, the cause the investigation before the build found and where.
# That a question's answer, or no investigation, gives no such line is a case of tests/unit/test_land_text.py.
if grep -qxF -- "- the cause, as the investigation before the build found it: the total adds the refund as a payment (billing/invoice.py:total)" "$text" \
  && ! grep -qF "$SHOP" "$text" \
  && [ "$(sed -n '/^## Checks$/,/^## Decisions of the build$/p' "$text" | grep -c '^- the cause, as the investigation')" = 1 ]; then
  pass "a request that came from a bug names in its checks the cause its investigation found, with its place and no path of this machine"
else
  fail "the cause of a bug in the text: $(cat "$text" 2>/dev/null)"
fi
project --repo "$SHOP" state careful-plan dropped "the test is over" >/dev/null

# A file that moved on the base counts as a change of the path it left.
open_task moved-file extra.txt four
checked moved-file && read_clean moved-file && propose moved-file
git -C "$other" pull -q origin main && git -C "$other" mv late.txt docs/late.txt && git -C "$other" commit -q -m "docs: move late" && git -C "$other" push -q origin main
err=$(land --repo "$SHOP" merge moved-file --by owner 2>&1 || true)
if [ "$(status_of land --repo "$SHOP" merge moved-file --by owner)" = 1 ] && grep -q "by files (.*late.txt" <<<"$err" && [ "$(status moved-file)" = open ]; then
  pass "a file moved on the base counts as a change of the path it left, and the merge is refused"
else
  fail "a rename on the base: $err"
fi
checked moved-file && propose moved-file
# The main checkout has a commit of its own, so it cannot follow origin after the merge.
git -C "$SHOP" commit -q --allow-empty -m "chore: only here"
out=$(land --repo "$SHOP" merge moved-file --by owner)
if [ "$(status moved-file)" = landed ] && [ "$(git -C "$ORIGIN" rev-parse main)" = "$(git -C "$SHOP/.lem/worktrees/moved-file" rev-parse HEAD)" ] \
  && [ "$(field '"did not follow origin/main" in d["left_behind"] and "brings it up" not in d["left_behind"]' <<<"$out")" = True ]; then
  pass "after the merge on GitHub the state is landed, and a main checkout that cannot follow is reported with git's own reason"
else
  fail "a merge the main checkout cannot follow: $out"
fi
out=$(land --repo "$SHOP" merge moved-file --by owner 2>&1 || true)
if grep -q "is 'landed', not .open." <<<"$out"; then pass "a landed task does not land again"; else fail "land twice: $out"; fi
git -C "$SHOP" reset -q --hard origin/main
# the reset took back the owner's edit of the settings in the main checkout; it is made again
shop_settings agent keep
out=$(land --repo "$SHOP" clean moved-file)
if [ "$(field '(d["worktree"], d["branch"])' <<<"$out")" = "(True, 'fix/moved-file')" ] && [ ! -e "$SHOP/.lem/worktrees/moved-file" ] && [ -z "$(git -C "$SHOP" branch --list fix/moved-file)" ]; then
  pass "clean removes a landed task's worktree and its branch in one run"
else
  fail "land clean: $out"
fi

# Two rounds at most. A request that is not careful and whose read found a must-fix gets a round after the fix, and one
# that is not clean after the second round goes to the owner as not green.
open_task not-clean nc.txt seven
checked not-clean
# A run that is cut off before the review is written down leaves nothing, the next run writes it
# down once, and the same record sent again is refused: one review never takes two rounds. A copy
# of the package whose project.py refuses the `review` event stands in for the kill. The copy is in a folder of the
# plugin's shape, whose plugin.json names this Lem's release, which each step reads (lem_release).
CUT=$WORK/cut/src/lem
mkdir -p "$WORK/cut/src" "$WORK/cut/.claude-plugin" && cp "$PWD/.claude-plugin/plugin.json" "$WORK/cut/.claude-plugin/"
cp -R "$PWD/src/lem" "$CUT"
printf '%s\n' 'import runpy, sys' 'if "review" in sys.argv: sys.exit("project.py: cut off")' \
  "sys.argv[0] = '$PWD/src/lem/project.py'" "runpy.run_path(sys.argv[0], run_name='__main__')" > "$CUT/project.py"
first=$(record not-clean 1 '{"kind": "read", "answered": ["codex"], "must_fix": 2}')
cut_off=$(status_of "$PY" -B "$CUT/__main__.py" land --repo "$SHOP" read not-clean --record "$first")
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
land --repo "$SHOP" checks not-clean >/dev/null
out=$(land --repo "$SHOP" read not-clean)
again=$(land --repo "$SHOP" read not-clean --record "$(clean not-clean 2)" 2>&1 || true)
land --repo "$SHOP" read not-clean --record "$(record not-clean 2 '{"kind": "round", "ran": [{"name": "correctness", "why": "a file of the app changes"}], "left_out": [{"name": "security", "why": "no input from outside is read"}], "answered": ["codex"], "must_fix": 1}')" >/dev/null
echo nine > "$tree/nc3.txt" && git -C "$tree" add -A && git -C "$tree" commit -q -m "fix: the round's finding"
land --repo "$SHOP" checks not-clean >/dev/null
third=$(land --repo "$SHOP" read not-clean)
fourth=$(land --repo "$SHOP" read not-clean --record "$(record not-clean 3 '{"kind": "round", "ran": [{"name": "correctness", "why": "a file of the app changes"}], "answered": ["codex"]}')" 2>&1 || true)
proposed=$(land --repo "$SHOP" propose not-clean --title "fix: not-clean" --notes "$NOTES")
text=$SHOP/.lem/state/tasks/not-clean/pr.md
agent=$(land --repo "$SHOP" merge not-clean --by merger 2>&1 || true)
why="two rounds reviewed it: the last one left 1 must-fix, and nobody reviewed what changed after it"
if [ "$(field '(d["due"], d["floor"], d["why"])' <<<"$out")" = "('review', 'round', 'an earlier review found a must-fix: after its fix a round reviews the change')" ] && grep -q "this change gets a review round with the profiles that fit at the least" <<<"$again" \
  && [ "$(field '(d["due"], d["why"])' <<<"$third")" = "('owner', '$why')" ] && grep -q "no review is due: two rounds reviewed it" <<<"$fourth" \
  && [ "$(field '(d["green"], d["not_green"])' <<<"$proposed")" = "(False, ['$why'])" ] && [ "$(kept not-clean title)" = "fix: not-clean" ] \
  && [ "$(sed -n 1p "$text")" = '**Not green.**' ] && [ "$(sed -n 3p "$text")" = "- $why" ] && grep -q '^  - left out security: no input from outside is read$' "$text" \
  && grep -q "^not green: $why$" "$SHOP/.lem/state/tasks/not-clean/state.md" \
  && grep -q "the request is not green ($why), so the owner merges it" <<<"$agent"; then
  pass "a request that is not careful with a must-fix gets a round after its fix, with each profile it ran or left out and why; after two rounds no third is taken, the request is proposed as not green, which its first lines say with the reason, and the merge agent does not merge it"
else
  fail "two rounds at most: $out / $again / $third / $fourth / $proposed / $agent / $(sed -n 1,4p "$text" 2>/dev/null)"
fi
land --repo "$SHOP" merge not-clean --by owner >/dev/null
if [ "$(status not-clean)" = landed ] && [ "$(git -C "$ORIGIN" show main:nc3.txt)" = nine ]; then pass "the owner's word lands a request that is not green"; else fail "the owner lands a request that is not green"; fi
land --repo "$SHOP" clean not-clean >/dev/null

# No gate command, and a protected branch.
open_task third-change note.txt three
shop_lines '[branch]' 'base = "main"' 'history = "keep"' 'land = "agent"'
err=$(land --repo "$SHOP" start third-change 2>&1 || true)
if [ "$(status_of land --repo "$SHOP" start third-change)" = 1 ] && grep -q "no command in its checks" <<<"$err" && [ "$(status third-change)" = blocked ]; then
  pass "a project with no gate command lands nothing, and the task is blocked instead of holding the landing line"
else
  fail "start with no gate: $err"
fi
# with a command of the checks, so that the protected base is the one reason left to refuse the step
shop_lines '[branch]' 'base = "release"' 'history = "keep"' 'land = "agent"' 'protected = ["release"]' '[checks]' 'commands = ["true"]'
err=$(land --repo "$SHOP" start third-change 2>&1) && code=0 || code=$?
if [ "$code" = 1 ] && grep -qF "protected" <<<"$err" && [ "$(status third-change)" = blocked ]; then pass "no step runs toward a branch the settings refuse"; else fail "land toward a protected base: $code $err"; fi
# The first task of a new repository sets up the checks: the main checkout's settings have no gate
# command, and the task's branch adds them to its own .lem/settings.toml. That gate gates the task,
# and its pull request is not green for it, so that a person reads the checks once. A branch that
# changes a gate the main checkout already has is gated by the main checkout's, as before.
FG=$WORK/first-gate
git init -q -b main "$FG" && ident "$FG"
project --repo "$FG" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' 'land = "agent"' > "$FG/.lem/settings.toml"
git -C "$FG" add -A && git -C "$FG" commit -q -m "chore: start" && on_github "$FG"
task_in "$FG" set-up-checks c.txt checked
read_in "$FG" set-up-checks
tree=$(project --repo "$FG" worktree-dir set-up-checks)
printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' 'land = "agent"' '[checks]' 'commands = ["echo 3 passed"]' > "$tree/.lem/settings.toml"
git -C "$tree" commit -q -am "chore: the checks"
brought_start=$(land --repo "$FG" start set-up-checks 2>&1 || true)
brought_gate=$(land --repo "$FG" base set-up-checks >/dev/null 2>&1 && polish_in "$FG" set-up-checks && land --repo "$FG" checks set-up-checks 2>&1 || true)
brought_floor=$(land --repo "$FG" read set-up-checks | field '(d["floor"], d["why"])' 2>&1 || true)
land --repo "$FG" read set-up-checks --record "$(record set-up-checks 1 '{"kind": "full", "ran": [{"name": "default", "why": "the checks come with it"}], "answered": ["codex"]}')" >/dev/null 2>&1 || true
land --repo "$FG" propose set-up-checks --title "chore: the checks" --notes "$MIG" >/dev/null 2>&1 || true
brought_agent=$(land --repo "$FG" merge set-up-checks --by merger 2>&1 || true)
text=$FG/.lem/state/tasks/set-up-checks/pr.md
FG2=$WORK/kept-gate
git init -q -b main "$FG2" && ident "$FG2"
project --repo "$FG2" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' 'land = "agent"' '[checks]' 'commands = ["echo main passed"]' > "$FG2/.lem/settings.toml"
git -C "$FG2" add -A && git -C "$FG2" commit -q -m "chore: start" && on_github "$FG2"
task_in "$FG2" other-checks k.txt kept
read_in "$FG2" other-checks
tree=$(project --repo "$FG2" worktree-dir other-checks)
printf '%s\n' '[branch]' 'base = "main"' 'history = "keep"' 'land = "agent"' '[checks]' 'commands = ["false"]' > "$tree/.lem/settings.toml"
git -C "$tree" commit -q -am "chore: other checks"
kept_gate=$(land --repo "$FG2" start other-checks >/dev/null 2>&1 && land --repo "$FG2" base other-checks >/dev/null 2>&1 && polish_in "$FG2" other-checks && land --repo "$FG2" checks other-checks 2>&1 || true)
kept_floor=$(land --repo "$FG2" read other-checks | field '(d["floor"], d["why"])' 2>&1 || true)
land --repo "$FG2" read other-checks --record "$(record other-checks 1 '{"kind": "full", "ran": [{"name": "default", "why": "the checks change"}], "answered": ["codex"]}')" >/dev/null 2>&1 || true
land --repo "$FG2" propose other-checks --title "chore: other checks" --notes "$MIG" >/dev/null 2>&1 || true
gate_why="the change edits [checks] of .lem/settings.toml, Lem's own settings, which say for every later task what is careful, what the checks run, who merges and where a task lands"
if [ "$(status_in "$FG" set-up-checks)" = open ] && ! grep -q "no command in its checks" <<<"$brought_start" \
  && [ "$(field '[(c["command"], c["last"]) for c in d["commands"]]' <<<"$brought_gate" 2>/dev/null)" = "[('echo 3 passed', '3 passed')]" ] \
  && [ "$(sed -n 1p "$text" 2>/dev/null)" = '**Not green.**' ] \
  && [ "$(sed -n 3p "$text")" = "- the checks came with this change: the main checkout's settings name no command of the checks, and the branch's .lem/settings.toml brings \`echo 3 passed\`. Read the checks once: every later task is checked by them" ] \
  && grep -qF "a careful request is merged by the owner, whatever the settings say ($gate_why)" <<<"$brought_agent" \
  && [ "$brought_floor" = "('full', \"the request is careful: $gate_why\")" ] && [ "$kept_floor" = "('full', \"the request is careful: $gate_why\")" ] \
  && [ "$(field '[(c["command"], c["last"]) for c in d["commands"]]' <<<"$kept_gate" 2>/dev/null)" = "[('echo main passed', 'main passed')]" ] \
  && [ "$(sed -n 1p "$FG2/.lem/state/tasks/other-checks/pr.md" 2>/dev/null | cut -c1-10)" = '**Green.**' ] \
  && grep -qxF -- "- careful: yes, $gate_why; the review says no: $NOT_CAREFUL" "$FG2/.lem/state/tasks/other-checks/pr.md"; then
  pass "a first task that brings the gate on its own branch, while the main checkout's settings have none, is gated by it and is not green for it; a branch that changes a gate the main checkout has is gated by the main checkout's; either is careful by the script, which says why, so it gets the full set and the owner merges it"
else
  fail "a gate that comes with the change: $brought_start / $brought_gate / $brought_floor / $brought_agent / $kept_gate / $kept_floor / $(cat "$text" 2>/dev/null)"
fi
project --repo "$FG" state set-up-checks dropped "the test is over" >/dev/null
project --repo "$FG2" state other-checks dropped "the test is over" >/dev/null

# A base that moved after the checks: a fresh merge agent reads what moved beside the change, and a move it calls
# safe merges with no new run of the checks; one it calls another round lands the task again first.
MB=$WORK/moved-base
git init -q -b main "$MB" && ident "$MB"
# the repository has no origin before its first commit, which init says on stderr
project --repo "$MB" init --base main >/dev/null 2>&1
# mb_settings LAND HISTORY: the moved-base shop's settings, an edit of the owner's in its main checkout
mb_settings() { printf '%s\n' '[branch]' 'base = "main"' "land = \"$1\"" "history = \"$2\"" '[checks]' 'commands = ["true"]' > "$MB/.lem/settings.toml"; }
mb_settings agent squash
mkdir -p "$MB/docs" && echo board > "$MB/docs/board.md" && printf '%s\n' 1 2 3 4 5 6 7 8 9 10 > "$MB/shared.txt"
git -C "$MB" add -A && git -C "$MB" commit -q -m "chore: start" && on_github "$MB"
MBO=$MB.origin.git
MBX=$WORK/moved-base-other
git clone -q "$MBO" "$MBX" 2>/dev/null && ident "$MBX"
# mb_move FILE: another task's commit on origin's main, which appends a line to FILE; prints the new main
mb_move() {
  git -C "$MBX" pull -q --ff-only origin main && echo "move $(git -C "$MBX" rev-list --count HEAD)" >> "$MBX/$1"
  git -C "$MBX" add -A && git -C "$MBX" commit -q -m "docs: $1" && git -C "$MBX" push -q origin main && git -C "$MBX" rev-parse HEAD
}
# mb_task SLUG FILE: a task of the moved-base shop, ready; mb_land SLUG [RECORD] [NOTES]: from ready to its pull request,
# with a read that found nothing, or the review RECORD of its first attempt (JSON), and NOTES
mb_task() { task_in "$MB" "$1" "$2" yes && read_in "$MB" "$1"; }
MB_READ='{"kind": "read", "answered": ["codex"]}'
mb_land() {
  land --repo "$MB" start "$1" >/dev/null && land --repo "$MB" base "$1" >/dev/null && polish_in "$MB" "$1" && land --repo "$MB" checks "$1" >/dev/null \
    && land --repo "$MB" read "$1" --record "$(record "$1" 1 "${2:-$MB_READ}")" >/dev/null \
    && land --repo "$MB" propose "$1" --title "fix: $1" --notes "${3:-$NOTES}" >/dev/null
}
# mb_kept SLUG KEY PYTHON: what landing.json keeps under KEY, as `d`
mb_kept() { "$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])).get(sys.argv[2]); print(eval(sys.argv[3], {"d": d}))' "$MB/.lem/state/tasks/$1/landing.json" "$2" "$3"; }
# mb_body SLUG PYTHON: the pull request's text on GitHub (the stand-in's), as `d`
mb_body() { gh_prs "$MB" "(lambda d: $2)(d['prs'][str($(mb_kept "$1" pr 'd["number"]'))]['body'])"; }
mb_events() { grep "\"task\": \"$1\"" "$MB/.lem/state/events.jsonl" | grep -c "\"event\": \"$2\"" || true; }
# mb_logged SLUG EVENT PYTHON: each EVENT of the task in the event log, as `d`, in a list
mb_logged() { "$PY" -c 'import json, sys; print([eval(sys.argv[3], {"d": d}) for d in map(json.loads, open(sys.argv[1])) if d.get("task") == sys.argv[2] and d.get("event") == sys.argv[4]])' "$MB/.lem/state/events.jsonl" "$1" "$3" "$2"; }

# Safe: the read of m2 comes after main moved to m3, so it covers m2 alone and the merge on m3 waits for a new read;
# GitHub's refusal writes no line; a failed edit of the text after GitHub's merge leaves the task open, and `merged` writes it.
# The squash commit's body names the fix made on the way first and ends with the task.
fixed_line="- \`docs/board.md\` (abc1234): a sentence named a key the board no longer has"
cp "$NOTES" "$WORK/mb-safe-notes.md" && printf '%s\n' '' '## Fixed on the way' '' "$fixed_line" >> "$WORK/mb-safe-notes.md"
mb_task mb-safe safe.txt && mb_land mb-safe "$MB_READ" "$WORK/mb-safe-notes.md"
m1=$(mb_kept mb-safe base d)
starts=$(mb_events mb-safe gate.start)
m2=$(mb_move docs/board.md)
brief=$(land --repo "$MB" merge-review mb-safe)
m3=$(mb_move docs/board.md)
printf '%s\n' 'Verdict: merge. The change does what its criterion says.' 'Base: safe. What moved changed only docs/board.md, which the change does not read.' > "$WORK/mb-safe.md"
late=$(land --repo "$MB" merge-review mb-safe --file "$WORK/mb-safe.md" --tip "$(field 'd["tip"]' <<<"$brief")" --base "$(field 'd["base"]' <<<"$brief")")
beyond=$(land --repo "$MB" merge mb-safe --by merger --via server --message "fix: mb-safe" 2>&1 || true)
kept_refusal=$(mb_kept mb-safe merge_refused '(d["by"], d["from"], d["kind"])')
reread=$(merge_read "$MB" mb-safe merge safe)
cleared=$(mb_kept mb-safe merge_refused d)
gh_said=$(GH_REFUSE="Pull request is not mergeable: a required check is pending" land --repo "$MB" merge mb-safe --by merger --via server --message "fix: mb-safe" 2>&1 || true)
untouched=$(mb_body mb-safe '"read of what moved" in d')
edit_said=$(GH_EDIT_REFUSE="HTTP 502: Bad Gateway" land --repo "$MB" merge mb-safe --by merger --via server --message "fix: mb-safe" 2>&1 || true)
open_still=$(status_in "$MB" mb-safe)
commit_body=$(git -C "$MBO" log -1 --format=%b main)
merged=$(land --repo "$MB" merged mb-safe)
line="The checks ran on main at ${m1:0:9}; it merged on main at ${m3:0:9}, after the merge agent's read of what moved: What moved touches nothing the change rests on."
started=$(grep '"event": "merge.start", "task": "mb-safe"' "$MB/.lem/state/events.jsonl" | tail -1 | field '(d.get("after"), d.get("base"))')
if [ "$(field '(d["base"], d["facts"]["moved"]["checks_ran_on"], d["facts"]["moved"]["base_now"], d["facts"]["moved"]["files"], d["facts"]["moved"]["overlap"], [c["subject"] for c in d["facts"]["moved"]["commits"]])' <<<"$brief")" \
    = "('$m2', '$m1', '$m2', ['docs/board.md'], [], ['docs: docs/board.md'])" ] \
  && [ "$(field '(d["base"], d["base_call"], d["base_why"])' <<<"$late")" = "('$m2', 'safe', 'What moved changed only docs/board.md, which the change does not read.')" ] \
  && grep -qF "the read of ${m2:0:9} said safe, and it covers no later base" <<<"$beyond" && [ "$kept_refusal" = "('merger', 'lem', 'base')" ] \
  && [ "$(field '(d["base"], d["base_call"], d["next"].startswith("the board"))' <<<"$reread")" = "('$m3', 'safe', True)" ] && [ "$cleared" = None ] \
  && grep -qF "GitHub refused the merge" <<<"$gh_said" && [ "$untouched" = False ] \
  && grep -qF "did not reach the pull request's text (gh pr edit said: HTTP 502: Bad Gateway); the task stays open, and \`lem land merged mb-safe\` tries again" <<<"$edit_said" \
  && [ "$open_still" = open ] && [ "$commit_body" = "$(printf '%s\n\n%s\n\n%s' "$fixed_line" "$line" "Lem task: mb-safe")" ] \
  && [ "$(field 'd["base_read"]' <<<"$merged")" = "$line" ] && [ "$(status_in "$MB" mb-safe)" = landed ] && [ "$(mb_body mb-safe "d.rstrip().endswith('''$line''')")" = True ] \
  && grep -qxF "$line" "$MB/.lem/state/tasks/mb-safe/pr.md" && grep -qxF "$line" "$MB/.lem/state/tasks/mb-safe/state.md" \
  && [ "$(mb_kept mb-safe merged_by '(d["by"], d["after"], d["base"], d["checks_ran_on"])')" = "('merger', 'a read of the moved base', '$m3', '$m1')" ] \
  && [ "$started" = "('a read of the moved base', '${m3:0:9}')" ] && [ "$(mb_events mb-safe gate.start)" = "$starts" ] \
  && [ "$(mb_logged mb-safe merge.review '(d["base"], d["base_call"])')" = "[('${m2:0:9}', 'safe'), ('${m3:0:9}', 'safe')]" ] \
  && [ "$(git -C "$MBO" show main:docs/board.md | grep -c '^move ')" = 2 ] && [ "$(git -C "$MBO" show main:safe.txt)" = yes ]; then
  pass "a base that moved after the checks is read by a fresh merge agent with the commits and the files that moved beside the change; its read covers the base its brief named, so an answer recorded after main moved again covers no later base and the merge waits for a new read; a safe read merges with no new run of the checks and keeps what moved, and the merge commit, the pull request's text, pr.md and the task's state name the base the checks ran on, the base it merged on and the read's why, also when the edit of the text failed once; the squash commit's body names the fix on the way before that line and ends with the task; a merge GitHub refuses writes no line"
else
  fail "a safe read of a moved base: $brief / $late / $beyond / $kept_refusal / $reread / $cleared / $gh_said / $untouched / $edit_said / $open_still / $commit_body / $merged / $started"
fi

# Another round: the read keeps a base refusal that only a new landing answers, also when the move touched a file the
# change edits too; and an answer with no base call, twice on a moved base, is recorded as another round.
mb_task mb-round round.txt
round_tree=$(project --repo "$MB" worktree-dir mb-round)
printf '%s\n' one 2 3 4 5 6 7 8 9 10 > "$round_tree/shared.txt" && git -C "$round_tree" commit -q -am "fix: the first line"
mb_land mb-round
mb_task mb-mute mute.txt && mb_land mb-mute
git -C "$MBX" pull -q --ff-only origin main && printf '%s\n' 1 2 3 4 5 6 7 8 9 ten > "$MBX/shared.txt" && git -C "$MBX" commit -q -am "fix: the last line" && git -C "$MBX" push -q origin main
overlap=$(land --repo "$MB" merge-review mb-round | field 'd["facts"]["moved"]["overlap"]')
round=$(merge_read "$MB" mb-round merge "another round")
round_tip=$(mb_kept mb-round proposed d)
again_brief=$(land --repo "$MB" merge-review mb-round 2>&1 || true)
printf '%s\n' 'Verdict: merge. Fine.' 'Base: safe. Nothing moved that matters.' > "$WORK/mb-round-safe.md"
again_answer=$(land --repo "$MB" merge-review mb-round --file "$WORK/mb-round-safe.md" --tip "$round_tip" --base "$(git -C "$MB" rev-parse origin/main)" 2>&1 || true)
again_merge=$(land --repo "$MB" merge mb-round --by merger --via server --message "fix: mb-round" 2>&1 || true)
round_refusal=$(mb_kept mb-round merge_refused '(d["by"], d["from"], d["kind"])')
mute_brief=$(land --repo "$MB" merge-review mb-mute)
printf '%s\n' 'Verdict: merge. The change does what its criterion says.' '' 'Its test proves it.' > "$WORK/mb-mute.md"
mute_first=$(land --repo "$MB" merge-review mb-mute --file "$WORK/mb-mute.md" --tip "$(field 'd["tip"]' <<<"$mute_brief")" --base "$(field 'd["base"]' <<<"$mute_brief")" 2>&1 || true)
mute_second=$(land --repo "$MB" merge-review mb-mute --file "$WORK/mb-mute.md" --tip "$(field 'd["tip"]' <<<"$mute_brief")" --base "$(field 'd["base"]' <<<"$mute_brief")")
mute_refusal=$(mb_kept mb-mute merge_refused '(d["from"], d["kind"])')
# the new landing: the rebase with no conflict carries the review and the merge review, with no call on the old base
land --repo "$MB" start mb-round >/dev/null && land --repo "$MB" base mb-round >/dev/null && land --repo "$MB" checks mb-round >/dev/null && land --repo "$MB" read mb-round >/dev/null
reproposed=$(land --repo "$MB" propose mb-round --title "fix: mb-round" --notes "$NOTES")
carried=$(mb_kept mb-round merge_review '(d["verdict"], "base_call" in d, "carried_from" in d)')
landed_round=$(land --repo "$MB" merge mb-round --by merger --via server --message "fix: mb-round")
if [ "$overlap" = "['shared.txt']" ] \
  && [ "$(field '(d["base_call"], "lem land start" in d["next"], "the owner is not asked" in d["next"])' <<<"$round")" = "('another round', True, True)" ] \
  && [ "$(mb_kept mb-round another_round d)" = "$round_tip" ] && [ "$round_refusal" = "('merger', 'lem', 'base')" ] \
  && grep -qF "said that the moved base needs another round of the checks, and no later read answers that" <<<"$again_brief" \
  && grep -qF "said that the moved base needs another round of the checks, and no later read answers that" <<<"$again_answer" \
  && grep -qF "the merge agent's read of this tip said another round; run \`lem land start\`" <<<"$again_merge" \
  && [ "$(mb_logged mb-round merge.refused '(d["kind"], d["from"], "another round" in d["said"])')" = "[('base', 'lem', True), ('base', 'lem', True)]" ] \
  && grep -qF "gives no call on the moved base" <<<"$mute_first" && grep -qF "the merge agent is asked again" <<<"$mute_first" \
  && [ "$(field '(d["verdict"], d["base_call"], d["base_why"])' <<<"$mute_second")" \
    = "('merge', 'another round', \"the merge agent's answer could not be recorded twice (its second line gave no call on the moved base), and in doubt the checks run again\")" ] \
  && [ "$mute_refusal" = "('lem', 'base')" ] \
  && [ "$(field 'd["merge_review"]' <<<"$reproposed")" = carried ] && [ "$carried" = "('merge', False, True)" ] \
  && [ "$(status_in "$MB" mb-round)" = landed ] && [ "$(mb_kept mb-round merged_by d)" = "{'by': 'merger', 'via': 'server'}" ] && [ "$(field 'd["base_read"]' <<<"$landed_round")" = None ] \
  && [ "$(git -C "$MBO" show main:shared.txt | tr '\n' ' ')" = "one 2 3 4 5 6 7 8 9 ten " ]; then
  pass "a read that says another round merges nothing and keeps a base refusal that no later read answers, also when the move touched a file the change edits; a second answer with no base call on a moved base is recorded as another round; the new landing carries the merge review with no call on the old base and merges with no line"
else
  fail "another round on a moved base: $overlap / $round / $again_brief / $again_answer / $again_merge / $round_refusal / $mute_first / $mute_second / $reproposed / $carried / $landed_round"
fi
project --repo "$MB" state mb-mute dropped "the test is over" >/dev/null

# The owner's merge that meets a moved base waits for the read, and on safe it goes through with no new press of his;
# with history = keep the pull request's text alone holds the line.
mb_settings agent keep
mb_task mb-owner owner.txt && mb_land mb-owner
owner_move=$(mb_move docs/board.md)
pressed=$(land --repo "$MB" merge mb-owner --by owner 2>&1 || true)
tap=$(mb_kept mb-owner owner_tap 'd["tip"] == "'"$(mb_kept mb-owner proposed d)"'"')
stands=$(merge_read "$MB" mb-owner merge safe)
stood=$(land --repo "$MB" merge mb-owner --by owner --via server --standing --tip "$(mb_kept mb-owner proposed d)")
owner_line="The checks ran on main at $(mb_kept mb-owner merged_by 'd["checks_ran_on"][:9]'); it merged on main at ${owner_move:0:9}, after the merge agent's read of what moved: What moved touches nothing the change rests on."
if grep -qF "the owner's merge stands, and goes through after a read that says \`Base: safe.\`" <<<"$pressed" && [ "$tap" = True ] \
  && [ "$(field '(d["base_call"], d["next"].startswith("the owner'"'"'s merge stands"))' <<<"$stands")" = "('safe', True)" ] && [ "$(mb_kept mb-owner merge_refused d)" = None ] \
  && [ "$(mb_logged mb-owner merge.stands '(d["by"], d["after"], d["base"])')" = "[('owner', 'a read of the moved base', '${owner_move:0:9}')]" ] \
  && [ "$(status_in "$MB" mb-owner)" = landed ] && [ "$(field 'd["base_read"]' <<<"$stood")" = "$owner_line" ] && [ "$(mb_body mb-owner "'''$owner_line''' in d")" = True ] \
  && [ "$(mb_kept mb-owner merged_by '(d["by"], d["via"], d["after"])')" = "('owner', 'server', 'a read of the moved base')" ] \
  && git -C "$MBO" merge-base --is-ancestor "$owner_move" main && [ "$(git -C "$MBO" show main:owner.txt)" = yes ] && [ -z "$(git -C "$MBO" log -1 --format=%b main)" ]; then
  pass "the owner's merge that meets a moved base waits for the merge agent's read; on safe the refusal is answered, his merge stands and goes through on the new base with no new press, and with history = keep the pull request's text alone names the read"
else
  fail "the owner's merge on a moved base: $pressed / $tap / $stands / $stood / $(git -C "$MBO" log -3 --format=%s main)"
fi
# His merge stands through a red base too: the read of what moved says another round, the new landing's checks are red
# because the base is, so the session holds the task blocked until the base is green again and lands it again from ready;
# the change and the reasons it is not green are the ones he saw, so propose says his merge stands.
mb_task mb-red red.txt && mb_land mb-red
mb_move docs/board.md >/dev/null
land --repo "$MB" merge mb-red --by owner >/dev/null 2>&1 || true
red_tap=$(mb_kept mb-red owner_tap 'd["tip"] == "'"$(mb_kept mb-red proposed d)"'"')
merge_read "$MB" mb-red merge "another round" >/dev/null
land --repo "$MB" start mb-red >/dev/null && land --repo "$MB" base mb-red >/dev/null
project --repo "$MB" state mb-red blocked "the base is red" "after: mb-base-fix" >/dev/null
mb_move docs/board.md >/dev/null
project --repo "$MB" state mb-red ready "the base is green again" >/dev/null
land --repo "$MB" start mb-red >/dev/null && land --repo "$MB" base mb-red >/dev/null && polish_in "$MB" mb-red && land --repo "$MB" checks mb-red >/dev/null
red_due=$(land --repo "$MB" read mb-red)
if [ "$(field 'd["due"]' <<<"$red_due")" != none ]; then
  land --repo "$MB" read mb-red --record "$(record mb-red "$(field 'd["round"]' <<<"$red_due")" "$MB_READ")" >/dev/null
fi
red_again=$(land --repo "$MB" propose mb-red --title "fix: mb-red" --notes "$NOTES" 2>&1 || true)
red_tree=$(project --repo "$MB" worktree-dir mb-red)
if [ "$red_tap" = True ] && [ "$(field 'str(d["owner_merge"]).startswith("stands")' <<<"$red_again")" = True ] \
  && [ "$(mb_kept mb-red owner_tap 'd and d["tip"]')" = "$(git -C "$red_tree" rev-parse HEAD)" ]; then
  pass "the owner's merge that a moved base refused stands through a red base: the task blocked until the base is green again lands once more from ready, and propose says his merge stands on the new tip while the change and the reasons it is not green are the ones he saw"
else
  fail "the owner's merge through a red base: $red_tap / $red_due / $red_again / $(mb_kept mb-red owner_tap d)"
fi
# It goes on as the server goes on: propose logged that his merge stands for the new tip, and the server's run of his
# merge lands it. What the cut landing carried, carried: no second review, no fresh merge agent, one new landing.
red_new=$(git -C "$red_tree" rev-parse HEAD)
red_landed=$(land --repo "$MB" merge mb-red --by owner --via server --standing --tip "$red_new" 2>&1 || true)
red_line="rebased on main; the review carried over the rebase; the merge review carried over the rebase; the checks passed again"
if [ "$(field 'd["due"]' <<<"$red_due")" = none ] && [ "$(field '(d["merge_review"], d["merge_review_why"], d["synced"])' <<<"$red_again")" = "('carried', None, '$red_line')" ] \
  && [ "$(mb_events mb-red review)" = 1 ] && [ "$(mb_events mb-red land.again)" = 1 ] && [ "$(mb_kept mb-red relands d)" = 1 ] \
  && [ "$(mb_body mb-red "'''$red_line''' in d.lower()")" = True ] \
  && [ "$(mb_logged mb-red merge.stands 'd["tip"]')" = "['${red_new:0:9}']" ] && [ "$(mb_events mb-red merge.ended)" = 0 ] \
  && [ "$(status_in "$MB" mb-red)" = landed ] && [ "$(mb_kept mb-red merged_by '(d["by"], d["via"])')" = "('owner', 'server')" ]; then
  pass "through a red base the new landing goes on with what it carried: no second review and no fresh merge agent, one new landing counted, the pull request's text says what carried, and the board's server lands the owner's standing merge of the new tip"
else
  fail "what carries through a red base: $red_due / $red_again / $red_landed / $(mb_events mb-red review) / $(mb_events mb-red land.again) / $(mb_logged mb-red merge.stands d)"
fi

# The steps of the path through a red base that the checks below share: mb_refused SLUG, the owner's merge refused on a
# moved base and kept, then the merge agent's read of what moved, which says another round; mb_wait SLUG, the new
# landing's start and first rebase, then its wait for the red base as blocked; mb_green SLUG, the base green again.
mb_refused() { mb_move docs/board.md >/dev/null; land --repo "$MB" merge "$1" --by owner >/dev/null 2>&1 || true; merge_read "$MB" "$1" merge "another round" >/dev/null; }
mb_wait() { land --repo "$MB" start "$1" >/dev/null && land --repo "$MB" base "$1" >/dev/null && project --repo "$MB" state "$1" blocked "the base is red" "after: mb-base-fix" >/dev/null; }
mb_green() { project --repo "$MB" state "$1" ready "the base is green again" >/dev/null; }
# mb_again SLUG [RECORD]: after the wait, the landing from start to the read: a review that is due is written down with
# RECORD (a read that found nothing by default)
mb_again() {
  local due
  land --repo "$MB" start "$1" >/dev/null && land --repo "$MB" base "$1" >/dev/null && polish_in "$MB" "$1" && land --repo "$MB" checks "$1" >/dev/null || return 1
  due=$(land --repo "$MB" read "$1")
  if [ "$(field 'd["due"]' <<<"$due")" != none ]; then land --repo "$MB" read "$1" --record "$(record "$1" "$(field 'd["attempt"]' <<<"$due")" "${2:-$MB_READ}")" >/dev/null; fi
}
# mb_meet FILE: origin's main gives FILE words of its own, so that a task that adds FILE meets a conflict on its next rebase
mb_meet() { git -C "$MBX" pull -q --ff-only origin main && echo theirs > "$MBX/$1" && git -C "$MBX" add -A && git -C "$MBX" commit -q -m "fix: $1 on main" && git -C "$MBX" push -q origin main; }
# mb_resolve SLUG FILE: the builder's resolution of that conflict, here the test's: the task's words stay
mb_resolve() {
  local tree
  tree=$(project --repo "$MB" worktree-dir "$1")
  git -C "$tree" rebase -q origin/main >/dev/null 2>&1 || true
  echo yes > "$tree/$2" && git -C "$tree" add "$2" && GIT_EDITOR=true git -C "$tree" rebase --continue >/dev/null 2>&1
}
# mb_keys SLUG: the keys landing.json holds, sorted
mb_keys() { "$PY" -c 'import json, sys; print(sorted(json.load(open(sys.argv[1]))))' "$MB/.lem/state/tasks/$1/landing.json"; }

# A commit after the second rebase changes the change he merged: propose says his merge ended and why, never null, and logs it.
mb_task mb-late late.txt && mb_land mb-late
mb_refused mb-late && mb_wait mb-late
mb_move docs/board.md >/dev/null
mb_green mb-late
late_tree=$(project --repo "$MB" worktree-dir mb-late)
land --repo "$MB" start mb-late >/dev/null && land --repo "$MB" base mb-late >/dev/null
echo repaired > "$late_tree/repair.txt" && git -C "$late_tree" add repair.txt && git -C "$late_tree" commit -q -m "fix: the failed check"
late_due=$(land --repo "$MB" checks mb-late >/dev/null && land --repo "$MB" read mb-late)
land --repo "$MB" read mb-late --record "$(record mb-late "$(field 'd["attempt"]' <<<"$late_due")" "$MB_READ")" >/dev/null
late=$(land --repo "$MB" propose mb-late --title "fix: mb-late" --notes "$NOTES" 2>&1 || true)
if [ "$(field 'd["owner_merge"]' <<<"$late")" = "ended: a commit came after the rebase; the owner merges it again" ] \
  && [ "$(mb_logged mb-late merge.ended '(d["by"], d["why"])')" = "[('owner', 'a commit came after the rebase')]" ] && [ "$(mb_kept mb-late owner_tap d)" = None ]; then
  pass "a commit after the rebase that follows a red base ends the owner's standing merge: propose prints ended with that reason, never null, and logs merge.ended once"
else
  fail "a commit after the second rebase: $late_due / $late / $(mb_logged mb-late merge.ended d)"
fi
project --repo "$MB" state mb-late dropped "the test is over" >/dev/null

# A start over still starts over, with nothing carried, and the end of his standing merge is told: start prints it as
# ended with the start over's reason and logs merge.ended once; a start over with no standing merge prints null.
mb_task mb-over over.txt && mb_land mb-over
mb_move docs/board.md >/dev/null
land --repo "$MB" merge mb-over --by owner >/dev/null 2>&1 || true
over_tip=$(mb_kept mb-over owner_tap 'd["tip"]')
project --repo "$MB" state mb-over ready --start-over "the owner asked for a fresh landing" >/dev/null
over=$(land --repo "$MB" start mb-over)
over_keys=$(mb_keys mb-over)
project --repo "$MB" state mb-over ready --start-over "the landing is cut again" >/dev/null
over_none=$(land --repo "$MB" start mb-over | field 'd["owner_merge"]')
if [ "$(field 'd["owner_merge"]' <<<"$over")" = "ended: the landing started over: the owner asked for a fresh landing; the owner merges it again" ] \
  && [ "$(mb_logged mb-over merge.ended '(d["tip"], d["why"])')" = "[('${over_tip:0:9}', 'the landing started over: the owner asked for a fresh landing')]" ] \
  && [ "$over_keys" = "['branch', 'polish', 'pr', 'pushed']" ] && [ "$over_none" = None ] && [ "$(mb_events mb-over land.again)" = 0 ]; then
  pass "ready --start-over over an open task with the owner's standing merge starts the landing over with only the pull request's keys, and start prints his merge as ended with the start over's reason and logs merge.ended once; a start over with no standing merge prints null"
else
  fail "a start over with his standing merge: $over / $over_keys / $over_none / $(mb_logged mb-over merge.ended d)"
fi
project --repo "$MB" state mb-over dropped "the test is over" >/dev/null

# The check for a command of the checks comes after what start does with the record: an open task's new landing is
# counted once, though start refused it and ran again; a start over is not lost through that refusal, which says the end
# of his merge, and the retry keeps only the pull request's keys.
mb_task mb-gate gate.txt && mb_land mb-gate
mb_move docs/board.md >/dev/null
land --repo "$MB" merge mb-gate --by owner >/dev/null 2>&1 || true
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' 'history = "keep"' > "$MB/.lem/settings.toml"
gate_refused=$(land --repo "$MB" start mb-gate 2>&1 || true)
gate_blocked=$(status_in "$MB" mb-gate)
mb_settings agent keep
land --repo "$MB" start mb-gate >/dev/null
gate_counted="$(mb_kept mb-gate relands d) $(mb_events mb-gate land.again) $(mb_kept mb-gate sync '(d["conflicting"], d["onto"])') $(mb_kept mb-gate owner_tap 'd is not None') $(status_in "$MB" mb-gate)"
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' 'history = "keep"' > "$MB/.lem/settings.toml"
project --repo "$MB" state mb-gate ready --start-over "the gate was cut off" >/dev/null
over_refused=$(land --repo "$MB" start mb-gate 2>&1 || true)
over_kept=$(mb_keys mb-gate)
mb_settings agent keep
over_retry=$(land --repo "$MB" start mb-gate | field 'd["owner_merge"]')
if grep -qF "no command in its checks" <<<"$gate_refused" && [ "$gate_blocked" = blocked ] && [ "$gate_counted" = "1 1 (False, None) True landing" ] \
  && grep -qF "The owner's merge ended: the landing started over: the gate was cut off; the owner merges it again" <<<"$over_refused" \
  && [ "$over_kept" = "['polish', 'pr', 'pushed']" ] && [ "$over_retry" = None ] && [ "$(mb_events mb-gate merge.ended)" = 1 ] && [ "$(status_in "$MB" mb-gate)" = landing ]; then
  pass "start counts an open task's new landing before it refuses a project with no command of the checks, and its retry counts it no second time; a start over refused the same way has already ended the owner's merge, which the refusal says, and the retry starts over with only the pull request's keys"
else
  fail "start's refusal for want of a command of the checks: $gate_refused / $gate_blocked / $gate_counted / $over_refused / $over_kept / $over_retry"
fi
project --repo "$MB" state mb-gate dropped "the test is over" >/dev/null

# A conflict on the second rebase, after a clean first one and the wait: the second rebase starts again from the tip
# proposed before, so the conflict's tip before is that one, and a resolution whose read finds nothing carries the merge
# review and his merge on a request that is not careful; on a careful one his merge ends with the careful reason.
mb_task mb-meet meet.txt && mb_land mb-meet
meet_t0=$(mb_kept mb-meet proposed d)
mb_refused mb-meet && mb_wait mb-meet
mb_meet meet.txt
mb_green mb-meet
land --repo "$MB" start mb-meet >/dev/null
meet_stop=$(land --repo "$MB" base mb-meet 2>/dev/null || true)
meet_before=$(mb_kept mb-meet conflict 'd["before"]')
mb_resolve mb-meet meet.txt
mb_again mb-meet
meet=$(land --repo "$MB" propose mb-meet --title "fix: mb-meet" --notes "$NOTES" 2>&1 || true)
WARY_READ='{"kind": "full", "ran": [{"name": "default", "why": "the request is careful"}], "answered": ["codex"]}'
mb_task mb-wary wary.txt
echo 'careful: the owner says so' >> "$MB/.lem/state/tasks/mb-wary/brief.md"
mb_land mb-wary "$WARY_READ" "$MIG"
mb_refused mb-wary && mb_wait mb-wary
mb_meet wary.txt
mb_green mb-wary
land --repo "$MB" start mb-wary >/dev/null && land --repo "$MB" base mb-wary >/dev/null 2>&1 || true
mb_resolve mb-wary wary.txt
mb_again mb-wary "$WARY_READ"
wary=$(land --repo "$MB" propose mb-wary --title "fix: mb-wary" --notes "$MIG" 2>&1 || true)
if [ "$(field 'd["conflict"]' <<<"$meet_stop")" = "['meet.txt']" ] && [ "$meet_before" = "$meet_t0" ] && [ "$(mb_kept mb-meet resolution 'd["before"]')" = "$meet_t0" ] \
  && [ "$(field '(d["merge_review"], d["owner_merge"].split(":")[0])' <<<"$meet")" = "('carried', 'stands')" ] \
  && [ "$(field 'd["owner_merge"]' <<<"$wary")" = "ended: the rebase met a conflict, and the request is careful: the owner says so; the owner merges it again" ]; then
  pass "a conflict on the rebase after a red base is met from the tip proposed before, and its resolution with a read that found nothing carries the merge review and the owner's merge on a request that is not careful; on a careful one his merge ends with the careful reason"
else
  fail "a conflict after a red base: $meet_stop / $meet_before / $meet_t0 / $meet / $wary"
fi
project --repo "$MB" state mb-meet dropped "the test is over" >/dev/null
project --repo "$MB" state mb-wary dropped "the test is over" >/dev/null

# The probe of decision 6 (probe-two-rebases.py, git 2.55.0): a branch of two commits, a red base that repeats the first
# commit's edit, so that git leaves that commit out of the first rebase, and a repair that reverts the red base whole.
# After the wait the second rebase starts again from the tip proposed before, so the branch holds both commits again.
mb_task mb-probe probe.txt
probe_tree=$(project --repo "$MB" worktree-dir mb-probe)
echo new > "$probe_tree/feature.txt" && git -C "$probe_tree" add feature.txt && git -C "$probe_tree" commit -q -m "feat: the feature"
echo new > "$probe_tree/label.txt" && git -C "$probe_tree" add label.txt && git -C "$probe_tree" commit -q -m "feat: the label"
mb_land mb-probe
probe_t0=$(mb_kept mb-probe proposed d)
git -C "$MBX" pull -q --ff-only origin main && echo new > "$MBX/feature.txt" && echo broken > "$MBX/broken.txt"
git -C "$MBX" add -A && git -C "$MBX" commit -q -m "fix: the red base" && git -C "$MBX" push -q origin main
land --repo "$MB" merge mb-probe --by owner >/dev/null 2>&1 || true
merge_read "$MB" mb-probe merge "another round" >/dev/null
mb_wait mb-probe
probe_dropped=$(git -C "$probe_tree" log --format=%s origin/main..HEAD | grep -c "the feature" || true)
git -C "$MBX" revert --no-edit HEAD >/dev/null && git -C "$MBX" push -q origin main
mb_green mb-probe
mb_again mb-probe
probe_held="$(git -C "$probe_tree" rev-list --count origin/main..HEAD) $(git -C "$probe_tree" show HEAD:feature.txt) $(git -C "$probe_tree" show HEAD:label.txt)"
probe_carried=$(mb_kept mb-probe rebase_carried '(d["from"], d["to"])')
probe=$(land --repo "$MB" propose mb-probe --title "fix: mb-probe" --notes "$NOTES" 2>&1 || true)
probe_new=$(git -C "$probe_tree" rev-parse HEAD)
if [ "$probe_dropped" = 0 ] && [ "$probe_held" = "3 new new" ] && [ "$probe_carried" = "('$probe_t0', '$probe_new')" ] \
  && [ "$(field 'd["owner_merge"].split(":")[0]' <<<"$probe")" = stands ]; then
  pass "a second rebase after a red base starts again from the tip proposed before: the commit git left out of the first rebase, onto a base that repeated its edit, is on the branch again once the base reverted it, and the owner's merge stands for the whole change"
else
  fail "the probe's two rebases: $probe_dropped / $probe_held / $probe_carried / $probe_t0 / $probe"
fi
# base run twice with no move in one landing: the record is still one rebase from the tip proposed before
probe_first=$(mb_kept mb-probe proposed d)
mb_refused mb-probe && mb_wait mb-probe
mb_green mb-probe
land --repo "$MB" start mb-probe >/dev/null && land --repo "$MB" base mb-probe >/dev/null && land --repo "$MB" base mb-probe >/dev/null
polish_in "$MB" mb-probe && land --repo "$MB" checks mb-probe >/dev/null
twice_carried=$(mb_kept mb-probe rebase_carried 'd["from"]')
twice=$(land --repo "$MB" propose mb-probe --title "fix: mb-probe" --notes "$NOTES" 2>&1 || true)
if [ "$twice_carried" = "$probe_first" ] && [ "$(field 'd["owner_merge"].split(":")[0]' <<<"$twice")" = stands ]; then
  pass "base run twice with no move of the base in one landing keeps one rebase from the tip proposed before, and the owner's merge still stands"
else
  fail "base twice with no move: $twice_carried / $probe_first / $twice"
fi
project --repo "$MB" state mb-probe dropped "the test is over" >/dev/null

# A commit added to the branch after the proposal, then the new landing, a clean first rebase, the wait and the second
# rebase: the second rebase starts again from the tip before Lem's own first one, so the commit is still on the branch,
# and propose says what one rebase with no wait says.
mb_task mb-tip tip.txt && mb_land mb-tip
mb_refused mb-tip
tip_tree=$(project --repo "$MB" worktree-dir mb-tip)
echo more > "$tip_tree/more.txt" && git -C "$tip_tree" add more.txt && git -C "$tip_tree" commit -q -m "fix: one more file"
mb_wait mb-tip
mb_move docs/board.md >/dev/null
mb_green mb-tip
mb_again mb-tip
tip_held=$(git -C "$tip_tree" log --format=%s origin/main..HEAD | grep -c "one more file" || true)
tip=$(land --repo "$MB" propose mb-tip --title "fix: mb-tip" --notes "$NOTES" 2>&1 || true)
if [ "$tip_held" = 1 ] && [ "$(field 'd["owner_merge"]' <<<"$tip")" = "ended: a commit came after the tip proposed before; the owner merges it again" ]; then
  pass "a commit added after the proposal stays on the branch through the two rebases of a red base, and propose ends the owner's merge with the reason one rebase with no wait gives"
else
  fail "a commit after the proposal and two rebases: $tip_held / $tip"
fi
project --repo "$MB" state mb-tip dropped "the test is over" >/dev/null

# A safe read never lets the merge agent merge what it may not merge today: a careful request still waits for the owner.
mb_settings agent squash
mb_task mb-careful careful.txt
printf '%s\n' 'slug: mb-careful' 'lead: session' 'careful: the owner says so' > "$(project --repo "$MB" task-dir mb-careful)/brief.md"
mb_land mb-careful '{"kind": "full", "ran": [{"name": "default", "why": "the request is careful"}], "answered": ["codex"]}' "$MIG"
mb_move docs/board.md >/dev/null
careful_read=$(merge_read "$MB" mb-careful merge safe)
careful_merge=$(land --repo "$MB" merge mb-careful --by merger --via server --message "fix: mb-careful" 2>&1 || true)
if [ "$(field '(d["base_call"], d["calls"], d["next"].startswith("it calls the owner"))' <<<"$careful_read")" = "('safe', True, True)" ] \
  && grep -qF "a careful request is merged by the owner" <<<"$careful_merge" && [ "$(status_in "$MB" mb-careful)" = open ]; then
  pass "a safe read of a moved base still calls the owner for a careful request, and the merge agent merges nothing"
else
  fail "a careful request on a moved base: $careful_read / $careful_merge"
fi
project --repo "$MB" state mb-careful dropped "the test is over" >/dev/null

# On a base that did not move, an answer with a heading above its verdict is refused once; the second for the same tip and
# base is a review that calls the owner with no verdict, whatever its lower line says, so the merge agent merges nothing.
# The task is green, not careful, with the review's careful call, so only the verdict rule stops the merge.
mb_task mb-heading heading.txt && mb_land mb-heading
heading_brief=$(land --repo "$MB" merge-review mb-heading)
heading_tip=$(field 'd["tip"]' <<<"$heading_brief")
heading_base=$(field 'd["base"]' <<<"$heading_brief")
printf '%s\n' '## Review' 'Verdict: merge. The change does what its criterion says.' > "$WORK/mb-heading.md"
heading_exit=0
heading_first=$(land --repo "$MB" merge-review mb-heading --file "$WORK/mb-heading.md" --tip "$heading_tip" --base "$heading_base" 2>&1) || heading_exit=$?
heading_second_exit=0
heading_second=$(land --repo "$MB" merge-review mb-heading --file "$WORK/mb-heading.md" --tip "$heading_tip" --base "$heading_base" 2>&1) || heading_second_exit=$?
heading_why="the merge agent twice gave no verdict on its first line; its last answer puts another line above its verdict, \`Verdict: merge.\`"
heading_waits=$(project --repo "$MB" waiting | field '"mb-heading" in [r["task"] for r in d["reviews"]]')
heading_merge=$(land --repo "$MB" merge mb-heading --by merger --via server --message "fix: mb-heading" 2>&1 || true)
if [ "$heading_base" = "$(mb_kept mb-heading base d)" ] && [ "$heading_exit" = 1 ] && grep -qF "the merge agent is asked again" <<<"$heading_first" \
  && [ "$heading_second_exit" = 0 ] && [ "$(field '(d["verdict"], d["calls"], d["why"], d["next"].startswith("it calls the owner"))' <<<"$heading_second")" = "(None, True, '$heading_why', True)" ] \
  && [ "$(mb_kept mb-heading merge_review '(d["verdict"], d["calls"], d["why"])')" = "(None, True, '$heading_why')" ] && [ "$(mb_kept mb-heading merge_unread d)" = None ] \
  && [ "$(mb_logged mb-heading merge.review '("verdict" in d, d["calls"])')" = "[(False, True)]" ] \
  && cmp -s "$WORK/mb-heading.md" "$MB/.lem/state/tasks/mb-heading/merge-review.md" \
  && [ "$heading_waits" = True ] && grep -qF "the merge review calls the owner" <<<"$heading_merge" && [ "$(status_in "$MB" mb-heading)" = open ]; then
  pass "on a base that did not move, a first answer with no verdict on its first line is refused and the merge agent is asked again; the second for the same tip and base is written down as a review that calls the owner, with no verdict and a why that names the lower line's verdict, so \"Read the merge review\" waits for him and the merge agent's merge is refused by the verdict rule"
else
  fail "a second answer with no verdict on a base that did not move: $heading_first / $heading_second / $heading_waits / $heading_merge"
fi
project --repo "$MB" state mb-heading dropped "the test is over" >/dev/null

# A merge on GitHub outside Lem between Lem's look at the base and its merge call: the merged commit's parent is not the
# base the read covered, and the pull request's text and the task's state say so.
mb_task mb-race race.txt && mb_land mb-race
mb_move docs/board.md >/dev/null
merge_read "$MB" mb-race merge safe >/dev/null
race_read=$(mb_kept mb-race merge_review 'd["base"]')
git -C "$MBX" pull -q --ff-only origin main && echo raced > "$MBX/raced.txt" && git -C "$MBX" add -A && git -C "$MBX" commit -q -m "feat: raced" && git -C "$MBX" push -q origin HEAD:refs/heads/racer
racer=$(git -C "$MBX" rev-parse HEAD) && git -C "$MBX" reset -q --hard origin/main
raced=$(GH_BASE_FIRST=$racer land --repo "$MB" merge mb-race --by merger --via server --message "fix: mb-race")
race_line="The checks ran on main at $(mb_kept mb-race base 'd[:9]'); it merged on main at ${racer:0:9}, which no read of the merge agent covered (its read covered ${race_read:0:9}): a merge on GitHub came between Lem's look at the base and its merge, and nothing undoes it"
if [ "$(field 'd["base_read"]' <<<"$raced")" = "$race_line" ] && [ "$(field 'd["uncovered"]' <<<"$raced")" = "mb-race: $race_line" ] && [ "$(git -C "$MBO" rev-parse main^)" = "$racer" ] \
  && [ "$(mb_body mb-race "'''$race_line''' in d")" = True ] && grep -qxF "$race_line" "$MB/.lem/state/tasks/mb-race/state.md"; then
  pass "a merge whose real parent on GitHub is not the base the read covered names the base it merged on and says that no read covered it, in the pull request's text, the task's state and a line for the owner"
else
  fail "a merge outside Lem before Lem's merge call: $raced / $race_line"
fi

# A move that a revert undid after Lem refused the owner's merge for it: the read's brief names the checks' own base,
# and that read, with no call on a move, answers the refusal, so his merge stands and goes through with no new run of
# the checks.
mb_task mb-back back.txt && mb_land mb-back
back_base=$(mb_kept mb-back base d)
back_starts=$(mb_events mb-back gate.start)
mb_move docs/board.md >/dev/null
back_refused=$(land --repo "$MB" merge mb-back --by owner --message "fix: mb-back" 2>&1 || true)
git -C "$MBX" revert --no-edit HEAD >/dev/null && git -C "$MBX" push -q origin main
back_main=$(git -C "$MBX" rev-parse HEAD)
back_read=$(merge_read "$MB" mb-back merge)
back_cleared=$(mb_kept mb-back merge_refused d)
back_merged=$(land --repo "$MB" merge mb-back --by owner --via server --standing --tip "$(mb_kept mb-back proposed d)" --message "fix: mb-back")
if grep -qF "moved after the checks ran, by files (docs/board.md)" <<<"$back_refused" \
  && [ "$(field '(d["base"], d["base_call"], d["next"].startswith("the owner'"'"'s merge stands"))' <<<"$back_read")" = "('$back_base', None, True)" ] \
  && [ "$back_cleared" = None ] && [ "$(mb_logged mb-back merge.stands '(d["after"], d["base"])')" = "[(\"a read of the base back on the checks' tree\", '${back_base:0:9}')]" ] \
  && [ "$(status_in "$MB" mb-back)" = landed ] && [ "$(field 'd["base_read"]' <<<"$back_merged")" = None ] && [ "$(git -C "$MBO" rev-parse main^)" = "$back_main" ] \
  && [ "$(mb_events mb-back gate.start)" = "$back_starts" ] && [ "$(git -C "$MBO" show main:back.txt)" = yes ]; then
  pass "a move of the base that a revert undid after Lem refused the owner's merge: the read's brief names the checks' own base, its read answers the refusal, and his merge stands and goes through with no new run of the checks"
else
  fail "a read on the checks' base after a revert: $back_refused / $back_read / $back_cleared / $back_merged / $(git -C "$MBO" log -3 --format=%s main)"
fi

# A task started from a reviewer's item of the state folder, which git never holds: its file leaves with the landing, by
# Lem's merge and by `merged`; a removal that fails leaves the task open for `merged`; a pull request closed on GitHub
# drops the task and leaves the file, so the item is undecided again.
mkdir -p "$MB/.lem/state/backlog"
# mb_item SLUG FILE: the reviewer's item SLUG.md, and a task of the moved-base shop started from it, to its pull request
mb_item() {
  printf '%s\n' '---' 'worth: later' 'where: tests/lem-serve.sh' 'added: 2026-11-24' '---' "# $1" '' 'A check fails by chance.' > "$MB/.lem/state/backlog/$1.md"
  mb_task "$1" "$2" && printf '%s\n' ".lem/state/backlog/$1.md" > "$MB/.lem/state/tasks/$1/ask.txt" && mb_land "$1"
}
mb_item mb-item-lem item-lem.txt
by_lem=$(land --repo "$MB" merge mb-item-lem --by owner --message "fix: mb-item-lem")
mb_item mb-item-again item-again.txt
chmod 555 "$MB/.lem/state/backlog"
not_removed=$(land --repo "$MB" merge mb-item-again --by owner --message "fix: mb-item-again" 2>&1 || true)
open_again=$(status_in "$MB" mb-item-again)
chmod 755 "$MB/.lem/state/backlog"
by_merged=$(land --repo "$MB" merged mb-item-again)
mb_item mb-item-closed item-closed.txt
"$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); d["prs"][sys.argv[2]]["state"] = "CLOSED"; json.dump(d, open(sys.argv[1], "w"))' \
  "$MB.origin.git.gh.json" "$(mb_kept mb-item-closed pr 'd["number"]')"
closed=$(land --repo "$MB" merged mb-item-closed)
if [ "$(status_in "$MB" mb-item-lem)" = landed ] && [ ! -e "$MB/.lem/state/backlog/mb-item-lem.md" ] \
  && [ "$(field 'd["item"]' <<<"$by_lem")" = "{'path': '.lem/state/backlog/mb-item-lem.md', 'removed': True}" ] \
  && grep -qF "was not removed" <<<"$not_removed" && grep -qF "the task stays open, and \`lem land merged mb-item-again\` tries again" <<<"$not_removed" \
  && [ "$open_again" = open ] && [ "$(git -C "$MBO" show main:item-again.txt)" = yes ] \
  && [ "$(status_in "$MB" mb-item-again)" = landed ] && [ ! -e "$MB/.lem/state/backlog/mb-item-again.md" ] \
  && [ "$(field 'd["item"]' <<<"$by_merged")" = "{'path': '.lem/state/backlog/mb-item-again.md', 'removed': True}" ] \
  && [ "$(field 'd["state"]' <<<"$closed")" = dropped ] && [ -f "$MB/.lem/state/backlog/mb-item-closed.md" ]; then
  pass "a task started from a reviewer's item of the state folder removes the item's file when it lands, by Lem's merge and by merged; a removal that fails leaves the task open and merged removes it; a pull request closed on GitHub drops the task and leaves the file"
else
  fail "the reviewer's item at the landing: $by_lem / $not_removed / $open_again / $by_merged / $closed / $(ls "$MB/.lem/state/backlog")"
fi

# A merge agent's seat that fails after the pull request is open: the fallback stands in, the brief of the same tip
# and base is written again with its seat, the record names the seat that read whatever the settings say by then, and
# the pull request's text gets the stand-in's line once. When the stand-in fails too, the task is blocked, keeps its
# pull request, and a merge on GitHub while it waits still lands it, with the stand-in's line in the text replaced by
# the one that says it failed too, though no read came after the block.
mb_task mb-stand stand.txt && mb_land mb-stand
printf '%s\n' '[seats]' 'merger = "codex/gpt-6.2-sol:high"' > "$MB/.lem/settings.local.toml"
stand_first=$(land --repo "$MB" merge-review mb-stand)
stood=$(project --repo "$MB" seat-failed mb-stand merger --seat codex/gpt-6.2-sol:high --error tokens --said "You have no tokens left")
stand_again=$(land --repo "$MB" merge-review mb-stand)
# the settings name another merger while the stand-in reads: the record names the seat kept with the brief
printf '%s\n' '[seats]' 'merger = "codex/gpt-6.2-astra:high"' > "$MB/.lem/settings.local.toml"
printf '%s\n' 'Verdict: merge. The change does what its criterion says.' > "$WORK/mb-stand.md"
stand_tip=$(field 'd["tip"]' <<<"$stand_again")
stand_base=$(field 'd["base"]' <<<"$stand_again")
stand_read=$(land --repo "$MB" merge-review mb-stand --file "$WORK/mb-stand.md" --tip "$stand_tip" --base "$stand_base")
land --repo "$MB" merge-review mb-stand --file "$WORK/mb-stand.md" --tip "$stand_tip" --base "$stand_base" >/dev/null
stand_line="- the merge agent was \`claude/opus:high\` in place of \`codex/gpt-6.2-sol:high\`: Codex had no tokens"
printf '%s\n' "$stand_line" > "$WORK/mb-stand-line.txt"
stand_pr=$(mb_kept mb-stand pr 'd["number"]')
stand_count=$(gh_prs "$MB" "d['prs']['$stand_pr']['body'].splitlines().count(open('$WORK/mb-stand-line.txt').read().strip())" 2>/dev/null || true)
stand_blocked=$(project --repo "$MB" seat-failed mb-stand merger --seat claude/opus:high --error login)
stand_status=$(status_in "$MB" mb-stand)
rm "$MB/.lem/settings.local.toml"
(cd "$MB" && gh pr merge "$stand_pr" --squash --match-head-commit "$(mb_kept mb-stand proposed d)" --subject "fix: mb-stand" >/dev/null)
stand_merged=$(land --repo "$MB" merged mb-stand)
stand_too="- the merge agent was to be \`claude/opus:high\` in place of \`codex/gpt-6.2-sol:high\`: Codex had no tokens; then Claude Code gave an error too: Claude Code had no login"
printf '%s\n' "$stand_too" > "$WORK/mb-stand-too.txt"
stand_lines=$(gh_prs "$MB" "[d['prs']['$stand_pr']['body'].splitlines().count(open(f).read().strip()) for f in ('$WORK/mb-stand-line.txt', '$WORK/mb-stand-too.txt')]" 2>/dev/null || true)
if [ "$(field '(d["seat"]["seat"], d["seat"]["from"])' <<<"$stand_first")" = "('codex/gpt-6.2-sol:high', '.lem/settings.local.toml')" ] \
  && [ "$(field '(d["blocked"], d["seat"], d["from"])' <<<"$stood")" = "(False, 'claude/opus:high', 'stand-in')" ] \
  && [ "$(field '(d["seat"]["seat"], d["seat"]["from"], d["tip"], d["base"], d["brief"])' <<<"$stand_again")" \
    = "$(field '("claude/opus:high", "stand-in", d["tip"], d["base"], d["brief"])' <<<"$stand_first")" ] \
  && [ "$(field 'd["facts"]["stand_ins"]' <<<"$stand_again")" = "[{'seat': 'merger', 'took': 'claude/opus:high', 'failed': 'codex/gpt-6.2-sol:high', 'error': 'tokens', 'failed_too': None}]" ] \
  && [ "$(field '(d["by"], d["calls"])' <<<"$stand_read")" = "('claude/opus:high', False)" ] && [ "$(mb_kept mb-stand merge_review 'd["by"]')" = claude/opus:high ] \
  && [ "$(mb_logged mb-stand merge.review 'd["by"]')" = "['claude/opus:high', 'claude/opus:high']" ] \
  && [ "$stand_count" = 1 ] && [ "$stand_lines" = "[0, 1]" ] && [ "$(grep -cxF -- "$stand_line" "$MB/.lem/state/tasks/mb-stand/pr.md")" = 0 ] \
  && [ "$(grep -cxF -- "$stand_too" "$MB/.lem/state/tasks/mb-stand/pr.md")" = 1 ] \
  && [ "$(field 'd["blocked"]' <<<"$stand_blocked")" = True ] && [ "$(field 'd["say"]' <<<"$stand_blocked")" = "the merge agent \`claude/opus:high\` gave an error: no login, and it was the fallback" ] \
  && [ "$stand_status" = blocked ] && [ "$(field 'd["pull_request"]["number"]' <<<"$stand_merged")" = "$stand_pr" ] && [ "$(status_in "$MB" mb-stand)" = landed ]; then
  pass "a merge agent whose seat fails after the pull request is open: the fallback stands in on the same brief, the record names the seat kept with it whatever the settings say by then, the pull request's text and pr.md get its line once; a stand-in that fails too blocks the task, and a merge on GitHub while it waits lands it, its line replaced by the one that says it failed too"
else
  fail "a merge agent's stand-in: $stand_first / $stood / $stand_again / $stand_read / $stand_blocked / $stand_status / $stand_count / $stand_lines / $stand_merged"
fi

# A builder's rebase that stops twice: base met only the first commit's conflict, in stop-a.txt, and the builder's rebase
# stops again on the second commit, in stop-b.txt. The resolution names both, each file whose patch differs between the
# two ranges of its range-diff (letters.txt too, whose lines around the change the base changed), and no file that the
# rebase left as it was. The second commit's subject and its line of letters.txt are in Latin-1: a byte that is not
# UTF-8 stops nothing.
git -C "$MBX" pull -q --ff-only origin main && seq 1 30 > "$MBX/letters.txt"
git -C "$MBX" add letters.txt && git -C "$MBX" commit -q -m "docs: letters" && git -C "$MBX" push -q origin main
git -C "$MB" pull -q --ff-only origin main
mb_task mb-stops stop-a.txt
stops_tree=$(project --repo "$MB" worktree-dir mb-stops)
echo yes > "$stops_tree/stop-b.txt" && { seq 1 8; printf 'caf\xe9\n'; seq 10 19; printf '%s\n' a b c d; seq 24 30; } > "$stops_tree/letters.txt"
git -C "$stops_tree" add stop-b.txt letters.txt && git -C "$stops_tree" commit -q -m "$(printf 'fix: the second fil\xe9')" 2>/dev/null
land --repo "$MB" start mb-stops >/dev/null && land --repo "$MB" base mb-stops >/dev/null && polish_in "$MB" mb-stops
git -C "$MBX" pull -q --ff-only origin main && echo theirs > "$MBX/stop-a.txt" && echo theirs > "$MBX/stop-b.txt"
{ seq 1 6; echo seven; seq 8 30; } > "$MBX/letters.txt"
git -C "$MBX" add -A && git -C "$MBX" commit -q -m "fix: both files on main" && git -C "$MBX" push -q origin main
stops_met=$(land --repo "$MB" base mb-stops 2>/dev/null || true)
git -C "$stops_tree" rebase -q origin/main >/dev/null 2>&1 || true
echo yes > "$stops_tree/stop-a.txt" && git -C "$stops_tree" add stop-a.txt
GIT_EDITOR=true git -C "$stops_tree" rebase --continue >/dev/null 2>&1 || true
echo yes > "$stops_tree/stop-b.txt" && git -C "$stops_tree" add stop-b.txt
GIT_EDITOR=true git -C "$stops_tree" rebase --continue >/dev/null 2>&1
# a git older than 2.38, whose range-diff takes no path: base refuses with the fix, and keeps nothing, the polish pass's
# names among them
real_git=$(command -v git)
mkdir -p "$WORK/old-git"
cat > "$WORK/old-git/git" <<SH
#!/bin/sh
for a in "\$@"; do if [ "\$a" = range-diff ]; then echo "usage: git range-diff <old-base>..<old-tip> <new-base>..<new-tip>" >&2; exit 129; fi; done
exec "$real_git" "\$@"
SH
chmod +x "$WORK/old-git/git"
cp "$MB/.lem/state/tasks/mb-stops/landing.json" "$WORK/stops-kept.json"
stops_old=$(PATH="$WORK/old-git:$PATH" land --repo "$MB" base mb-stops 2>&1) && stops_code=0 || stops_code=$?
if [ "$stops_code" = 1 ] && grep -qF "git 2.38 or newer" <<<"$stops_old" && grep -qF "\`git --version\` says git version" <<<"$stops_old" \
  && ! grep -q Traceback <<<"$stops_old" && [ "$(mb_kept mb-stops polish 'd is not None')" = True ] \
  && cmp -s "$WORK/stops-kept.json" "$MB/.lem/state/tasks/mb-stops/landing.json"; then
  pass "base on a git whose range-diff takes no path refuses with what failed and the fix, and keeps nothing, the polish pass's names among them"
else
  fail "base on a git older than 2.38: $stops_code / $stops_old / $(diff "$WORK/stops-kept.json" "$MB/.lem/state/tasks/mb-stops/landing.json" || true)"
fi
stops=$(land --repo "$MB" base mb-stops 2>&1 || true)
if [ "$(field 'd["conflict"]' <<<"$stops_met")" = "['stop-a.txt']" ] && [ "$(field 'd["resolved"]' <<<"$stops")" = "['stop-a.txt']" ] \
  && [ "$(mb_kept mb-stops resolution 'd["files"]')" = "['letters.txt', 'stop-a.txt', 'stop-b.txt']" ]; then
  pass "a builder's rebase that stops on a later commit too: the resolution names the files of each stop, every file whose patch the rebase changed, for the read of the resolution"
else
  fail "a resolution over two stops: $stops_met / $stops / $(mb_kept mb-stops resolution d)"
fi
if [ "$(field 'd["tip"]' <<<"$stops" 2>&1)" = "$(git -C "$stops_tree" rev-parse HEAD)" ] && ! grep -q Traceback <<<"$stops"; then
  pass "a resolution whose changed line and whose commit's subject hold a byte that is not UTF-8 is read like any other: base takes it, with no traceback"
else
  fail "a resolution with a byte that is not UTF-8: $stops"
fi
project --repo "$MB" state mb-stops dropped "the test is over" >/dev/null

finish
