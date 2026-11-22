#!/usr/bin/env bash
# The board's acts (serve.py `board_act`, `board_start`): the owner's yes to the criteria, a merge from its confirm step,
# the park of a task a breaker holds, a fresh session of a task with none and a new task, posted as forms to a server of
# this run. The
# afternoon of tests/board-showcase.py gives the criteria, the breaker and the task with no session; a throwaway
# repository on the stand-in for GitHub gives a task that is open, which the merge lands with land.py, as `lem land
# merge SLUG --by owner` does. The tailnet door is a listener of serve.py's own handler in a process of this block,
# with a name and a login of its own: no check runs the tailscale command. And the server's duties across tasks
# (serve.py `duties`), called in a process of this block over a repository the server does not show, with the real
# `lem session` (session.py) behind them and the stand-in for agtermctl of tests/lib.sh (`agterm_standin`).
#
# For the acts of the server a stand-in takes the place of `lem session` (LEM_SESSION_SCRIPT). It is run as
# `python3 -B STANDIN --repo REPO VERB ...`, writes `VERB ARGS...` (no --repo) as one line to LEM_SESSION_CALLS, and prints:
# for `list`, the JSON list in the file LEM_SESSION_LIST (`[]` with none), each entry {"task", "session", "name",
# "live", "agent", "unanswered"}; for `open SLUG --why WHY`, {"task": SLUG, "session": "S-NEW", "name": SLUG,
# "phase": "build", "already": false, "say": "..."}; for `wake SLUG --why WHY`, {"task": SLUG, "session": "S-NEW",
# "woke": true}. It logs no event.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

DOOR_PID=""
# the run's exit stops the door of this block too, beside the server lib.sh stops
ended() {
  local pid
  stopped
  for pid in $SERVE_PID $DOOR_PID; do kill -TERM "$pid" 2>/dev/null; wait "$pid" 2>/dev/null || true; done
  rm -rf "$WORK"
}
trap ended EXIT

cat > "$WORK/session-standin.py" <<'PY'
import json, os, sys
args = sys.argv[1:]
if args[:1] == ["--repo"]:
    args = args[2:]
with open(os.environ["LEM_SESSION_CALLS"], "a") as calls:
    calls.write(" ".join(args) + "\n")
verb = args[0] if args else ""
if verb == "list":
    listed = os.environ.get("LEM_SESSION_LIST")
    print(open(listed).read() if listed and os.path.exists(listed) else "[]")
elif verb == "open":
    print(json.dumps({"task": args[1], "session": "S-NEW", "name": args[1], "phase": "build", "already": False, "say": f"{args[1]}: a session opened"}))
elif verb == "wake":
    print(json.dumps({"task": args[1], "session": "S-NEW", "woke": True}))
else:
    sys.exit(f"session stand-in: no such command: {verb}")
PY
export LEM_SESSION_SCRIPT=$WORK/session-standin.py LEM_SESSION_CALLS=$WORK/session-calls
DEMO=$("$PY" -B tests/board-showcase.py --demo "$WORK/demo" | field 'd["repo"]')
STATE=$DEMO/.lem/state
# The shop: one task proposed as a pull request on the stand-in for GitHub, so that its merge is the forge's.
SHOP=$WORK/fix-shop
ORIGIN=$SHOP.origin.git
git init -q -b main "$SHOP"
ident "$SHOP"
commit "$SHOP" init
on_github "$SHOP"
project --repo "$SHOP" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "owner"' 'history = "squash"' '[checks]' 'commands = ["true"]' > "$SHOP/.lem/project.toml"
echo one > "$SHOP/app.txt" && git -C "$SHOP" add -A && git -C "$SHOP" commit -q -m "chore: start" && git -C "$SHOP" push -q origin main
task_in "$SHOP" word-in-file ok.txt yes && read_in "$SHOP" word-in-file
land --repo "$SHOP" start word-in-file >/dev/null && land --repo "$SHOP" base word-in-file >/dev/null && polish_in "$SHOP" word-in-file
land --repo "$SHOP" checks word-in-file >/dev/null && land --repo "$SHOP" read word-in-file --record "$(clean word-in-file 1)" >/dev/null
land --repo "$SHOP" propose word-in-file --title "fix: the word is in the file" --notes "$NOTES" >/dev/null
TIP=$(kept_in "$SHOP" word-in-file proposed)
"$PY" -B "$SERVE" --add "$DEMO" >/dev/null && "$PY" -B "$SERVE" --add "$SHOP" >/dev/null
serve_up
SERVER=http://127.0.0.1:$SERVE_PORT
HOST=$(curl -fsS "$SERVER/api/server" | field 'd["host"]')
BASE=$SERVER/$HOST/shop
# post URL [ORIGIN] FIELD...: a form of the board's page, posted; prints the status and where it sends the page
post() {
  local url=$1 origin=$2 fields=()
  shift 2
  for field in "$@"; do fields+=(--data-urlencode "$field"); done
  curl -s -o /dev/null -w '%{http_code} %{redirect_url}' -H "Origin: $origin" -H 'Sec-Fetch-Site: same-origin' "${fields[@]}" "$url"
}
words() { "$PY" -c 'import html, re, sys; t = sys.stdin.read(); t = re.sub(r"(?s)<(script|style|template|svg)\b.*?</\1>", " ", t); print(" ".join(html.unescape(re.sub(r"<[^>]+>", " ", t)).split()))'; }
events() { grep -c "\"event\": \"$2\", \"task\": \"$3\"" "$1/.lem/state/events.jsonl" || true; }
digest=$("$PY" -c 'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest()[:16])' "$STATE/tasks/stock-on-product-page/criteria.md")

waits=$(curl -fsS "$BASE/waits")
criteria_tab=$(curl -fsS "$BASE/tasks/stock-on-product-page/criteria")
if grep -qF "Read and approve" <<<"$waits" && ! grep -qF "stock-on-product-page/approve" <<<"$waits" \
  && grep -qF "action=\"/$HOST/shop/tasks/stock-on-product-page/approve\"" <<<"$criteria_tab" && grep -qF "name=\"digest\" value=\"$digest\"" <<<"$criteria_tab" \
  && grep -qF "href=\"/$HOST/shop/tasks/refund-line-on-receipt/merge?in=waits\"" <<<"$waits" \
  && grep -qF "href=\"/$HOST/shop/tasks/gift-note-in-export/park?in=waits\"" <<<"$waits" && ! grep -qF "fee-notice-to-merchants/park" <<<"$waits"; then
  pass "on this Mac a row of Waits for you has the owner's act: the way to the criteria, with his yes under their text on the task's tab, the way to a merge's confirm step, and the way to park a task a breaker holds"
