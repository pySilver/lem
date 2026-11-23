#!/usr/bin/env bash
# A task's own session (session.py), offline: a stand-in for agtermctl on PATH keeps agterm's tree in
# a file, records each call and answers as agterm does, in a throwaway repository with tasks in each
# phase. The copy of the talk reads a transcript written by hand under a HOME of the block's own.
export PYTHONDONTWRITEBYTECODE=1
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

SESSION=$PWD/skills/lem/scripts/session.py
BIN=$WORK/bin
CALLS=$WORK/calls
TREE=$WORK/tree.json
mkdir -p "$BIN"
agterm_standin "$BIN"
# Two workspaces: the caller's session sits in W-MINE, the owner looks at W-OTHER
printf '%s\n' '[{"id": "S-ASK", "name": "refund-rounding", "workspace": "W-MINE", "foreground": ["claude"]}, {"id": "S-HIS", "name": "notes", "workspace": "W-OTHER", "active": true}]' > "$TREE"

R=$WORK/shop
git init -q -b main "$R" && ident "$R" && project --repo "$R" init --base main >/dev/null 2>&1 && git -C "$R" add -A && git -C "$R" commit -q -m "chore: start"
STATE=$R/.lem/state
SHELL_LINE=$("$PY" -c 'import os, pwd; print(pwd.getpwuid(os.getuid()).pw_shell)')
# sess ARGS: lem session as a session of agterm runs it; AS=ID runs it from another session, AS= from no session
sess() {
  env CALLS="$CALLS" TREE="$TREE" MAILBOX="${MAILBOX:-[]}" PATH="$BIN:$PATH" AGTERM_SESSION_ID="${AS-S-ASK}" AGTERM_SOCKET="$WORK/agterm.sock" AGTERM_WINDOW_ID= \
    "$PY" -B "$SESSION" --repo "$R" "$@"
}
pr() { project --repo "$R" "$@"; }
calls_of() { grep -F "\"$1\"" "$CALLS" | grep -F "\"$2\"" || true; }
events() { "$PY" -c 'import json, sys; print([(r["event"], r.get("session"), r.get("phase"), r.get("why")) for r in map(json.loads, open(sys.argv[1])) if r["event"].startswith("session.")])' "$STATE/events.jsonl"; }

pr task-dir gift-note --ask "the export holds the gift note" >/dev/null
pr state gift-note held "the interview waits for the owner" "type: feat, because the export gets a column" >/dev/null

