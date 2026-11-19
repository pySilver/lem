#!/usr/bin/env bash
# The companion of a need (companion.py), offline: a stand-in for agtermctl on PATH keeps a tree of
# sessions in a file, records each call and answers as agterm does, in a throwaway repository with
# tasks whose interview, criteria or choice waits for the owner. The copy of the talk reads a
# transcript written by hand under a HOME of the block's own.
export PYTHONDONTWRITEBYTECODE=1
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

COMPANION=$PWD/skills/lem/scripts/companion.py
BIN=$WORK/bin
CALLS=$WORK/calls
TREE=$WORK/tree.json
mkdir -p "$BIN"
# The stand-in: each call one JSON line in CALLS; `tree` gives the sessions of TREE, `session new` adds one
# (S-1, S-2, ...) under its --parent, `session close` takes its --target away.
{
  printf '#!%s\n' "$PY"
  cat <<'STANDIN'
import json, os, sys
args = sys.argv[1:]
with open(os.environ["CALLS"], "a") as calls:
    calls.write(json.dumps(args) + "\n")
nodes = json.load(open(os.environ["TREE"]))
def value(flag):
    return args[args.index(flag) + 1]
if args[:1] == ["tree"]:
    print(json.dumps({"result": {"tree": {"workspaces": [{"sessions": nodes}]}}}))
elif args[:2] == ["session", "new"]:
    # each new session a number of its own, never one a closed session had
    count = os.environ["TREE"] + ".count"
    number = int(open(count).read()) + 1 if os.path.exists(count) else 1
    open(count, "w").write(str(number))
    made = {"id": "S-%d" % number, "name": value("--name"), "parent": value("--parent")}
    nodes.append(made)
    json.dump(nodes, open(os.environ["TREE"], "w"))
    print(json.dumps({"result": {"id": made["id"]}}))
elif args[:2] == ["session", "close"]:
    json.dump([node for node in nodes if node["id"] != value("--target")], open(os.environ["TREE"], "w"))
STANDIN
} > "$BIN/agtermctl"
chmod +x "$BIN/agtermctl"
printf '%s\n' '[{"id": "S-LEM", "name": "Lem · shop"}]' > "$TREE"

R=$WORK/shop
git init -q -b main "$R" && ident "$R" && project --repo "$R" init --base main >/dev/null && git -C "$R" add -A && git -C "$R" commit -q -m "chore: start"
STATE=$R/.lem/state
# comp ARGS: lem companion as Lem's session runs it; AS=ID runs it from another session
comp() {
  env CALLS="$CALLS" TREE="$TREE" PATH="$BIN:$PATH" AGTERM_SESSION_ID="${AS:-S-LEM}" AGTERM_PANE_ID=P-LEM AGTERM_SOCKET="$WORK/agterm.sock" AGTERM_WINDOW_ID=W1 \
    "$PY" -B "$COMPANION" --repo "$R" "$@"
}
pr() { project --repo "$R" "$@"; }
SHELL_LINE=$("$PY" -c 'import os, pwd; print(pwd.getpwuid(os.getuid()).pw_shell)')

# Lem's transcript, by hand: an older talk, a compaction, the owner's turn where the topic began, a turn of
# another topic, and his /lem line with the text the skill loads after it.
SID=4f1e2d3c-0000-4000-8000-00000000a11c
mkdir -p "$WORK/home/.claude/projects/-shop"
"$PY" - "$WORK/home/.claude/projects/-shop/$SID.jsonl" <<'PY'
import json, sys
def typed(text, at):
    return {"type": "user", "origin": {"kind": "human"}, "promptSource": "typed", "timestamp": at, "message": {"role": "user", "content": text}}