else
  fail "the acts of Waits for you: $(grep -o 'wr-acts.\{0,400\}' <<<"$waits" | head -c 1500)"
fi

# A page's own forms carry its origin with no script too: the board sends Referrer-Policy same-origin, under which the
# browser's POST names the board's origin (no-referrer would make it `null`, which the guard refuses as it did).
policy=$(curl -fsS -D - -o /dev/null "$BASE/tasks/stock-on-product-page/criteria" | tr -d '\r' | grep -i '^referrer-policy:' || true)
nulled=$(post "$BASE/tasks/stock-on-product-page/approve" null "digest=$digest")
if [ "$policy" = "Referrer-Policy: same-origin" ] && [ "${nulled%% *}" = 403 ] && [ ! -e "$STATE/tasks/stock-on-product-page/criteria.json" ]; then
  pass "a page of the board carries Referrer-Policy same-origin, and a form posted with the Origin null is still refused"
else
  fail "the referrer policy and a null origin: $policy / $nulled"
fi

# A form of another site, and one that carries criteria other than the file's, approve nothing.
elsewhere=$(post "$BASE/tasks/stock-on-product-page/approve" https://evil.example "digest=$digest")
stale=$(post "$BASE/tasks/stock-on-product-page/approve" "$SERVER" "digest=0000" "in=waits")
stale_note=$(curl -fsS "${stale#* }" | words)
if [ "${elsewhere%% *}" = 403 ] && [ "${stale%% *}" = 303 ] && grep -qF "/stock-on-product-page?in=waits&note=" <<<"$stale" \
  && grep -qF "Not done. The criteria changed since the page showed them" <<<"$stale_note" \
  && [ ! -e "$STATE/tasks/stock-on-product-page/criteria.json" ] && [ "$(events "$DEMO" board.act stock-on-product-page)" = 0 ]; then
  pass "a form from another origin is refused, and one whose criteria are not the file's approves nothing and says why on the task's page"
else
  fail "the refusals of an approval: $elsewhere / $stale / ${stale_note:0:600}"
fi

# The tailnet door: serve.py's handler with a door of a name and a login of this block's, on a port of its own.
DOOR_PORT=$("$PY" -I -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')
"$PY" -B -c '
import sys
sys.path.insert(0, "skills/lem/scripts")
import serve, lem_peers
serve.Handler.machine = serve.Machine()
serve.Handler.peers = lem_peers.Peers(lambda: {})
door = serve.Door("/nonexistent/tailscale", "mac.tail0000.ts.net", int(sys.argv[1]), "owner@example.com")
server = serve.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), type("DoorHandler", (serve.Handler,), {"door": door}))
print(serve.HOSTNAME, flush=True)
server.serve_forever()
' "$DOOR_PORT" > "$WORK/door.out" 2>&1 &
DOOR_PID=$!
soon grep -q . "$WORK/door.out"
DOOR_HOST=$(head -1 "$WORK/door.out")
through() {
  local login=$1
  shift
  curl -s -o /dev/null -w '%{http_code} %{redirect_url}' -H "Host: mac.tail0000.ts.net:$DOOR_PORT" -H "Tailscale-User-Login: $login" \
    -H "Origin: https://mac.tail0000.ts.net:$DOOR_PORT" -H 'Sec-Fetch-Site: same-origin' --data-urlencode "digest=$digest" \
    "http://127.0.0.1:$DOOR_PORT/$DOOR_HOST/shop/tasks/stock-on-product-page/approve"
}
other=$(through someone@example.com)
mine=$(through owner@example.com)
kill -TERM "$DOOR_PID" 2>/dev/null; wait "$DOOR_PID" 2>/dev/null || true
DOOR_PID=""
approved=$("$PY" -c 'import json, sys; d = json.load(open(sys.argv[1])); print((d["by"], d["number"]))' "$STATE/tasks/stock-on-product-page/criteria.json" 2>/dev/null || true)
asked=$(grep '"event": "board.act", "task": "stock-on-product-page"' "$STATE/events.jsonl" | field '(d["act"], d["via"])' || true)
if [ "${other%% *}" = 403 ] && [ "${mine%% *}" = 303 ] && [ "$approved" = "('owner', 1)" ] && [ "$asked" = "('approve', 'the board, through the tailnet door')" ] \
  && grep -qxF "wake stock-on-product-page --why owner" "$LEM_SESSION_CALLS" \
  && ! grep -rqF "owner@example.com" "$STATE/events.jsonl" "$STATE/tasks/stock-on-product-page" \
  && ! curl -fsS "$BASE/waits" | grep -qF "stock-on-product-page/approve"; then
  pass "through the door another login is refused, and the owner's yes is the owner's approval of the criteria, with where he asked and never his login, and the word to the task's session"
else
  fail "the approval through the door: $other / $mine / $approved / $asked"
fi

parked=$(post "$BASE/tasks/gift-note-in-export/park" "$SERVER" "why=  wait for the export's new reader  ")
parked_page=$(curl -fsS "${parked#* }" | words)
state=$(project --repo "$DEMO" tasks | field 'next((t["status"], t["state"].splitlines()[0]) for t in d if t["slug"] == "gift-note-in-export")')
if [ "${parked%% *}" = 303 ] && [[ "$state" == "('parked', "*"wait for the export's new reader\")" ]] \
  && grep -qF "Done. The task is parked. Its session got word of it, and closes once you have left it. /lem resume gift-note-in-export in any session brings it back." <<<"$parked_page" \
  && grep -qxF "wake gift-note-in-export --why owner" "$LEM_SESSION_CALLS" \
  && [ "$(grep '"event": "board.act", "task": "gift-note-in-export"' "$STATE/events.jsonl" | field '(d["act"], d["via"])')" = "('park', 'the board, on this Mac')" ]; then
  pass "a park from the board writes the state parked with the owner's line of why, tells the task's session, and its page says what happens next"
else
  fail "the park: $parked / $state / ${parked_page:0:600}"
fi

