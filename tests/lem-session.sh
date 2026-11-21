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
made=$(calls_of session new)
want=$("$PY" -c 'import json, sys; print(json.dumps(sys.argv[1:]))' session new --workspace W-MINE --cwd "$R" --name gift-note --no-select --command \
  "$SHELL_LINE -l -c 'LEM_TASK=gift-note CLAUDE_CODE_AUTO_COMPACT_WINDOW=600000 claude --plugin-dir \"$PWD\" \"Read $STATE/tasks/gift-note/session.md and follow it.\"'" --json --socket "$WORK/agterm.sock")
brief=$(cat "$STATE/tasks/gift-note/session.md" 2>/dev/null || true)
if [ "$(field '(d["session"], d["phase"], d["already"])' <<<"$first" 2>&1)" = "('S-1', 'shape', False)" ] \
  && [ "$(field '(d["session"], d["already"])' <<<"$second" 2>&1)" = "('S-1', True)" ] \
  && [ "$made" = "$want" ] && calls_of move top | grep -qF '"S-1"' && [ -z "$(calls_of session select)" ] \
  && grep -qxF "Read $PWD/skills/lem/prompts/session.md and follow it." <<<"$brief" && grep -qxF "phase: shape" <<<"$brief" \
  && grep -qxF "opened because: new" <<<"$brief" && grep -qxF "worktree: none yet" <<<"$brief" \
  && [ "$(events)" = "[('session.open', 'S-1', 'shape', 'new')]" ] && git -C "$R" check-ignore -q "$STATE/tasks/gift-note/session.md"; then
  pass "open makes one session of the task in the caller's workspace, with no focus, LEM_TASK and the compaction number in its launch line and session.md as its first read, then moves it to the top and logs it; a second open prints the one that runs"
else
  fail "open twice: $first / $second / $made / $want / $brief / $(events)"
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

# The list: each task's newest session; a wake older than ten minutes whose line is still in the mailbox is unanswered.
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
if [ "$(field '[(s["task"], s["session"], s["phase"], s["live"], s["agent"], s["selected"], s["unanswered"]) for s in d]' <<<"$listed" 2>&1)" \
  = "[('gift-note', 'S-2', 'build', True, True, False, True), ('coupon-slug', 'S-3', 'shape', True, True, False, False)]" ] \
  && grep -qF '["msg", "read", "--as", "S-2:P-2", "--json"' "$CALLS"; then
  pass "list gives each task's newest session with its phase, whether it lives, runs an agent and is selected, and a wake whose line still waits in its mailbox after ten minutes as unanswered"
else
  fail "list: $listed"
fi

# The refusals of open: a parked task, one queued after a task that has not ended, and a task no workspace is known for;
# the owner's word on the board to a parked task wakes nobody and opens nothing, with no refusal.
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
  && grep -qF "the task 'csv-dates' is queued after 'gift-note', which has not ended" <<<"$queued" && [ "$(tail -n 1 <<<"$queued")" = "exit 1" ] \
  && grep -qF "no workspace of agterm is known for alone-task" <<<"$nowhere" && [ "$(tail -n 1 <<<"$nowhere")" = "exit 1" ] && [ "$told" = "(False, False)" ]; then
  pass "open refuses a parked task, a task queued after one that has not ended, and a task whose workspace nothing names, each with exit 1 and the fix; the owner's wake of a parked task opens nothing and refuses nothing"
else
  fail "the refusals of open: $parked / $queued / $nowhere / $told"
fi

# The wait: it ends when the task's state is one it names, and with the first event of a name logged after its start.
sess wait gift-note --until open,landed --every 0.1 > "$WORK/waited" 2>&1 &
waiter=$!
sess wait gift-note --event plan.talk --every 0.1 > "$WORK/talked" 2>&1 &
talker=$!
sleep 0.5
pr log gift-note plan.talk reviewer=codex turns:=2 questions:=0 settled:=0 open:=0 repaired:=0 design:=0 unargued:=0 root:=0 layer:=0 shared:=0 >/dev/null
wait "$talker"
pr state gift-note ready "the report is written" >/dev/null
pr state gift-note landing "the checks run" >/dev/null
pr state gift-note open "proposed" >/dev/null
wait "$waiter"
if [ "$(field '(d["status"], d["line"])' < "$WORK/waited" 2>&1)" = "('open', 'proposed')" ] && [ "$(field 'd["event"]["event"]' < "$WORK/talked" 2>&1)" = "plan.talk" ]; then
  pass "wait ends when the task's state is one it names, and at the first event of its name logged after its start"
else
  fail "wait: $(cat "$WORK/waited") / $(cat "$WORK/talked")"
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