def said(text, at):
    return {"type": "assistant", "timestamp": at, "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}
records = [
    typed("The slip prints one note.", "2026-11-19T08:00:00Z"), said("Yes, one cell.", "2026-11-19T08:00:04Z"),
    {"type": "system", "subtype": "compact_boundary", "timestamp": "2026-11-19T08:30:00Z"},
    typed("The export should carry the gift note too.", "2026-11-19T09:00:00Z"), said("The export has no note column today.", "2026-11-19T09:00:06Z"),
    typed("Also: are the backups green?", "2026-11-19T09:05:00Z"), said("The backups ran at 03:00.", "2026-11-19T09:05:03Z"),
    {"type": "user", "origin": {"kind": "human"}, "timestamp": "2026-11-19T09:10:00Z",
     "message": {"content": "<command-message>lem:lem</command-message>\n<command-name>/lem:lem</command-name>\n<command-args>the export holds the gift note</command-args>"}},
    {"type": "user", "isMeta": True, "timestamp": "2026-11-19T09:10:00Z", "message": {"content": [{"type": "text", "text": "Base directory for this skill: /x"}]}},
    said("feat: the export holds the gift note. Standard track.", "2026-11-19T09:10:08Z"),
    typed("/lem the report dates stay whole", "2026-11-19T09:20:00Z"), said("feat: the report dates stay whole.", "2026-11-19T09:20:05Z"),
]
open(sys.argv[1], "w").write("".join(json.dumps(record) + "\n" for record in records))
PY
talk() { env -u CLAUDE_CONFIG_DIR HOME="$WORK/home" CLAUDE_CODE_SESSION_ID="$SID" "$PY" -B "$COMPANION" --repo "$R" talk "$@"; }

pr task-dir gift-note --ask "the export holds the gift note" >/dev/null
pr state gift-note held "the interview waits for the owner" "type: feat, because the export gets a column" >/dev/null
# the second ask started on the fast track, and /lem standard-track gave it an interview
pr task-dir report-dates --ask "the report dates stay whole" >/dev/null
pr state report-dates building "small change: one builder" "type: fix, because the dates are cut" >/dev/null
pr state report-dates held "the interview waits for the owner" "type: fix, because the dates are cut" >/dev/null

copied=$(talk gift-note --from "The export should" --leave "Also: are the backups" --leave "/lem the report dates" 2>&1 || true)
page=$(cat "$STATE/tasks/gift-note/talk.md" 2>/dev/null || true)
if [ "$(field '[d["turns"], d["owner_turns"], [i["words"] for i in d["left_out"]]]' <<<"$copied" 2>&1)" = "[4, 2, ['Also: are the backups green?', '/lem the report dates stay whole']]" ] \
  && grep -qxF "/lem the export holds the gift note" <<<"$page" && grep -qxF "The export has no note column today." <<<"$page" \
  && ! grep -qF "Base directory" <<<"$page" && ! grep -qF "The backups ran" <<<"$page" && ! grep -qF "The slip prints" <<<"$page" \
  && grep -qF "the owner's turn of 2026-11-19 09:05 UTC that starts \"Also: are the backups green?\", with 1 turn of Lem after it" <<<"$page"; then
  pass "talk copies Lem's turns word for word from the owner's turn where the topic began, his /lem line as he typed it, and names each turn left out by its time and first words; the skill's text is no turn of his"
else
  fail "the copy of the talk: $copied / $page"
fi

no_id=$(env -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CONFIG_DIR HOME="$WORK/home" "$PY" -B "$COMPANION" --repo "$R" talk gift-note --from x 2>&1; echo "exit $?")
no_file=$(env -u CLAUDE_CONFIG_DIR HOME="$WORK/nowhere" CLAUDE_CODE_SESSION_ID="$SID" "$PY" -B "$COMPANION" --repo "$R" talk gift-note --from x 2>&1; echo "exit $?")
no_turn=$(talk gift-note --from "Nothing he said" 2>&1; echo "exit $?")
if [ "$(tail -n 1 <<<"$no_id")" = "exit 1" ] && grep -qF "lem companion: CLAUDE_CODE_SESSION_ID is not set" <<<"$no_id" \
  && [ "$(tail -n 1 <<<"$no_file")" = "exit 1" ] && grep -qF "no transcript $SID.jsonl under $WORK/nowhere/.claude/projects" <<<"$no_file" \
  && [ "$(tail -n 1 <<<"$no_turn")" = "exit 1" ] && grep -qF "no turn of the owner starts with 'Nothing he said'" <<<"$no_turn"; then
  pass "talk refuses with exit 1 and the fix when the session's id is not set, its transcript is not there, or no owner turn starts with the text"
else
  fail "the refusals of talk: $no_id / $no_file / $no_turn"
fi

# Two interviews open at once, each a companion under Lem's session, with no focus.
no_talk=$(comp open report-dates --need interview 2>&1; echo "exit $?")
talk report-dates --from "/lem the report dates" >/dev/null
rm -f "$CALLS"
first=$(comp open gift-note --need interview 2>&1 || true)
second=$(comp open report-dates --need interview 2>&1 || true)
made=$(grep '"new"' "$CALLS" || true)
want_cmd="$SHELL_LINE -l -c 'claude \"Read $STATE/tasks/gift-note/companion-interview.md and follow it.\"'"
if [ "$(field 'd["say"]' <<<"$first" 2>&1)" = "the interview of gift-note is open in \`gift-note · interview\` under this session" ] \
  && [ "$(field 'd["say"]' <<<"$second" 2>&1)" = "the interview of report-dates is open in \`report-dates · interview\` under this session" ] \
  && [ "$(grep -c . <<<"$made")" = 2 ] && [ "$(head -n 1 <<<"$made")" = "$("$PY" -c 'import json, sys; print(json.dumps(sys.argv[1:]))' session new --parent S-LEM --cwd "$R" --name "gift-note · interview" --no-select --command "$want_cmd" --json --socket "$WORK/agterm.sock")" ] \
  && ! grep -qF -- "--model" <<<"$made" && [ "$(tail -n 1 <<<"$no_talk")" = "exit 1" ] && grep -qF "has no talk.md in its task directory" <<<"$no_talk"; then
  pass "two interviews open at once, each under Lem's session with its fixed name, no focus, the main checkout, the owner's default Claude and the brief; an interview with no copied talk is refused"
else
  fail "two interviews: $first / $second / $made / $no_talk"
fi

brief=$(cat "$STATE/tasks/gift-note/companion-interview.md" 2>/dev/null || true)
again=$(comp open gift-note --need interview 2>&1 || true)
listed=$(comp list 2>&1 || true)
if grep -qxF "Read $PWD/skills/lem/prompts/companion.md and follow it." <<<"$brief" && grep -qxF "coordinator: S-LEM:P-LEM" <<<"$brief" \
  && grep -qxF "socket: $WORK/agterm.sock" <<<"$brief" && grep -qxF "lem session: Lem · shop" <<<"$brief" && grep -qxF "need: interview" <<<"$brief" \
  && [ "$(field 'd["already"]' <<<"$again" 2>&1)" = True ] && [ "$(grep -c '"new"' "$CALLS")" = 2 ] \
  && [ "$(field '[c["name"] for c in d]' <<<"$listed" 2>&1)" = "['gift-note · interview', 'report-dates · interview']" ] \
  && git -C "$R" check-ignore -q "$STATE/tasks/gift-note/talk.md" && git -C "$R" check-ignore -q "$STATE/tasks/gift-note/companion-interview.md" \
  && [ -z "$(git -C "$R" status --porcelain --untracked-files=all)" ]; then
  pass "the brief names the companion's stage, the task, Lem's address and Lem's session as the sidebar shows it; a need whose companion runs is not opened twice; list shows both; the copy of the talk and the brief stay in the state folder git ignores"
else
  fail "the brief, a second open, the list: $brief / $again / $listed / $(git -C "$R" status --porcelain --untracked-files=all)"
fi

# His yes in the companion: the approval on record gives the start, and the companion that runs is due its close.
printf '%s\n' '## Acceptance criteria' '' 'Size: full, because the export gets a column.' '' '1. The export of order 1042 holds its gift note.' > "$WORK/criteria.md"
"$PY" -B "$CRITERIA" --repo "$R" approve gift-note --file "$WORK/criteria.md" >/dev/null
owed=$(comp due 2>&1 || true)
closed=$(comp close gift-note --need interview --why answered 2>&1 || true)
twice=$(comp close gift-note --need interview --why answered 2>&1; echo "exit $?")
after=$(comp due 2>&1 || true)
if [ "$(field '[s["name"] for s in d["start"]]' <<<"$owed" 2>&1)" = "['gift-note · interview']" ] && [ "$(field '[(c["name"], c["why"]) for c in d["close"]]' <<<"$owed" 2>&1)" = "[('gift-note · interview', 'answered')]" ] \
  && [ "$(field 'd["open"]' <<<"$owed" 2>&1)" = "[]" ] && [ "$(field '[d["closed"], d["ran"]]' <<<"$closed" 2>&1)" = "[True, True]" ] \
  && ! grep -qF '"S-1"' "$TREE" && [ "$(tail -n 1 <<<"$twice")" = "exit 0" ] && grep -qF '"closed": false' <<<"$twice" \
  && [ "$(field '[[s["name"] for s in d["start"]], d["close"]]' <<<"$after" 2>&1)" = "[['gift-note · interview'], []]" ] \
  && grep -qF '"event": "companion.close", "task": "gift-note", "need": "interview", "session": "S-1", "why": "answered"' "$STATE/events.jsonl"; then
  pass "after his yes the held block still newest gives the lead's start from the record, the companion is due its close, close logs why and ends its session, and a second close finds nothing and exits 0"
else
  fail "the approval and the close: $owed / $closed / $twice / $after"
fi

# A choice of a lead: its companion, a card he closed with no answer, and his word that opens it again.
pr task-dir cart-total --ask "the cart total after a refund" >/dev/null && pr state cart-total building "lead: builder" >/dev/null
"$PY" -B "$DECISIONS" --repo "$R" ask cart-total "${CASE[@]}" --what "Where the note goes" --option "the last column" --option "after the price" --recommended "the last column" --why w --said s >/dev/null
due_choice=$(comp due | field '[o["name"] for o in d["open"]]' 2>&1 || true)
card=$(comp open cart-total --need choice --choice 1 2>&1 || true)
comp close cart-total --need choice --choice 1 --why dismissed >/dev/null
due_dismissed=$(comp due | field 'd["open"]' 2>&1 || true)
refused=$(comp open cart-total --need choice --choice 1 2>&1; echo "exit $?")
asked=$(comp open cart-total --need choice --choice 1 --asked 2>&1 || true)
if [ "$due_choice" = "['cart-total · choice 1']" ] && [ "$(field 'd["say"]' <<<"$card" 2>&1)" = "choice 1 of cart-total is open in \`cart-total · choice 1\` under this session" ] \
  && [ "$due_dismissed" = "[]" ] && [ "$(tail -n 1 <<<"$refused")" = "exit 1" ] && grep -qF "opens again on his word only" <<<"$refused" \
  && [ "$(field 'd["name"]' <<<"$asked" 2>&1)" = "cart-total · choice 1" ] && [ "$(field 'd["already"]' <<<"$asked" 2>&1)" = False ]; then
  pass "a choice that waits is due its companion; a card he closed with no answer is due nothing and open refuses it, and --asked, his word, opens it again"
else
  fail "a choice's companion: $due_choice / $card / $due_dismissed / $refused / $asked"
fi

# From a companion's own session the parent is the top of the group, as the board's: the new one sits beside it.
pr task-dir slip-note --ask "the slip names the note" >/dev/null && pr state slip-note held "the criteria wait for the owner: somebody else wrote the request" >/dev/null
beside=$(AS=S-2 comp open slip-note --need criteria 2>&1 || true)
if [ "$(field 'd["parent"]' <<<"$beside" 2>&1)" = "S-LEM" ] && [ "$(field 'd["say"]' <<<"$beside" 2>&1)" = "the criteria of slip-note are open in \`slip-note · criteria\` beside this session" ]; then
  pass "criteria that wait for his yes open a companion, and one opened from a companion's session is its sibling under Lem's session"
else
  fail "a companion from a companion: $beside"
fi

# The fast track opens nothing, and while he is away nothing opens; each companion that runs is due one message, once.
pr task-dir typo-fix --ask "fix the typo" >/dev/null && pr state typo-fix building "small change: one builder" >/dev/null
fast=$(comp open typo-fix --need interview 2>&1; echo "exit $?")
pr task-dir late-ask --ask "a late ask" >/dev/null && pr state late-ask held "the interview waits for the owner" >/dev/null
pr owner away --words "/lem im-away" >/dev/null
away_open=$(comp open late-ask --need interview 2>&1; echo "exit $?")
told_due=$(comp due | field '[sorted(a["name"] for a in d["away"]), d["open"], [c["name"] for c in d["close"]]]' 2>&1 || true)
comp told-away report-dates --need interview >/dev/null
after_told=$(comp due | field 'sorted(a["name"] for a in d["away"])' 2>&1 || true)
if [ "$(tail -n 1 <<<"$fast")" = "exit 1" ] && grep -qF "typo-fix is on the fast track" <<<"$fast" \
  && [ "$(tail -n 1 <<<"$away_open")" = "exit 1" ] && grep -qF "the owner is away" <<<"$away_open" \
  && [ "$told_due" = "[['report-dates · interview', 'slip-note · criteria'], [], ['cart-total · choice 1']]" ] && [ "$after_told" = "['slip-note · criteria']" ]; then
  pass "a task on the fast track opens no companion; while the owner is away nothing opens, the card his away took is due its close, and each companion that runs is due one message until told-away records it"
else
  fail "the fast track and away: $fast / $away_open / $told_due / $after_told"
fi

finish