# The merge: nothing without the confirm step; the confirm step says green first, then the commit; the merge then
# lands the branch as one commit with the proposal's title, in the background, and its page says so.
M=$SERVER/$HOST/fix-shop/tasks/word-in-file
bare=$(post "$M/merge" "$SERVER" "tip=$TIP")
bare_page=$(curl -fsS "${bare#* }" | words)
confirm=$(curl -fsS "$M/merge" | words)
# a form that carries another commit than the one proposed, as a confirm step read before a new proposal does
stale=$(post "$M/merge" "$SERVER" "confirm=yes" "tip=0000000000000000000000000000000000000000")
stale_page=$(curl -fsS "${stale#* }" | words)
if [ "${stale%% *}" = 303 ] && grep -qF "Not done. The branch was proposed again since the confirm step showed it: nothing was merged. Read the confirm step again." <<<"$stale_page" \
  && [ "$(status_in "$SHOP" word-in-file)" = open ] && [ "$(events "$SHOP" merge.start word-in-file)" = 0 ] && [ "$(git -C "$ORIGIN" log -1 --format=%s main)" = "chore: start" ]; then
  pass "a merge whose form carries another commit than the one proposed now merges nothing, and its page says to read the confirm step again"
else
  fail "the merge of a commit the confirm step did not show: $stale / $(status_in "$SHOP" word-in-file) / $(grep -o "Not done[^<]*" <<<"$stale_page" | head -c 300)"
fi
merged=$(post "$M/merge" "$SERVER" "confirm=yes" "tip=$TIP")
soon test "$(status_in "$SHOP" word-in-file)" = landed
soon grep -q '"event": "board.act", "task": "word-in-file"' "$SHOP/.lem/state/events.jsonl"
merged_page=$(curl -fsS "${merged#* }" | words)
if grep -qF "Not done. A merge runs only from its confirm step" <<<"$bare_page" && grep -qF "Merge #1 · confirm Green" <<<"$confirm" && grep -qF "${TIP:0:12}" <<<"$confirm" \
  && grep -qF "Lands as one commit: fix: the word is in the file" <<<"$confirm" && [ "${merged%% *}" = 303 ] && [ "$(status_in "$SHOP" word-in-file)" = landed ] \
  && [ "$(git -C "$ORIGIN" log -1 --format=%s main)" = "fix: the word is in the file" ] && grep -qF "Done. Merged: pull request #1 is on main" <<<"$merged_page" \
  && [ "$(grep '"event": "board.act", "task": "word-in-file"' "$SHOP/.lem/state/events.jsonl" | field '(d["act"], d["via"])')" = "('merge', 'the board, on this Mac')" ]; then
  pass "a merge runs only from its confirm step, which says green first and names the commit; then land.py lands the branch on the owner's word, and the task's page says what came of it"
else
  fail "the merge: $bare / $(grep -o "Not done[^<]*" <<<"$bare_page" | head -c 200) / $(grep -o "Merge #1 · confirm.\{0,300\}" <<<"$confirm") / $merged / $(status_in "$SHOP" word-in-file) / $(git -C "$ORIGIN" log -1 --format=%s main) / $(grep -o "Done\..\{0,200\}" <<<"$merged_page")"
fi

# "Open a session" for the task with no session: one `lem session open` with the reason of a task that never had
# one, and its page says what happens next; a task whose session lives gets no such act.
: > "$LEM_SESSION_CALLS"
opened=$(post "$BASE/tasks/cart-total-after-coupon/session" "$SERVER" "in=waits")
opened_page=$(curl -fsS "${opened#* }" | words)
refused=$(post "$BASE/tasks/stock-on-product-page/session" "$SERVER" "in=waits")
refused_page=$(curl -fsS "${refused#* }" | words)
if [ "${opened%% *}" = 303 ] && [ "$(grep -c '^open ' "$LEM_SESSION_CALLS")" = 1 ] && grep -qxF "open cart-total-after-coupon --why owner" "$LEM_SESSION_CALLS" \
  && grep -qF "Done. A session of the task opened in agterm" <<<"$opened_page" && grep -qF "Its agent reads the task’s state and goes on from there" <<<"$opened_page" \
  && grep -qF "Not done. No session of stock-on-product-page was opened: its session runs" <<<"$refused_page" \
  && [ "$(grep '"event": "board.act", "task": "cart-total-after-coupon"' "$STATE/events.jsonl" | field 'd["act"]')" = session ]; then
  pass "Open a session runs lem session open once for a task with none, its page says what comes next, and a task whose session lives is refused"
else
  fail "the act of a session: $opened / $(cat "$LEM_SESSION_CALLS") / ${opened_page:0:400} / ${refused_page:0:400}"
fi

# A new task from the board: the owner's words on the form of "+" name it by their first five plain words, and a backlog
# item by its file's stem; each gets its directory with its ask and its session with no focus. A slug of a task that
# runs is refused by the server, and one of a task that ended by task-dir, as it says.
: > "$LEM_SESSION_CALLS"
new_form=$(curl -fsS "$BASE/new" | words)
started=$(post "$SERVER/$HOST/shop/start" "$SERVER" "words=  Add the gift note to the CSV export, please  ")
started_page=$(curl -fsS "${started#* }" | words)
item=$(post "$SERVER/$HOST/shop/start" "$SERVER" "item=export-in-one-query")
running=$(post "$SERVER/$HOST/shop/start" "$SERVER" "words=Stock on product page")
running_page=$(curl -fsS "${running#* }" | words)
ended_slug=$(post "$SERVER/$HOST/shop/start" "$SERVER" "words=order date on invoice")
ended_page=$(curl -fsS "${ended_slug#* }" | words)
# a task whose directory and words are there and whose session has not opened yet: the board sees no task, and
# task-dir keeps the words that came first
project --repo "$DEMO" task-dir refund-email-to-the-customer --ask "Refund email to the customer, in Polish" >/dev/null
other_words=$(post "$SERVER/$HOST/shop/start" "$SERVER" "words=Refund email to the customer, in English")
other_page=$(curl -fsS "${other_words#* }" | words)
if grep -qF "What should Lem do?" <<<"$new_form" && [[ "$started" == "303 $SERVER/$HOST/shop/tasks/add-the-gift-note-to?note="* ]] \
  && [ "$(cat "$STATE/tasks/add-the-gift-note-to/ask.txt")" = "Add the gift note to the CSV export, please" ] \
  && grep -qF "Done. Lem opened the session add-the-gift-note-to in agterm" <<<"$started_page" \
  && [[ "$item" == "303 $SERVER/$HOST/shop/tasks/export-in-one-query?note="* ]] && [ "$(cat "$STATE/tasks/export-in-one-query/ask.txt")" = docs/backlog/export-in-one-query.md ] \
  && [ "$(grep -c '^open ' "$LEM_SESSION_CALLS")" = 2 ] && grep -qxF "open add-the-gift-note-to --why new" "$LEM_SESSION_CALLS" && grep -qxF "open export-in-one-query --why new" "$LEM_SESSION_CALLS" \
  && grep -qF "Not done. stock-on-product-page is a task already" <<<"$running_page" \
  && [[ "$ended_slug" == "303 $SERVER/$HOST/shop/new?note="* ]] && grep -qF "Not done. project.py: the task 'order-date-on-invoice' is landed; a new task takes a slug of its own" <<<"$ended_page" \
  && [ "$(grep '"event": "board.act", "task": "add-the-gift-note-to"' "$STATE/events.jsonl" | field 'd["act"]')" = start ] \
  && grep -qF "Not done. project.py: the task 'refund-email-to-the-customer' holds other words already" <<<"$other_page" && grep -qF "choose another name" <<<"$other_page" \
  && [ "$(cat "$STATE/tasks/refund-email-to-the-customer/ask.txt")" = "Refund email to the customer, in Polish" ] && ! grep -qF refund-email "$LEM_SESSION_CALLS"; then
  pass "a new task starts from the board: the owner's words name it by their first five plain words and a backlog item by its stem, each gets its ask and its session with no focus, and a slug that runs or ended, or whose words differ, is refused with why"