# A new task's session: one `session new` in the caller's workspace, with no focus, the task's two variables and
# its first read, then at the top of the workspace; a second open while it runs prints the same one.
rm -f "$CALLS"
first=$(sess open gift-note --why new 2>&1 || true)
second=$(AS="" sess open gift-note --why dead 2>&1 || true)
focused=$(sess open gift-note --focus 2>&1; echo "exit $?")
# the launch line as its two levels read it: agterm's words, then the login shell's words of the -c string
made=$(calls_of session new | "$PY" -c 'import json, shlex, sys
call = json.loads(sys.stdin.read())
at = call.index("--command") + 1
outer = shlex.split(call[at])
call[at] = outer[:3] + [shlex.split(outer[3])]
print(json.dumps(call))')
want=$("$PY" -c 'import json, sys; print(json.dumps(sys.argv[1:]))' session new --workspace W-MINE --cwd "$R" --name gift-note --no-select --command \
  --json --socket "$WORK/agterm.sock" | "$PY" -c 'import json, sys
call = json.loads(sys.stdin.read())
call.insert(call.index("--command") + 1, [sys.argv[1], "-l", "-c", ["LEM_TASK=gift-note", "CLAUDE_CODE_AUTO_COMPACT_WINDOW=600000", "claude", "--model", "opus", "--effort", "high", "--plugin-dir", sys.argv[2], f"Read {sys.argv[3]} and follow it."]])
print(json.dumps(call))' "$SHELL_LINE" "$PWD" "$STATE/tasks/gift-note/session.md")
brief=$(cat "$STATE/tasks/gift-note/session.md" 2>/dev/null || true)
if [ "$(field '(d["session"], d["phase"], d["already"])' <<<"$first" 2>&1)" = "('S-1', 'shape', False)" ] \
  && [ "$(field '(d["session"], d["already"])' <<<"$second" 2>&1)" = "('S-1', True)" ] \
  && [ "$made" = "$want" ] && calls_of move top | grep -qF '"S-1"' && [ -z "$(calls_of session select)" ] \
  && grep -qF "unrecognized arguments: --focus" <<<"$focused" && [ "$(tail -n 1 <<<"$focused")" = "exit 2" ] \
  && [ "$(head -n 1 <<<"$brief")" = "Read \`skills/lem/prompts/session.md\` in the folder that \`lem version\` prints as \`root\`, and follow it; when \`lem version\` fails, stop and say that \`lem\` is not on the PATH, with \`lem doctor\` as the check." ] \
  && ! grep -qF "$PWD/skills" <<<"$brief" && grep -qxF "phase: shape" <<<"$brief" \
  && grep -qxF "opened because: new" <<<"$brief" && grep -qxF "worktree: none yet" <<<"$brief" \
  && [ "$(events)" = "[('session.open', 'S-1', 'shape', 'new')]" ] && git -C "$R" check-ignore -q "$STATE/tasks/gift-note/session.md"; then
  pass "open makes one session of the task in the caller's workspace, with no focus and no flag that gives it, LEM_TASK, the compaction number and Lem's default seat in its launch line and session.md as its first read, which names its standing text through lem version and no folder of the Lem that wrote it, then moves it to the top and logs it; a second open prints the one that runs"
else
  fail "open twice: $first / $second / $focused / $made / $want / $brief / $(events)"
fi

# The change of phase: the lead's state and handoff.md, then next from the shape session: a fresh session for
# the build in the main checkout, the old one named handed off, and the line that closes it once he left it.
pr state gift-note building "lead: session" >/dev/null
printf '%s\n' 'task: gift-note' '' '## Settled' '' '- the criteria' > "$STATE/tasks/gift-note/handoff.md"
early=$(AS=S-1 sess next gift-note 2>&1; echo "exit $?")
tree_dir=$(pr worktree-dir gift-note)
git -C "$R" worktree add -q "$tree_dir" -b feat/gift-note main
printf '%s\n' "task: gift-note · from shape · written: $(date -u +%Y-%m-%dT%H:%MZ)" '' '## Settled' '' '- the criteria' '' '## Open' '' 'none' '' \
  '## Next step' '' 'Plan the column.' '' '## Failed' '' 'none' '' '## Changed files' '' 'none' > "$STATE/tasks/gift-note/handoff.md"
rm -f "$CALLS"
handed=$(AS=S-1 sess next gift-note 2>&1 || true)
if grep -qF "is not in the form of \`templates/handoff.md\`" <<<"$early" && [ "$(tail -n 1 <<<"$early")" = "exit 1" ] \
  && [ "$(field '(d["session"], d["phase"], d["old"], d["from"], d["close"])' <<<"$handed" 2>&1)" = "('S-2', 'build', 'S-1', 'shape', 'lem session close gift-note --session S-1 --why handoff --when-unselected')" ] \
  && ! grep -qF "\"--cwd\", \"$tree_dir\"" <<<"$(calls_of session new)" && grep -qxF "worktree: $tree_dir" "$(pr task-dir gift-note)/session.md" && grep -qF '"rename", "gift-note \u00b7 handed off", "--target", "S-1"' "$CALLS" \
  && [ "$(events)" = "[('session.open', 'S-1', 'shape', 'new'), ('session.open', 'S-2', 'build', 'handoff')]" ]; then
  pass "next refuses a handoff.md that is not in its form, then opens a fresh session for the build in the main checkout, with the task's worktree named in session.md, names the old one handed off, logs it and prints the line that closes the old one"
else
  fail "next: $early / $handed / $(cat "$CALLS") / $(events)"
fi

same=$(AS=S-2 sess next gift-note 2>&1; echo "exit $?")
if grep -qF "the state of gift-note still gives the phase build: write the new state block first" <<<"$same" && [ "$(tail -n 1 <<<"$same")" = "exit 1" ]; then
  pass "next refuses while the state still gives the caller's phase, and names --same for the owner's hand off"
else
  fail "next in the same phase: $same"
fi

# The close: never a session the owner has selected, unless it waits until he left it; then logged and closed undoable.
"$PY" -c 'import json, sys; n = json.load(open(sys.argv[1])); [x.update(active=(x["id"] == "S-1")) for x in n]; json.dump(n, open(sys.argv[1], "w"))' "$TREE"
refused=$(sess close gift-note --session S-1 --why handoff 2>&1; echo "exit $?")
sess close gift-note --session S-1 --why handoff --when-unselected --every 0.1 > "$WORK/closed" 2>&1 &
waiter=$!
sleep 0.5
still=$(calls_of session close)
"$PY" -c 'import json, sys; n = json.load(open(sys.argv[1])); [x.update(active=(x["id"] == "S-HIS")) for x in n]; json.dump(n, open(sys.argv[1], "w"))' "$TREE"
wait "$waiter"
if grep -qF "the owner has the session \`gift-note · handed off\` selected" <<<"$refused" && [ "$(tail -n 1 <<<"$refused")" = "exit 1" ] && [ -z "$still" ] \
  && [ "$(field 'd["closed"]' < "$WORK/closed" 2>&1)" = True ] && grep -qF '"session", "close", "--target", "S-1", "--undoable"' "$CALLS" \
  && grep -qF "('session.close', 'S-1', None, 'handoff')" <<<"$(events)"; then
  pass "close refuses a session the owner has selected; with --when-unselected it waits until he left it, logs the close and closes it with agterm's undo"
else
  fail "close: $refused / $still / $(cat "$WORK/closed") / $(events)"
fi

# A close that waits gives up on a session woken after it started: the owner keeps the session of a queued task
# selected, its task ends, and the server's wake (`lem: SLUG queue`) gives it work again, which no close may end.
"$PY" -c 'import json, sys; n = json.load(open(sys.argv[1])); [x.update(active=(x["id"] == "S-2")) for x in n]; json.dump(n, open(sys.argv[1], "w"))' "$TREE"
rm -f "$CALLS"
sess close gift-note --session S-2 --why handoff --when-unselected --every 0.1 > "$WORK/kept" 2>&1 &
waiter=$!
# the close has read the log once it asks agterm for the tree
for _ in $(seq 50); do grep -qF '"tree"' "$CALLS" 2>/dev/null && break; sleep 0.1; done
AS="" sess wake gift-note --why queue >/dev/null 2>&1
for _ in $(seq 50); do kill -0 "$waiter" 2>/dev/null || break; sleep 0.1; done
# a close that did not give up still runs in the subshell's child: end it too, so that it closes no session
# when the owner leaves S-2 below and the checks after this one meet the same sessions
pkill -P "$waiter" 2>/dev/null || true
kill "$waiter" 2>/dev/null || true
wait "$waiter" 2>/dev/null || true
"$PY" -c 'import json, sys; n = json.load(open(sys.argv[1])); [x.update(active=(x["id"] == "S-HIS")) for x in n]; json.dump(n, open(sys.argv[1], "w"))' "$TREE"
if [ "$(field '(d["closed"], d["woken"])' < "$WORK/kept" 2>&1)" = "(False, True)" ] && ! grep -qF '"session", "close", "--target", "S-2"' "$CALLS" \
  && ! grep -qF "('session.close', 'S-2'" <<<"$(events)" && grep -qF "('session.wake', 'S-2', None, 'queue')" <<<"$(events)"; then
  pass "close --when-unselected ends with no close and no record when the session is woken while it waits"
else
  fail "close after a wake: $(cat "$WORK/kept") / $(cat "$CALLS") / $(events)"
fi

# The wake: a live session gets the pane message and the record; a task with none gets a new session.
pr task-dir coupon-slug --ask "the coupon has a slug" >/dev/null
pr state coupon-slug held "the interview waits for the owner" "type: feat, because a coupon gets a slug" >/dev/null
rm -f "$CALLS"
woke=$(AS="" sess wake gift-note --why conflict --head abc123 2>&1 || true)
opened=$(AS="" sess wake coupon-slug --why queue 2>&1 || true)
if [ "$(field '(d["woke"], d["session"])' <<<"$woke" 2>&1)" = "(True, 'S-2')" ] && grep -qF '["msg", "send", "lem: gift-note conflict", "--to", "S-2:left", "--socket"' "$CALLS" \
  && [ "$(field '(d["woke"], d["opened"], d["session"], d["phase"])' <<<"$opened" 2>&1)" = "(False, True, 'S-3', 'shape')" ] \
  && grep -qF '"--workspace", "W-MINE"' <<<"$(calls_of session new)" \
  && [ "$(tail -n 1 "$STATE/events.jsonl" | field '(d["event"], d["why"])')" = "('session.open', 'queue')" ] \
  && grep -qF '"event": "session.wake", "task": "gift-note", "session": "S-2", "why": "conflict", "head": "abc123"' "$STATE/events.jsonl"; then
  pass "wake sends lem: SLUG WHY to the left pane of the task's live session and keeps the head on its record; a task with no session gets one, in the repository's newest workspace when nothing else names one"
else
  fail "wake: $woke / $opened / $(cat "$CALLS")"
fi

# The list: each task's newest session, with the phase its task is in now beside the one it opened in; a wake older
# than ten minutes whose line is still in the mailbox is unanswered.
pr state coupon-slug building "small change: one builder" "type: feat, because a coupon gets a slug" >/dev/null
"$PY" - "$STATE/events.jsonl" <<'PY'
import json, sys
lines = open(sys.argv[1]).read().splitlines()
out = []
for line in lines:
    record = json.loads(line)
    if record["event"] == "session.wake":
        record["ts"] = "2026-11-20T08:00:00Z"
    out.append(json.dumps(record))
open(sys.argv[1], "w").write("\n".join(out) + "\n")
PY
"$PY" - "$STATE/events.jsonl" <<'PY'
import json, sys
# the wake is older than the session it was sent to only through the edit above: the open moves back too
lines = [json.loads(line) for line in open(sys.argv[1])]
for record in lines:
    if record["event"] == "session.open" and record["session"] == "S-2":
        record["ts"] = "2026-11-20T07:00:00Z"
open(sys.argv[1], "w").write("".join(json.dumps(record) + "\n" for record in lines))
PY
listed=$(MAILBOX='{"result": {"messages": [{"body": "lem: gift-note conflict"}]}}' sess list 2>&1 || true)
if [ "$(field '[(s["task"], s["session"], s["phase"], s["opened_in"], s["live"], s["agent"], s["selected"], s["unanswered"]) for s in d]' <<<"$listed" 2>&1)" \
  = "[('gift-note', 'S-2', 'build', 'build', True, True, False, True), ('coupon-slug', 'S-3', 'fast', 'shape', True, True, False, False)]" ] \
  && grep -qF '["msg", "read", "--as", "S-2:P-2", "--json"' "$CALLS"; then
  pass "list gives each task's newest session with the phase its task is in now (a fast track's, not the shape it opened in), whether it lives, runs an agent and is selected, and a wake whose line still waits in its mailbox after ten minutes as unanswered"
else
  fail "list: $listed"
fi

# The refusals of open: a parked task, one queued after a task that has not ended, and a task no workspace is known for;
# the owner's word on the board to a parked task wakes nobody and opens nothing, with no refusal.
pr state coupon-slug held "the interview waits for the owner" >/dev/null
pr state coupon-slug parked "put aside" >/dev/null
pr task-dir csv-dates --ask "the CSV dates stay whole" >/dev/null
pr state csv-dates queued "needs the export's column" "after: gift-note" >/dev/null
parked=$(sess open coupon-slug 2>&1; echo "exit $?")
pr task-dir old-note --ask "the old note goes" >/dev/null && pr state old-note held "the interview waits for the owner" >/dev/null && pr state old-note parked "put aside" >/dev/null
told=$(AS="" sess wake old-note --why owner 2>/dev/null | field '(d["woke"], d["opened"])' 2>&1 || true)
queued=$(sess open csv-dates --why queue 2>&1; echo "exit $?")
R2=$WORK/lonely && git init -q -b main "$R2" && ident "$R2" && project --repo "$R2" init --base main >/dev/null 2>&1 && project --repo "$R2" task-dir alone-task >/dev/null
nowhere=$(env CALLS="$CALLS" TREE="$TREE" PATH="$BIN:$PATH" AGTERM_SESSION_ID= AGTERM_SOCKET= AGTERM_WINDOW_ID= "$PY" -B "$SESSION" --repo "$R2" open alone-task 2>&1; echo "exit $?")
if grep -qF "lem session: the task 'coupon-slug' is parked" <<<"$parked" && [ "$(tail -n 1 <<<"$parked")" = "exit 1" ] \
  && grep -qF "the task 'csv-dates' is queued after 'gift-note', which has not ended: it gets its session when gift-note is landed or answered, and when gift-note is dropped it waits for the owner's word" <<<"$queued" \
  && [ "$(tail -n 1 <<<"$queued")" = "exit 1" ] \
  && grep -qF "no workspace of agterm is known for alone-task" <<<"$nowhere" && [ "$(tail -n 1 <<<"$nowhere")" = "exit 1" ] && [ "$told" = "(False, False)" ]; then
  pass "open refuses a parked task, a task queued after one that has not ended, and a task whose workspace nothing names, each with exit 1 and the fix; the owner's wake of a parked task opens nothing and refuses nothing"
else
  fail "the refusals of open: $parked / $queued / $nowhere / $told"
fi

# The wait: it ends when the task's state is one it names, and with the first event of a name logged after its start.
sess wait gift-note --until open,landed --every 0.1 > "$WORK/waited" 2>&1 &
waiter=$!
# a plan.talk logged before the event waiter starts, which it does not count; the next one is logged again until the
# waiter ends (60 s at most), since nothing tells when a waiter in the background has started under the load of all.sh
pr log gift-note plan.talk reviewer=codex turns:=2 questions:=0 settled:=0 open:=0 repaired:=0 design:=0 unargued:=0 root:=0 layer:=0 shared:=0 >/dev/null
sess wait gift-note --event plan.talk --every 0.1 > "$WORK/talked" 2>&1 &
talker=$!
tries=0
while kill -0 "$talker" 2>/dev/null && [ "$tries" -lt 600 ]; do
  pr log gift-note plan.talk reviewer=codex turns:=3 questions:=0 settled:=0 open:=0 repaired:=0 design:=0 unargued:=0 root:=0 layer:=0 shared:=0 >/dev/null
  tries=$((tries + 1))
  sleep 0.1
done
kill "$talker" 2>/dev/null || true
wait "$talker" || true
pr state gift-note ready "the report is written" >/dev/null
pr state gift-note landing "the checks run" >/dev/null
pr state gift-note open "proposed" >/dev/null
wait "$waiter"
# a companion the waiting session opened (the plan talk's pair) gone before the state came: the wait ends, and names it
"$PY" -c 'import json, sys; n = json.load(open(sys.argv[1])); n.append({"id": "C-9", "name": "gift-note · plan talk", "parent": "S-2", "workspace": "W-MINE", "foreground": ["/bin/zsh", "-l", "-c", "claude \"Read b and follow it.\""]}); json.dump(n, open(sys.argv[1], "w"))' "$TREE"
sess wait gift-note --until landed --companion C-9 --every 0.1 > "$WORK/companion" 2>&1 &
waiter=$!
sleep 0.3
companion_lived=$(jobs -r | wc -l | tr -d ' ')
"$PY" -c 'import json, sys; n = json.load(open(sys.argv[1])); json.dump([x for x in n if x["id"] != "C-9"], open(sys.argv[1], "w"))' "$TREE"
wait "$waiter"
# its session gone from agterm's tree: the wait ends with it, and says so
sess wait gift-note --until landed --every 0.1 > "$WORK/gone" 2>&1 &
waiter=$!
sleep 0.3
"$PY" -c 'import json, sys; n = json.load(open(sys.argv[1])); json.dump([x for x in n if x["id"] != "S-2"], open(sys.argv[1], "w"))' "$TREE"
wait "$waiter"
if [ "$(field '(d["status"], d["line"], d["gone"])' < "$WORK/waited" 2>&1)" = "('open', 'proposed', False)" ] && [ "$(field '(d["event"]["event"], d["event"]["turns"])' < "$WORK/talked" 2>&1)" = "('plan.talk', 3)" ] \
  && [ "$(field '(d["gone"], d["session"], d["status"])' < "$WORK/gone" 2>&1)" = "(True, 'S-2', 'open')" ] && grep -qF "lem session open gift-note --why dead" "$WORK/gone" \
  && [ "$companion_lived" = 1 ] && [ "$(field '(d["gone"], d["companion"], d["status"])' < "$WORK/companion" 2>&1)" = "(True, 'C-9', 'open')" ] && grep -qF "## Plan talk" "$WORK/companion"; then
  pass "wait ends when the task's state is one it names, at the first event of its name logged after its start, when the task's session is gone, and with --companion when that companion is gone, which it says"
else
  fail "wait: $(cat "$WORK/waited") / $(cat "$WORK/talked") / $(cat "$WORK/gone") / $companion_lived $(cat "$WORK/companion")"
fi

# The first line to the caller: open --why new prints the wait for it, which ends with the line of the task's first
# block, written while it runs, in the form for another session.
pr task-dir footer-terms --ask "the footer says Terms, not Terms and Conditions" >/dev/null
opened=$(sess open footer-terms --why new 2>&1 || true)
sess wait footer-terms --first-line --every 0.1 > "$WORK/first-line" 2>&1 &
waiter=$!
sleep 0.3
printf '%s\n' '## Acceptance criteria' '' 'Size: small, because one word.' '' '1. The footer says Terms.' > "$STATE/tasks/footer-terms/criteria.md"
printf '%s\n' "Read \`skills/lem/prompts/small.md\` in the folder that \`lem version\` prints as \`root\`, and follow it; when \`lem version\` fails, stop and say that \`lem\` is not on the PATH, with \`lem doctor\` as the check." 'task: footer-terms' 'branch: fix/footer-terms' > "$STATE/tasks/footer-terms/brief.md"
pr state footer-terms building "small change: one builder" "type: fix, because the footer is wrong today" >/dev/null
wait "$waiter"
if [ "$(field 'd["then"]' <<<"$opened" 2>&1)" = "lem session wait footer-terms --first-line" ] && [ "$(field 'd["gone"]' < "$WORK/first-line" 2>&1)" = False ] \
  && [ "$(field 'd["say"]' < "$WORK/first-line" 2>&1)" = 'footer-terms · fix: "the footer says Terms". Branch fix/footer-terms. Fast track: one builder, the checks, one read, then the pull request. Nothing waits for you. Wrong read? /lem standard-track footer-terms, /lem be-careful footer-terms.' ]; then
  pass "open --why new prints the wait for the first line, which ends when the task's first block is written, with the line that names the task and its commands"
else
  fail "the first line to the caller: $opened / $(cat "$WORK/first-line")"
fi

# The copy of the talk: the owner's turns and the agent's, word for word.
SID=4f1e2d3c-0000-4000-8000-00000000a11c
mkdir -p "$WORK/home/.claude/projects/-shop"
"$PY" - "$WORK/home/.claude/projects/-shop/$SID.jsonl" <<'PY'
import json, sys
def typed(text, at):
    return {"type": "user", "origin": {"kind": "human"}, "timestamp": at, "message": {"role": "user", "content": text}}
def said(text, at):
    return {"type": "assistant", "timestamp": at, "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}
records = [
    typed("The slip prints one note.", "2026-11-19T08:00:00Z"), said("Yes, one cell.", "2026-11-19T08:00:04Z"),
    typed("The export should carry the gift note too.", "2026-11-19T09:00:00Z"), said("The export has no note column today.", "2026-11-19T09:00:06Z"),
    typed("Also: are the backups green?", "2026-11-19T09:05:00Z"), said("The backups ran at 03:00.", "2026-11-19T09:05:03Z"),
    {"type": "user", "origin": {"kind": "human"}, "timestamp": "2026-11-19T09:10:00Z",
     "message": {"content": "<command-message>lem:lem</command-message>\n<command-name>/lem:lem</command-name>\n<command-args>the export holds the gift note</command-args>"}},
    {"type": "user", "isMeta": True, "timestamp": "2026-11-19T09:10:00Z", "message": {"content": [{"type": "text", "text": "Base directory for this skill: /x"}]}},
    said("feat: the export holds the gift note. Standard track.", "2026-11-19T09:10:08Z"),
]
open(sys.argv[1], "w").write("".join(json.dumps(record) + "\n" for record in records))
PY
copied=$(env -u CLAUDE_CONFIG_DIR HOME="$WORK/home" CLAUDE_CODE_SESSION_ID="$SID" "$PY" -B "$SESSION" --repo "$R" talk gift-note --from "The export should" --leave "Also: are the backups" 2>&1 || true)
page=$(cat "$STATE/tasks/gift-note/talk.md" 2>/dev/null || true)
if [ "$(field '[d["turns"], d["owner_turns"], [i["words"] for i in d["left_out"]]]' <<<"$copied" 2>&1)" = "[4, 2, ['Also: are the backups green?']]" ] \
  && grep -qxF "/lem the export holds the gift note" <<<"$page" && grep -qxF "The export has no note column today." <<<"$page" \
  && ! grep -qF "Base directory" <<<"$page" && ! grep -qF "The slip prints" <<<"$page"; then
  pass "talk copies the session's turns word for word from the owner's turn where the topic began, his /lem line as he typed it, and leaves out a turn of another topic and the skill's text"
else
  fail "the copy of the talk: $copied / $page"
fi

finish