else
  fail "a new task from the board: $started / ${started_page:0:300} / $item / $(cat "$LEM_SESSION_CALLS") / ${running_page:0:300} / $ended_slug / ${ended_page:0:300} / ${other_page:0:300}"
fi

# The server's duties, over a repository the server does not show, so that only this process acts on it: a pull
# request merged on GitHub runs `lem land merged` and then the wake of its task's session; one GitHub calls
# conflicting is woken once; a task queued after the merged one gets its session opened. `task-dir` and `lem
# session open` put a repository into the list of workspaces of Lem's home folder, so the rest of this block has a
# home folder of its own, whose list the server of this block does not read.
export XDG_CONFIG_HOME=$WORK/aside
mkdir -p "$XDG_CONFIG_HOME/lem" && printf '[load]\nstart = 0\n' > "$XDG_CONFIG_HOME/lem/machine.toml"
DUTY=$WORK/duty-shop
git init -q -b main "$DUTY" && ident "$DUTY" && commit "$DUTY" init && on_github "$DUTY"
project --repo "$DUTY" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "owner"' 'history = "squash"' '[checks]' 'commands = ["true"]' > "$DUTY/.lem/project.toml"
git -C "$DUTY" add -A && git -C "$DUTY" commit -q -m "chore: start" && git -C "$DUTY" push -q origin main
for slug in first-word second-word; do
  task_in "$DUTY" "$slug" "$slug.txt" yes && read_in "$DUTY" "$slug"
  land --repo "$DUTY" start "$slug" >/dev/null && land --repo "$DUTY" base "$slug" >/dev/null && polish_in "$DUTY" "$slug"
  land --repo "$DUTY" checks "$slug" >/dev/null && land --repo "$DUTY" read "$slug" --record "$(clean "$slug" 1)" >/dev/null
  land --repo "$DUTY" propose "$slug" --title "fix: $slug" --notes "$NOTES" >/dev/null
done
project --repo "$DUTY" task-dir third-word --ask "Put the third word into a file." >/dev/null
project --repo "$DUTY" state third-word queued "it starts after first-word" "after: first-word" >/dev/null
# agterm, as the stand-in keeps it: the session the owner typed in, in the workspace W-1, from which first-word's own opened
AGT=$WORK/agt
agterm_standin "$AGT/bin"
printf '%s\n' '[{"id": "S-HIS", "name": "notes", "workspace": "W-1", "foreground": ["claude"]}]' > "$AGT/tree.json"
agt() { env -u AGTERM_SOCKET -u AGTERM_WINDOW_ID CALLS="$AGT/calls" TREE="$AGT/tree.json" PATH="$AGT/bin:$PATH" "$@"; }
agt AGTERM_SESSION_ID=S-HIS "$PY" -B skills/lem/scripts/session.py --repo "$DUTY" open first-word --why new >/dev/null
# GitHub merges the first pull request, and calls the second one conflicting
(cd "$DUTY" && gh pr merge 1 --squash --match-head-commit "$(git -C "$DUTY.origin.git" rev-parse refs/heads/fix/first-word)" --subject "fix: first-word" >/dev/null)
"$PY" -c 'import json, sys; f = sys.argv[1]; d = json.load(open(f)); d["prs"]["2"]["mergeable"] = "CONFLICTING"; json.dump(d, open(f, "w"))' "$DUTY.origin.git.gh.json"
looked=$(agt AGTERM_SESSION_ID=S-HIS AGTERM_WINDOW_ID=W-HIS LEM_SESSION_SCRIPT= "$PY" -B -c '
import json, sys
sys.path.insert(0, "skills/lem/scripts")
import serve
serve.detach_from_session()
w = serve.Workspace("duty-shop", sys.argv[1])
forge = serve.forge_once(w)
w.look_sessions()
first = serve.run_duties(w)
second = serve.run_duties(w)
print(json.dumps({"forge": [(x["task"], x["exit"]) for x in forge], "first": [(x["verb"], x["task"], x["why"], x["exit"]) for x in first], "second": len(second)}))
' "$DUTY")
sessions=$("$PY" -c 'import json, sys; print([(r["event"], r["task"], r.get("session"), r.get("why"), r.get("workspace"), r.get("head") is not None) for r in map(json.loads, open(sys.argv[1])) if r["event"] in ("session.open", "session.wake")])' "$DUTY/.lem/state/events.jsonl")
if [ "$(status_in "$DUTY" first-word)" = landed ] && [ "$(field 'd["forge"]' <<<"$looked")" = "[['first-word', 0]]" ] \
  && [ "$(field 'sorted(map(tuple, d["first"]))' <<<"$looked")" = "[('open', 'third-word', 'queue', 0), ('wake', 'first-word', 'merged', 0), ('wake', 'second-word', 'conflict', 0)]" ] \
  && [ "$(field 'd["second"]' <<<"$looked")" = 0 ] && grep -qF '["msg", "send", "lem: first-word merged", "--to", "S-1:left"]' "$AGT/calls" \
  && [ "$sessions" = "[('session.open', 'first-word', 'S-1', 'new', 'W-1', False), ('session.wake', 'first-word', 'S-1', 'merged', None, False), ('session.open', 'second-word', 'S-2', 'conflict', 'W-1', False), ('session.wake', 'second-word', 'S-2', 'conflict', None, True), ('session.open', 'third-word', 'S-3', 'queue', 'W-1', False)]" ] \
  && ! grep -qF -- '--window' "$AGT/calls"; then
  pass "after GitHub merged a pull request the server runs lem land merged, then lem session wakes the task's session with a pane message; it opens a session for a conflicting one with its head on record and one for the task queued after the merged one, in the workspace the log names"
else
  fail "the server's duties: $looked / $(status_in "$DUTY" first-word) / $sessions / $(cat "$AGT/calls")"
fi

# A pull request closed on GitHub with no merge while no session runs for its task: the server runs `lem land
# merged`, which drops the task, and its wake opens the task's session in the land phase with no focus, so that
# the session pays what the task's ticket is owed and removes the worktree (stages/land.md, prompts/session.md).
CLOSE=$WORK/close-shop
git init -q -b main "$CLOSE" && ident "$CLOSE" && commit "$CLOSE" init && on_github "$CLOSE"
project --repo "$CLOSE" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "owner"' 'history = "squash"' '[checks]' 'commands = ["true"]' > "$CLOSE/.lem/project.toml"
git -C "$CLOSE" add -A && git -C "$CLOSE" commit -q -m "chore: start" && git -C "$CLOSE" push -q origin main
task_in "$CLOSE" word-not-wanted word.txt yes && read_in "$CLOSE" word-not-wanted
land --repo "$CLOSE" start word-not-wanted >/dev/null && land --repo "$CLOSE" base word-not-wanted >/dev/null && polish_in "$CLOSE" word-not-wanted
land --repo "$CLOSE" checks word-not-wanted >/dev/null && land --repo "$CLOSE" read word-not-wanted --record "$(clean word-not-wanted 1)" >/dev/null
land --repo "$CLOSE" propose word-not-wanted --title "fix: word-not-wanted" --notes "$NOTES" >/dev/null
printf '%s\n' '[{"id": "S-HIS", "name": "notes", "workspace": "W-1", "foreground": ["claude"]}]' > "$AGT/tree.json"
agt AGTERM_SESSION_ID=S-HIS "$PY" -B skills/lem/scripts/session.py --repo "$CLOSE" open word-not-wanted --why new >/dev/null
# its session is gone (agterm's tree holds the owner's session alone), and GitHub closes the pull request with no merge
printf '%s\n' '[{"id": "S-HIS", "name": "notes", "workspace": "W-1", "foreground": ["claude"]}]' > "$AGT/tree.json"
: > "$AGT/calls"
"$PY" -c 'import json, sys; f = sys.argv[1]; d = json.load(open(f)); d["prs"]["1"]["state"] = "CLOSED"; json.dump(d, open(f, "w"))' "$CLOSE.origin.git.gh.json"
closed=$(agt LEM_SESSION_SCRIPT= "$PY" -B -c '
import json, sys
sys.path.insert(0, "skills/lem/scripts")
import serve
serve.detach_from_session()
w = serve.Workspace("close-shop", sys.argv[1])
forge = serve.forge_once(w)
w.look_sessions()
first = serve.run_duties(w)
w.look_sessions()
second = serve.run_duties(w)
print(json.dumps({"forge": [(x["task"], x["exit"]) for x in forge], "first": [(x["verb"], x["task"], x["why"], x["exit"]) for x in first], "second": len(second)}))
' "$CLOSE")
opens=$("$PY" -c 'import json, sys; print([(r["why"], r["phase"]) for r in map(json.loads, open(sys.argv[1])) if r["event"] == "session.open"])' "$CLOSE/.lem/state/events.jsonl")
line=$(project --repo "$CLOSE" tasks | field 'next(t["state"].splitlines()[0] for t in d if t["slug"] == "word-not-wanted")')
if [ "$(status_in "$CLOSE" word-not-wanted)" = dropped ] && [[ "$line" == *"dropped: the pull request was closed on the forge" ]] \
  && [ "$(field 'd["forge"]' <<<"$closed")" = "[['word-not-wanted', 0]]" ] && [ "$(field 'd["first"]' <<<"$closed")" = "[['wake', 'word-not-wanted', 'merged', 0]]" ] \
  && [ "$(field 'd["second"]' <<<"$closed")" = 0 ] && [ "$opens" = "[('new', 'land'), ('merged', 'land')]" ] \
  && grep -qF '"--no-select"' "$AGT/calls" && ! grep -qF '["session", "select"' "$AGT/calls" && [ -d "$WORK/close-shop/.lem/worktrees/word-not-wanted" ]; then
  pass "after GitHub closed a pull request with no merge while no session ran for its task, the server drops the task and its wake opens the task's session in the land phase with no focus, once, its worktree still there for that session to clean"
else
  fail "the wake of a pull request closed on GitHub: $closed / $(status_in "$CLOSE" word-not-wanted) / $line / $opens / $(cat "$AGT/calls")"
fi

# The merge agent's merge is the server's duty: after its review says `merge` and calls nobody, the server runs
# `lem land merge SLUG --by merger --via server` in a thread with no act of anyone, the pull request lands, and the
# next look wakes the task's session for its cleanup through the stand-in for agtermctl.
AUTO=$WORK/auto-shop
git init -q -b main "$AUTO" && ident "$AUTO" && commit "$AUTO" init && on_github "$AUTO"
project --repo "$AUTO" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' 'history = "squash"' '[checks]' 'commands = ["true"]' > "$AUTO/.lem/project.toml"
git -C "$AUTO" add -A && git -C "$AUTO" commit -q -m "chore: start" && git -C "$AUTO" push -q origin main
task_in "$AUTO" word-by-agent word.txt yes && read_in "$AUTO" word-by-agent
land --repo "$AUTO" start word-by-agent >/dev/null && land --repo "$AUTO" base word-by-agent >/dev/null && polish_in "$AUTO" word-by-agent
land --repo "$AUTO" checks word-by-agent >/dev/null && land --repo "$AUTO" read word-by-agent --record "$(clean word-by-agent 1)" >/dev/null
land --repo "$AUTO" propose word-by-agent --title "fix: the word by the agent" --notes "$NOTES" >/dev/null
reviewed=$(merge_read "$AUTO" word-by-agent | field '(d["calls"], d["next"].startswith("the board'"'"'s server merges it"))')
: > "$AGT/calls"
agt AGTERM_SESSION_ID=S-HIS "$PY" -B skills/lem/scripts/session.py --repo "$AUTO" open word-by-agent --why new >/dev/null
auto=$(agt LEM_SESSION_SCRIPT= "$PY" -B -c '
import json, sys, threading
sys.path.insert(0, "skills/lem/scripts")
import serve
serve.detach_from_session()
w = serve.Workspace("auto-shop", sys.argv[1])
w.look_sessions()
first = serve.run_duties(w)
for thread in threading.enumerate():
    if thread.name.startswith("merge "):
        thread.join(120)
w.look_sessions()
second = serve.run_duties(w)
print(json.dumps({"first": [(x["verb"], x["task"], x["why"]) for x in first], "second": [(x["verb"], x["task"], x["why"], x["exit"]) for x in second]}))
' "$AUTO")
started=$(grep '"event": "merge.start", "task": "word-by-agent"' "$AUTO/.lem/state/events.jsonl" | field '(d["by"], d["via"])')
if [ "$reviewed" = "(False, True)" ] && [ "$(field 'd["first"]' <<<"$auto")" = "[['merge', 'word-by-agent', 'merger']]" ] \
  && [ "$(status_in "$AUTO" word-by-agent)" = landed ] && [ "$(git -C "$AUTO.origin.git" log -1 --format=%s main)" = "fix: the word by the agent" ] \
  && [ "$started" = "('merger', 'server')" ] && [ "$(kept_in "$AUTO" word-by-agent merged_by)" = "{'by': 'merger', 'via': 'server'}" ] \
  && [ "$(field 'd["second"]' <<<"$auto")" = "[['wake', 'word-by-agent', 'merged', 0]]" ] && grep -qF '["msg", "send", "lem: word-by-agent merged", "--to", "S-' "$AGT/calls"; then
  pass "after the merge agent's verdict merge the server's duty merges the pull request with no act of anyone, the record says the server ran the merge agent's merge, and the next look wakes the task's session"
else
  fail "the merge agent's merge by the server: $reviewed / $auto / $(status_in "$AUTO" word-by-agent) / $started / $(kept_in "$AUTO" word-by-agent merged_by) / $(cat "$AGT/calls")"
fi

# Two proposed tasks, each with the merge agent's verdict merge. The first merges; the server's merge of the
# second meets the base the first moved, and Lem keeps that refusal and wakes the second's session. The
# session lands it again (here the test runs its steps): the rebase with no conflict carries the review and the
# merge review onto the new tip, and the server merges it with no second read by the merge agent.
MOVE=$WORK/move-shop
git init -q -b main "$MOVE" && ident "$MOVE" && commit "$MOVE" init && on_github "$MOVE"
project --repo "$MOVE" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' 'history = "squash"' '[checks]' 'commands = ["true"]' > "$MOVE/.lem/project.toml"
git -C "$MOVE" add -A && git -C "$MOVE" commit -q -m "chore: start" && git -C "$MOVE" push -q origin main
for slug in first-move second-move; do
  task_in "$MOVE" "$slug" "$slug.txt" yes && read_in "$MOVE" "$slug"
  land --repo "$MOVE" start "$slug" >/dev/null && land --repo "$MOVE" base "$slug" >/dev/null && polish_in "$MOVE" "$slug"
  land --repo "$MOVE" checks "$slug" >/dev/null && land --repo "$MOVE" read "$slug" --record "$(clean "$slug" 1)" >/dev/null
  land --repo "$MOVE" propose "$slug" --title "fix: $slug" --notes "$NOTES" >/dev/null && merge_read "$MOVE" "$slug" >/dev/null
done
land --repo "$MOVE" merge first-move --by merger --via server --message "fix: first-move" >/dev/null
BEFORE=$(kept_in "$MOVE" second-move proposed)
duty() {
  "$PY" -B -c '
import json, sys, threading
sys.path.insert(0, "skills/lem/scripts")
import serve
w = serve.Workspace("move-shop", sys.argv[1])
ran = serve.run_duties(w)
for thread in threading.enumerate():
    if thread.name.startswith("merge "):
        thread.join(120)
print(json.dumps({"ran": [(x["verb"], x["task"], x["why"]) for x in ran], "owed": serve.duties(w.model(), {}, set())}))
' "${1:-$MOVE}"
}
refused=$(duty)
kind=$(kept_in "$MOVE" second-move merge_refused | "$PY" -c 'import ast, sys; d = ast.literal_eval(sys.stdin.read()); print((d["by"], d["from"], d["kind"]))')
land --repo "$MOVE" start second-move >/dev/null && land --repo "$MOVE" base second-move >/dev/null && land --repo "$MOVE" checks second-move >/dev/null
due_now=$(land --repo "$MOVE" read second-move | field 'd["due"]')
again=$(land --repo "$MOVE" propose second-move --title "fix: second-move" --notes "$NOTES")
AFTER=$(kept_in "$MOVE" second-move proposed)
merged=$(duty)
reviews=$("$PY" -c 'import json, sys; print([("carried" in r) for r in map(json.loads, open(sys.argv[1])) if r["event"] == "merge.review" and r["task"] == "second-move"])' "$MOVE/.lem/state/events.jsonl")
if [ "$(field 'd["ran"]' <<<"$refused")" = "[['merge', 'second-move', 'merger']]" ] && [ "$(field 'd["owed"]' <<<"$refused")" = "[['wake', 'second-move', 'refused']]" ] \
  && [ "$kind" = "('merger', 'lem', 'base')" ] && [ "$due_now" = none ] && [ "$BEFORE" != "$AFTER" ] \
  && [ "$(field '(d["merge_review"], d["green"])' <<<"$again")" = "('carried', True)" ] && [ "$(kept_in "$MOVE" second-move relands)" = 1 ] \
  && [ "$(field 'd["ran"]' <<<"$merged")" = "[['merge', 'second-move', 'merger']]" ] && [ "$(status_in "$MOVE" second-move)" = landed ] \
  && [ "$reviews" = "[False, True]" ] \
  && [ "$(git -C "$MOVE.origin.git" log -2 --format=%s main)" = "$(printf '%s\n' 'fix: second-move' 'fix: first-move')" ]; then
  pass "a merge that meets the base another merge moved is kept for its tip and wakes the task's session; landed again with no conflict, the review and the merge review carry onto the new tip, and the server merges it with no second read"
else
  fail "the merge after a moved base: $refused / $kind / $due_now / $again / $merged / $reviews / $(status_in "$MOVE" second-move) / $(git -C "$MOVE.origin.git" log -3 --format=%s main)"
fi

# A change whose review left a must-fix open: two rounds leave 1 must-fix, so the request is not green for it and the
# merge agent calls the owner, who merges it. The base moves and his merge is refused for it; the merge agent's read
# says another round, and the new landing's rebase meets no conflict. The review carries as it was, its must-fix too:
# the request is not green for the same must-fix, the merge review carries, his merge stands, and the server merges it.
OPEN=$WORK/open-must-fix-shop
git init -q -b main "$OPEN" && ident "$OPEN" && commit "$OPEN" init && on_github "$OPEN"
project --repo "$OPEN" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' 'history = "squash"' '[checks]' 'commands = ["true"]' > "$OPEN/.lem/project.toml"
git -C "$OPEN" add -A && git -C "$OPEN" commit -q -m "chore: start" && git -C "$OPEN" push -q origin main
task_in "$OPEN" open-must-fix open.txt yes && read_in "$OPEN" open-must-fix
land --repo "$OPEN" start open-must-fix >/dev/null && land --repo "$OPEN" base open-must-fix >/dev/null && polish_in "$OPEN" open-must-fix
land --repo "$OPEN" checks open-must-fix >/dev/null
land --repo "$OPEN" read open-must-fix --record "$(record open-must-fix 1 '{"kind": "read", "answered": ["codex"], "must_fix": 1}')" >/dev/null
land --repo "$OPEN" read open-must-fix --record "$(record open-must-fix 2 '{"kind": "round", "ran": [{"name": "default", "why": "it fits"}], "answered": ["codex"], "must_fix": 1}')" >/dev/null
first=$(land --repo "$OPEN" propose open-must-fix --title "fix: open-must-fix" --notes "$NOTES")
called=$(merge_read "$OPEN" open-must-fix | field 'd["calls"]')
OPEN_MOVER=$WORK/open-must-fix-mover
git clone -q "$OPEN.origin.git" "$OPEN_MOVER" && ident "$OPEN_MOVER"
echo moved > "$OPEN_MOVER/moved.txt" && git -C "$OPEN_MOVER" add moved.txt && git -C "$OPEN_MOVER" commit -q -m "docs: moved" && git -C "$OPEN_MOVER" push -q origin main
pressed=$(land --repo "$OPEN" merge open-must-fix --by owner --message "fix: open-must-fix" 2>&1 || true)
round=$(merge_read "$OPEN" open-must-fix merge "another round" | field 'd["base_call"]')
land --repo "$OPEN" start open-must-fix >/dev/null && land --repo "$OPEN" base open-must-fix >/dev/null && land --repo "$OPEN" checks open-must-fix >/dev/null
due_open=$(land --repo "$OPEN" read open-must-fix | field '(d["due"], d["why"])')
reproposed=$(land --repo "$OPEN" propose open-must-fix --title "fix: open-must-fix" --notes "$NOTES")
logged=$("$PY" -c 'import json, sys; print([(r["green"], r.get("review")) for r in map(json.loads, open(sys.argv[1])) if r["event"] == "proposed" and r["task"] == "open-must-fix"])' "$OPEN/.lem/state/events.jsonl")
open_merged=$(duty "$OPEN")
open_reviews=$("$PY" -c 'import json, sys; print([("carried" in r) for r in map(json.loads, open(sys.argv[1])) if r["event"] == "merge.review" and r["task"] == "open-must-fix"])' "$OPEN/.lem/state/events.jsonl")
must_fix_why="two rounds reviewed it: the last one left 1 must-fix"
carried_line="rebased on main; the review carried over the rebase, and its open must-fix; the checks passed again"
if [ "$(field '(d["green"], d["not_green"])' <<<"$first")" = "(False, ['$must_fix_why'])" ] && [ "$called" = True ] \
  && grep -qF "the owner's merge stands, and goes through after a read that says \`Base: safe.\`" <<<"$pressed" && [ "$round" = "another round" ] \
  && [ "$due_open" = "('owner', '$must_fix_why')" ] \
  && [ "$(field '(d["green"], d["not_green"], d["merge_review"], d["owner_merge"].startswith("stands"), d["synced"])' <<<"$reproposed")" \
    = "(False, ['$must_fix_why'], 'carried', True, '$carried_line')" ] \
  && [ "$(kept_in "$OPEN" open-must-fix rebase_uncovered)" = None ] \
  && grep -qxF "Rebased on main; the review carried over the rebase, and its open must-fix; the checks passed again." "$OPEN/.lem/state/tasks/open-must-fix/pr.md" \
  && [ "$logged" = "[(False, None), (False, 'the review carried over the rebase, and its open must-fix')]" ] \
  && [ "$(field 'd["ran"]' <<<"$open_merged")" = "[['merge', 'open-must-fix', 'owner']]" ] && [ "$(status_in "$OPEN" open-must-fix)" = landed ] \
  && [ "$(kept_in "$OPEN" open-must-fix merged_by | "$PY" -c 'import ast, sys; d = ast.literal_eval(sys.stdin.read()); print((d["by"], d["via"], d.get("after")))')" = "('owner', 'server', 'a re-check')" ] \
  && [ "$open_reviews" = "[False, False, True]" ] \
  && [ "$(git -C "$OPEN.origin.git" log -2 --format=%s main)" = "$(printf '%s\n' 'fix: open-must-fix' 'docs: moved')" ]; then
  pass "a review that left a must-fix open carries over a rebase with no conflict as it was: the request stays not green for the same must-fix, the pull request's text and the proposed event say that the review and its open must-fix carried, the merge review carries, the owner's merge stands, and the server merges it"
else
  fail "a clean rebase of an open must-fix: $first / $called / $pressed / $round / $due_open / $reproposed / $logged / $open_merged / $open_reviews / $(kept_in "$OPEN" open-must-fix merged_by) / $(status_in "$OPEN" open-must-fix)"
fi

# The same moved base, read by a fresh merge agent instead of a new landing: the server's merge of the second
# task meets the base the first one moved, Lem keeps the refusal and wakes the session, whose merge agent reads
# what moved and answers `Base: safe.`. That read answers the refusal: the server's next look merges the second
# task on the moved base with no new run of its checks, and the board reads it as Lem's merge, not a new landing.
SAFE=$WORK/safe-shop
git init -q -b main "$SAFE" && ident "$SAFE" && commit "$SAFE" init && on_github "$SAFE"
project --repo "$SAFE" init --base main >/dev/null
printf '%s\n' '[branch]' 'base = "main"' 'land = "agent"' 'history = "squash"' '[checks]' 'commands = ["true"]' > "$SAFE/.lem/project.toml"
git -C "$SAFE" add -A && git -C "$SAFE" commit -q -m "chore: start" && git -C "$SAFE" push -q origin main
# safe_read SLUG SECOND: the merge agent's read of the proposed task, its brief and then its answer, with SECOND as
# the answer's second line when it is not empty, recorded with the tip and the base the brief named; prints the record
safe_read() {
  local brief answer
  brief=$(land --repo "$SAFE" merge-review "$1") || return 1
  answer=$(field 'd["answer"]' <<<"$brief")
  printf 'Verdict: merge. The change does what its criterion says.\n%s\nIts test proves it, and the task took as long as expected.\n' "$2" > "$answer"
  land --repo "$SAFE" merge-review "$1" --file "$answer" --tip "$(field 'd["tip"]' <<<"$brief")" --base "$(field 'd["base"]' <<<"$brief")"
}
for slug in docs-first code-second; do
  task_in "$SAFE" "$slug" "$slug.txt" yes && read_in "$SAFE" "$slug"
  land --repo "$SAFE" start "$slug" >/dev/null && land --repo "$SAFE" base "$slug" >/dev/null && polish_in "$SAFE" "$slug"
  land --repo "$SAFE" checks "$slug" >/dev/null && land --repo "$SAFE" read "$slug" --record "$(clean "$slug" 1)" >/dev/null
  land --repo "$SAFE" propose "$slug" --title "fix: $slug" --notes "$NOTES" >/dev/null && safe_read "$slug" "" >/dev/null
done
land --repo "$SAFE" merge docs-first --by merger --via server --message "fix: docs-first" >/dev/null
CHECKS_RAN=$(events "$SAFE" gate.start code-second)
PROPOSED=$(kept_in "$SAFE" code-second proposed)
# safe_duty: the server's duties once, its merge's thread joined; then what it owes, and how the board reads the task
safe_duty() {
  "$PY" -B -c '
import json, sys, threading
sys.path.insert(0, "skills/lem/scripts")
import serve, lem_board_model as bm
w = serve.Workspace("safe-shop", sys.argv[1])
ran = serve.run_duties(w)
for thread in threading.enumerate():
    if thread.name.startswith("merge "):
        thread.join(120)
m = w.model()
t = m.by_slug["code-second"]
review = next((e for e in reversed(t.events) if e.get("event") == "merge.review"), {})
print(json.dumps({"ran": [(x["verb"], x["task"], x["why"]) for x in ran], "owed": serve.duties(m, {}, set()), "wait": t.merge_wait, "status": t.status,
                  "feed": bm.describe(review, m)}))
' "$SAFE"
}
refused=$(safe_duty)
kept=$(kept_in "$SAFE" code-second merge_refused | "$PY" -c 'import ast, sys; d = ast.literal_eval(sys.stdin.read()); print((d["from"], d["kind"]))')
moved=$(land --repo "$SAFE" merge-review code-second | field '("docs-first.txt" in d["facts"]["moved"]["files"], d["facts"]["moved"]["overlap"])')
said=$(safe_read code-second "Base: safe. docs-first only added docs-first.txt, which this change neither edits nor reads.")
read_now=$("$PY" -B -c '
import json, sys
sys.path.insert(0, "skills/lem/scripts")
import serve
w = serve.Workspace("safe-shop", sys.argv[1])
t = w.model().by_slug["code-second"]
print(json.dumps({"owed": serve.duties(w.model(), {}, set()), "wait": t.merge_wait, "refused": t.refused}))
' "$SAFE")
merged=$(safe_duty)
if [ "$(field '(d["ran"], d["owed"], d["wait"])' <<<"$refused")" = "([['merge', 'code-second', 'merger']], [['wake', 'code-second', 'refused']], 'reads')" ] \
  && [ "$kept" = "('lem', 'base')" ] && [ "$moved" = "(True, [])" ] \
  && [ "$(field '(d["owed"], d["wait"], d["refused"])' <<<"$read_now")" = "([['merge', 'code-second', 'merger']], 'merges', None)" ] \
  && [ "$(field '(d["ran"], d["status"])' <<<"$merged")" = "([['merge', 'code-second', 'merger']], 'landed')" ] \
  && [ "$(field 'bool(__import__("re").fullmatch(r"the moved base [0-9a-f]+ is safe; it merges", d["feed"]["text"]))' <<<"$merged")" = True ] \
  && [ "$(field 'd["feed"]["sub"]' <<<"$merged")" = "docs-first only added docs-first.txt, which this change neither edits nor reads." ] \
  && [ "$(events "$SAFE" gate.start code-second)" = "$CHECKS_RAN" ] && [ "$(kept_in "$SAFE" code-second proposed)" = "$PROPOSED" ] \
  && [ "$(git -C "$SAFE.origin.git" log -2 --format=%s main)" = "$(printf '%s\n' 'fix: code-second' 'fix: docs-first')" ] \
  && [ "$(git -C "$SAFE.origin.git" show main:docs-first.txt)" = yes ] && [ "$(git -C "$SAFE.origin.git" show main:code-second.txt)" = yes ]; then
  pass "a merge that meets the base another merge moved waits for the merge agent's read of what moved; its Base: safe. answers Lem's refusal, and the server's next look merges the task on the moved base with no new run of the checks, keeping what moved, the board showing the read and its why"
else
  fail "the server's merge after a safe read of a moved base: $refused / $kept / $moved / $said / $read_now / $merged / $(events "$SAFE" gate.start code-second) vs $CHECKS_RAN / $(git -C "$SAFE.origin.git" log -3 --format=%s main)"
fi

finish
