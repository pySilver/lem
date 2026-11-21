#!/usr/bin/env bash
# The board server (serve.py) and lem board (board.py), over HTTP: the afternoon of tests/board-showcase.py in a
# throwaway repository, a server of this run on its own port and home folder (tests/lib.sh), and curl. The routes,
# what each page says, what is not served, the stream, the jump to a task's session with a stand-in for agtermctl,
# lem board's address and its companion, and the start on demand. The tailnet door needs Tailscale: its rule is a unit case
# (tests/unit/test_serve.py), and no check here runs the tailscale command.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

BOARD=$PWD/skills/lem/scripts/board.py
# A stand-in for agtermctl, first on the PATH of this block and of its server: it prints the tree of AGT_TREE and records
# each call in AGT_CALLS.
FAKE=$WORK/fake
mkdir -p "$FAKE"
# shellcheck disable=SC2016  # the stand-in's own variables, expanded when it runs
printf '%s\n' '#!/bin/sh' 'echo "$*" >> "$AGT_CALLS"' 'case "$1" in tree) cat "$AGT_TREE" ;; session) [ "$2 $3" = "overlay open" ] && echo "{\"result\": {\"id\": \"NEW\"}}" ;; esac' 'exit 0' > "$FAKE/agtermctl"
chmod +x "$FAKE/agtermctl"
export PATH="$FAKE:$PATH" AGT_CALLS="$WORK/calls" AGT_TREE="$WORK/tree.json"
DEMO=$("$PY" -B tests/board-showcase.py --demo "$WORK/demo" | field 'd["repo"]')
STATE=$DEMO/.lem/state
"$PY" -B "$SERVE" --add "$DEMO" >/dev/null
serve_up
SERVER=http://127.0.0.1:$SERVE_PORT
HOST=$(curl -fsS "$SERVER/api/server" | field 'd["host"]')
BASE=$SERVER/$HOST/shop
# code URL: the status of a GET; got URL: its body
code() { curl -s -o /dev/null -w '%{http_code}' "$@" || true; }
got() { curl -fsS "$@"; }
# words: the text of an HTML page on stdin, its tags taken out
words() { "$PY" -c 'import html, re, sys; t = sys.stdin.read(); t = re.sub(r"(?s)<(script|style|template|svg)\b.*?</\1>", " ", t); print(" ".join(html.unescape(re.sub(r"<[^>]+>", " ", t)).split()))'; }
# lanes: the kanban on stdin as {column: [the tasks of its cards]}
lanes() { "$PY" -c 'import re, sys; t = sys.stdin.read(); cols = re.split(r"<section class=\"col [^\"]*\" id=\"col-", t)[1:]; print({c.split("\"", 1)[0]: re.findall(r"<article[^>]*id=\"card-([a-z0-9-]+)\"", c) for c in cols})'; }

server=$(got "$SERVER/api/server")
listed=$(got "$SERVER/api/workspaces")
if [ "$(field '(d["port"], d["config"])' <<<"$server")" = "($SERVE_PORT, '$XDG_CONFIG_HOME/lem')" ] && [ -n "$HOST" ] \
  && [ "$(field '[(w["name"], w["url"], w["waits"], w["building"], w["checks"]) for w in d]' <<<"$listed")" = "[('shop', '/$HOST/shop/', 6, 2, 1)]" ] \
  && [ "$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' "$SERVER/")" = "302 $BASE/" ]; then
  pass "/api/server names the server of this home folder and the machine's name, /api/workspaces counts what waits, what builds and what is in its checks, and / with one workspace goes to its board"
else
  fail "the server and its workspaces: $server / $listed"
fi

kanban=$(got "$BASE/")
said=$(words <<<"$kanban")
if [ "$(lanes <<<"$kanban")" = "{'you': ['gift-note-in-export', 'stock-on-product-page', 'refund-line-on-receipt', 'footer-terms-typo'], 'build': ['refund-rounding', 'cart-total-after-coupon'], 'checks': ['coupon-has-a-slug'], 'done': ['order-date-on-invoice', 'why-export-is-slow']}" ] \
  && grep -qF "The criteria wait for you" <<<"$said" && grep -qF "Investigating: an investigator reproduces the bug" <<<"$said" \
  && grep -qF "Waits for the merge: pull request #41" <<<"$said" && grep -qF "Landed: main: pull request #38 is merged" <<<"$said" \
  && grep -qF "Demo data." <<<"$said" && grep -qF "Read the breaker of gift-note-in-export" <<<"$said" && ! grep -qF 'id="card-fee-notice-to-merchants"' <<<"$kanban" && grep -qF 'data-agterm-url-value="/'"$HOST"'/shop/agterm"' <<<"$kanban"; then
  pass "the kanban puts each task in the column of who acts and a parked one in none, each card says its state in the board's words, the sidebar has what waits, and a page for this Mac carries the address of agterm's acts"
else
  fail "the kanban: $(lanes <<<"$kanban") / ${said:0:1500}"
fi

T=$BASE/tasks/order-date-on-invoice
tabs=""
for tab in "" /criteria /checks /timeline /artifacts "?in=waits" /artifacts/report.md/; do tabs="$tabs $(code "$T$tab")"; done
overview=$(got "$T" | words)
frame=$(got -H 'Turbo-Frame: task' "$T")
for view in waits backlog activity; do tabs="$tabs $(code "$BASE/$view")"; done
if [ "$tabs" = " 200 200 200 200 200 200 404 200 200 200" ] && grep -qF "What we are building" <<<"$overview" \
  && grep -qF "1 backlog item filed" <<<"$overview" && grep -qF "The invoice footer wraps on A5" <<<"$overview" \
  && grep -q '<turbo-frame id="task"' <<<"$frame" && ! grep -q 'id="col-you"' <<<"$frame"; then
  pass "a task's Overview and each of its tabs and each view answer, Overview names the backlog item the task's branch filed, a request of the frame gets the panel alone, and a file the task does not have is not found"
else
  fail "the task's pages: $tabs / ${overview:0:800}"
fi

# An artifact: markdown as escaped text the browser renders, a page of HTML only from the raw route under a sandbox,
# and nothing outside a task's own files.
printf '%s\n' '<!doctype html><title>The owner page</title><p>Built.</p>' > "$STATE/tasks/order-date-on-invoice/page.html"
printf '%s\n' 'line one <b>not markup</b>' 'line two' > "$STATE/tasks/order-date-on-invoice/report.md"
art=$(got "$T/artifacts/report.md/")
raw_headers=$(curl -fsS -D - -o "$WORK/raw.html" "$T/raw/page.html")
outside=""
for path in "$BASE/events.jsonl" "$BASE/tasks/order-date-on-invoice/raw/report.md" "$BASE/tasks/order-date-on-invoice/raw/..%2F..%2Fevents.jsonl" \
  "$BASE/tasks/order-date-on-invoice/artifacts/..%2F..%2Fevents.jsonl/" "$BASE/tasks/No-Such" "$BASE/tasks/no-such-task" "$BASE/old/board.html" "$BASE/meta.js" \
  "$SERVER/assets/..%2Fscripts%2Fserve.py" "$SERVER/$HOST/no-such-workspace/" "$BASE/tasks/order-date-on-invoice/raw/decisions.lock"; do
  outside="$outside $(code "$path")"
done
if grep -qF 'line one &lt;b&gt;not markup&lt;/b&gt;' <<<"$art" && ! grep -qF '<b>not markup' <<<"$art" \
  && grep -qi '^content-security-policy: sandbox allow-scripts' <<<"$raw_headers" && grep -qF '<p>Built.</p>' "$WORK/raw.html" \
  && [ "$outside" = " 404 404 404 404 404 404 404 404 404 404 404" ]; then
  pass "an artifact's text reaches the page escaped, an HTML artifact comes only from the raw route under a sandbox, and the log, a lock, a path out of a task's files, an unknown task or workspace and the old page's files are not found"
else
  fail "artifacts and what is not served: $outside / $raw_headers / ${art:0:300}"
fi

# A task's pictures: a picture of its media folder only, by its name and its first bytes, never another file.
R=$BASE/tasks/refund-line-on-receipt
MEDIA=$STATE/tasks/refund-line-on-receipt/media
printf '%s\n' '<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>' > "$MEDIA/drawn.svg"
printf '%s\n' 'a text with the name of a picture' > "$MEDIA/text.png"
picture=$(curl -s -o "$WORK/after.png" -w '%{http_code} %{content_type}' "$R/media/receipt-after.png")
refused=""
for path in media/drawn.svg media/text.png "media/..%2Freport.md" media/; do refused="$refused $(code "$R/$path")"; done
rm "$MEDIA/drawn.svg" "$MEDIA/text.png"
if [ "$picture" = "200 image/png" ] && cmp -s "$WORK/after.png" "$MEDIA/receipt-after.png" && [ "$refused" = " 404 404 404 404" ]; then
  pass "a task's picture comes from its media route, and an SVG, a text with a picture's name and a path out of the folder do not"
else
  fail "the media route: $picture / $refused"
fi

# A proposal that is not green lists its reasons, one row each: the reason in plain words, its detail folded under it.
checks=$(got "$R/checks")
rows=$("$PY" -c 'import re, sys; t = sys.stdin.read(); print([re.sub(r"<[^>]+>", "", h) for h in re.findall(r"<span class=\"rs-head\">(.*?)</span>", t.split("id=\"pr-reasons\"", 1)[-1])])' <<<"$checks")
if [ "$rows" = "['Decision 1 was taken without the owner', 'The owner did not approve the criteria', 'The bar is lower in tests/test_receipt.py', 'Two rounds reviewed it']" ] \
  && grep -qF '<details class="rs-fold" id="pr-r3">' <<<"$checks" && grep -qF 'href="https://github.com/acme/shop/pull/44"' <<<"$checks"; then
  pass "a proposal that is not green lists each reason as a row of its own with its detail folded under it, and a pull request it names is a link"
else
  fail "the reasons of not green: $rows"
fi

# A breaker: one row of "Waits for you" that opens the task on its document, which is the first card of its Overview;
# a parked task in its own folded group under the rows, with why and the command that brings it back.
waits=$(got "$BASE/waits")
breaker=$(got "$BASE/tasks/gift-note-in-export")
first=$("$PY" -c 'import re, sys; t = sys.stdin.read().split("id=\"tb-overview\"", 1)[-1]; print(re.findall(r"<section class=\"card[^\"]*\" id=\"([a-z-]+)\"", t)[:2])' <<<"$breaker")
if grep -qF 'id="wait-breaker-gift-note-in-export-1"' <<<"$waits" && grep -qF "Read the breaker of gift-note-in-export" <<<"$waits" \
  && grep -qF 'id="parked"' <<<"$waits" && grep -qF "wait for the merchants&#x27; association to confirm the fee date" <<<"$waits" && grep -qF "/lem resume fee-notice-to-merchants" <<<"$waits" \
  && [ "$first" = "['breaker', 'building']" ] && grep -qF "# The gift note has no place in the export that keeps criterion 1" <<<"$breaker" && grep -qF "/lem park gift-note-in-export" <<<"$breaker"; then
  pass "a breaker is one row of Waits for you, its document is the first card of the task's Overview, and a parked task stands in a group of its own with why and /lem resume"
else
  fail "the breaker and the parked task: $first / $(words <<<"$waits" | head -c 1200)"
fi

# The backlog's filter is in the address: a shared link shows the same list. The server draws every item with the
# field and the chip the address picks, and the backlog controller hides what the filter leaves out.
filtered=$(got "$BASE/backlog?worth=later&q=query")
shown=$("$PY" -c 'import re, sys; t = sys.stdin.read(); print(sorted(re.findall(r"<details class=\"bl-item\" id=\"item-([a-z0-9-]+)\"(?![^>]*data-js-out)", t)))' <<<"$filtered")
if [ "$shown" = "['export-in-one-query', 'invoice-footer-wraps']" ] && grep -qF 'id="f-worth-later" href="/'"$HOST"'/shop/backlog?q=query" data-turbo-action="replace"' <<<"$filtered" \
  && grep -qF 'aria-pressed="true"' <<<"$filtered" && grep -qF 'value="query"' <<<"$filtered"; then
  pass "the backlog's filter comes from the address: its words in the field and its chip on, over every item, so a shared link shows the same list"
else
  fail "the backlog's filter: $shown"
fi

# The diagram library: a document with a chart names it, and a page with none never does.
charted=$(got "$R")
library=$("$PY" -c 'import re, sys; print((re.findall(r"data-lem-mermaid=\"([^\"]+)\"", sys.stdin.read()) or [""])[0])' <<<"$charted")
if [ -n "$library" ] && [ "$(code "$SERVER$library")" = 200 ] && grep -qF 'id="t-i-expand"' <<<"$charted" \
  && ! got "$BASE/" | grep -q mermaid && ! got "$T" | grep -q mermaid && ! got "$BASE/backlog" | grep -q mermaid; then
  pass "a document with a chart names the diagram library and the icons of the chart's controls, and a page with no chart never names it"
else
  fail "the diagram library: '$library' / $(got "$BASE/" | grep -c mermaid)"
fi

# The switcher names a workspace whole, however long its name, and the machine under it only when there are two.
LONG=$WORK/a-repository-whose-name-is-longer-than-the-sidebar-is-wide
git init -q -b main "$LONG" && commit "$LONG" init && project --repo "$LONG" init --base main >/dev/null && mkdir -p "$LONG/.lem/state"
"$PY" -B "$SERVE" --add "$LONG" >/dev/null
switcher=$(got "$SERVER/$HOST/a-repository-whose-name-is-longer-than-the-sidebar-is-wide/")
"$PY" -B "$SERVE" --remove "$LONG" >/dev/null
if grep -qF '<span class="ws-label"><span class="ws-name">a-repository-whose-name-is-longer-than-the-sidebar-is-wide</span></span>' <<<"$switcher" \
  && grep -qF '<span class="ws-n">shop</span>' <<<"$switcher" && ! grep -qF 'ws-host' <<<"$switcher"; then
  pass "the switcher names the workspace whole, however long its name, and with one machine names no machine"
else
  fail "the switcher: $(grep -o '<details class="ws".*</details>' <<<"$switcher" | head -c 800)"
fi

# Another name of the machine, and an address with no machine's name in it, reach the same page.
alias=$(field '(d["aliases"] or [""])[0]' <<<"$server")
moved=$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' "$SERVER/shop/backlog")
if [ -z "$alias" ]; then
  skip "the machine's other name goes to the same page under its name: this machine has no name on a tailnet"
elif [ "$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' "$SERVER/$alias/shop/tasks/order-date-on-invoice?in=waits")" = "302 $BASE/tasks/order-date-on-invoice?in=waits" ] \
  && [ "$moved" = "302 $BASE/backlog" ]; then
  pass "the machine's other name goes to the same page under its name, and so does an address with no machine's name in it"
else
  fail "the machine's other name: $alias / $moved"
fi

# The stream: a refresh within seconds of a state block, and of a file of the open task written with no event.
count=$(grep -c '' "$STATE/events.jsonl")
curl -sN --max-time 6 "$BASE/stream?since=$count" > "$WORK/stream.out" 2>/dev/null &
streamed=$!
soon grep -q ': open' "$WORK/stream.out"
project --repo "$DEMO" state cart-total-after-coupon building "an investigator reproduces the bug and finds its cause" "investigation: bug" >/dev/null
wait "$streamed" || true
curl -sN --max-time 4 "$BASE/stream?since=$((count + 1))&task=why-export-is-slow" > "$WORK/stream-task.out" 2>/dev/null &
streamed=$!
soon grep -q ': open' "$WORK/stream-task.out"
echo 'written by an agent, with no event' > "$STATE/tasks/why-export-is-slow/notes.md"
wait "$streamed" || true
if grep -qxF "id: $((count + 1))" "$WORK/stream.out" && grep -qxF 'data: <turbo-stream action="refresh"></turbo-stream>' "$WORK/stream.out" \
  && grep -qxF 'data: <turbo-stream action="refresh"></turbo-stream>' "$WORK/stream-task.out"; then
  pass "the stream sends Turbo a refresh, its id the log's line count, within seconds of a state block, and of a file of the open task written with no event"
else
  fail "the stream: $(cat "$WORK/stream.out") / $(cat "$WORK/stream-task.out")"
fi

# lem board, with a stand-in for agtermctl that prints a tree and records its calls: the board opens at the server's
# address as a page companion of the session's group, and is known by its workspace's address. A state folder of an
# older Lem loses the copies of the old page, and nothing else.
printf '%s\n' '{"result": {"tree": {"workspaces": [{"sessions": [{"id": "LEM", "foreground": ["/usr/local/bin/claude"]}, {"id": "OTHER"},' \
  '{"id": "PX", "content": "page", "parent": "LEM", "htmlOverlays": [{"url": "http://127.0.0.1:1/elsewhere/shop/", "page": "http://127.0.0.1:1/elsewhere/shop/"}]},' \
  "{\"id\": \"PA\", \"name\": \"Lem board\", \"content\": \"page\", \"parent\": \"LEM\", \"htmlOverlays\": [{\"url\": \"$BASE/\", \"page\": \"$BASE/backlog\"}]}," \
  "{\"id\": \"PO\", \"name\": \"Lem board · shop\", \"content\": \"page\", \"parent\": \"OTHER\", \"htmlOverlays\": [{\"file\": \"$STATE/board.html\"}]}]}]}}}" > "$WORK/tree.json"
opened() { : > "$AGT_CALLS"; env -u AGTERM_WINDOW_ID -u AGT_WINDOW_ID -u AGT_SESSION_ID -u AGT_SOCKET AGTERM_SESSION_ID="$1" AGTERM_SOCKET="$WORK/agterm.sock" "$PY" -B "$BOARD" --repo "$DEMO" "${@:2}"; }
mkdir -p "$STATE/vendor" "$STATE/artifacts" && touch "$STATE/board.html" "$STATE/meta.js" "$STATE/events.js" "$STATE/owner.js" "$STATE/task-gift-note-in-export.html" "$STATE/vendor/board-kit.js" "$STATE/artifacts/x.js" "$STATE/keep.txt"
kept=$(opened LEM)
kept_calls=$(cat "$AGT_CALLS")
fresh=$(opened OTHER --task stock-on-product-page --follow)
fresh_calls=$(cat "$AGT_CALLS")
moved=$(opened LEM --task stock-on-product-page)
moved_calls=$(cat "$AGT_CALLS")
left=$(cd "$STATE" && ls -d board.html meta.js events.js owner.js task-gift-note-in-export.html vendor artifacts 2>/dev/null || true)
if [ "$(field '(d["url"], d["companion"], d["reloaded"], d["name"], d["removed"])' <<<"$kept")" = "('$BASE/', 'PA', True, 'Lem board · shop', ['board.html', 'meta.js', 'owner.js', 'events.js', 'vendor/', 'artifacts/', 'task-gift-note-in-export.html'])" ] \
  && grep -qxF "session overlay reload --current --target PA --socket $WORK/agterm.sock" <<<"$kept_calls" && ! grep -q "PX\|overlay open\|session close" <<<"$kept_calls" \
  && [ -z "$left" ] && [ -f "$STATE/keep.txt" ] && [ -f "$STATE/events.jsonl" ] \
  && [ "$(field '(d["companion"], d["parent"], d["reloaded"])' <<<"$fresh")" = "('NEW', 'OTHER', False)" ] && grep -qxF "session close --target PO --socket $WORK/agterm.sock" <<<"$fresh_calls" \
  && grep -qxF "session overlay open --url $BASE/tasks/stock-on-product-page --persistent --js --companion --target OTHER --json --socket $WORK/agterm.sock" <<<"$fresh_calls" \
  && grep -qxF "session select --target NEW --socket $WORK/agterm.sock" <<<"$fresh_calls" \
  && grep -qxF "session close --target PA --socket $WORK/agterm.sock" <<<"$moved_calls" && grep -qF "overlay open --url $BASE/tasks/stock-on-product-page" <<<"$moved_calls"; then
  pass "lem board opens the server's address as a page companion: its workspace's board is reloaded where it stands, a task's board opens anew, one that shows the old page as a file is closed, another repository's is left alone, and the old page's copies go"
else
  fail "lem board: $kept / $kept_calls / $fresh / $fresh_calls / $moved_calls / $left"
fi

# The jump to a task's session, as the board's page asks it: on this Mac, from the board's own origin, and only to the
# session of a task's newest session.open; the typing into a session is no route. A task stuck with no session is a row
# of Waits for you with "Open a session", and a task whose session lives has none.
act() { curl -s -X POST -H "Origin: ${3:-$SERVER}" -H 'Content-Type: application/json' -d "$2" "$BASE/agterm/$1"; }
GIFT=$("$PY" -c 'import json, sys; print([e for e in map(json.loads, open(sys.argv[1])) if e["event"] == "session.open" and e["task"] == "gift-note-in-export"][-1]["session"])' "$STATE/events.jsonl")
: > "$AGT_CALLS"
switched=$(act select "{\"session\": \"$GIFT\"}")
not_ours=$(act select '{"session": "OTHER"}')
other_site=$(act select "{\"session\": \"$GIFT\"}" https://evil.example)
typed_code=$(curl -s -o /dev/null -w '%{http_code}' -X POST -H "Origin: $SERVER" -H 'Content-Type: application/json' -d '{"line": "/lem status gift-note-in-export"}' "$BASE/agterm/type")
act_calls=$(cat "$AGT_CALLS")
waits=$(got "$BASE/waits")
stuck=$(got "$BASE/tasks/cart-total-after-coupon")
lives=$(got "$BASE/tasks/gift-note-in-export")
if [ "$(field '(d["done"], d["said"])' <<<"$switched")" = "(True, 'Switched to the session.')" ] && grep -qF "no session of this workspace's tasks" <<<"$not_ours" \
  && grep -qF "another origin" <<<"$other_site" && [ "$typed_code" = 405 ] && [ "$act_calls" = "session select --target $GIFT" ] \
  && grep -qF 'id="wait-session-cart-total-after-coupon"' <<<"$waits" && grep -qF "No session runs this task" <<<"$waits" \
  && grep -qF 'action="/'"$HOST"'/shop/tasks/cart-total-after-coupon/session"' <<<"$waits" && grep -qF 'action="/'"$HOST"'/shop/tasks/cart-total-after-coupon/session"' <<<"$stuck" \
  && ! grep -qF '/tasks/gift-note-in-export/session"' <<<"$lives" && grep -qF "Go to the session" <<<"$lives"; then
  pass "the board jumps only to a task's own session, with no socket and no typing; a task with no session is a row of Waits for you, and it and its header have Open a session"
else
  fail "the jump and the row of no session: $switched / $not_ours / $other_site / $typed_code / $act_calls / $(words <<<"$waits" | head -c 1200)"
fi

# The board's notifications: the machine's key, a device that turns them on from the board's own page and only from it,
# the list it lands in, and the way off. The endpoint is a stand-in that nothing sends to (LEM_PUSH=record, tests/lib.sh),
# and the demo workspace sends nothing.
ENDPOINT=https://fcm.googleapis.com/fcm/send/lem-test-not-a-device
on_page() { curl -s -X POST -H "Origin: ${3:-$SERVER}" -H 'Sec-Fetch-Site: same-origin' -H 'Content-Type: application/json' -H 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148' -d "$2" "$SERVER/api/push/$1"; }
key=$(got "$SERVER/api/push/key")
added=$(on_page subscribe "{\"endpoint\": \"$ENDPOINT\", \"keys\": {\"p256dh\": \"x\", \"auth\": \"y\"}}")
listed_push=$(got "$SERVER/api/server")
elsewhere=$(on_page subscribe "{\"endpoint\": \"$ENDPOINT-2\"}" https://evil.example)
not_a_service=$(on_page subscribe '{"endpoint": "https://127.0.0.1/x"}')
removed=$(on_page unsubscribe "{\"endpoint\": \"$ENDPOINT\"}")
worker=$(curl -fsS -D - -o /dev/null "$SERVER/sw.js")
if [ "$(field 'len(d["key"])' <<<"$key")" = 87 ] && [ "$("$PY" -c 'import os, sys; print(oct(os.stat(sys.argv[1]).st_mode & 0o777))' "$XDG_CONFIG_HOME/lem/push-key.pem")" = 0o600 ] \
  && [ "$(field '(d["on"], d["device"], d["devices"])' <<<"$added")" = "(True, 'iPhone · Safari', 1)" ] \
  && [ "$(field '[x["device"] for x in d["push"]["devices"]]' <<<"$listed_push")" = "['iPhone · Safari']" ] \
  && grep -qF "only from the board's own page" <<<"$elsewhere" && grep -qF "IP address" <<<"$not_a_service" \
  && [ "$(field '(d["removed"], d["devices"])' <<<"$removed")" = "(True, 0)" ] && grep -qi '^content-type: text/javascript' <<<"$worker" \
  && got "$BASE/waits" | grep -qF 'id="push-page" data-controller="push"' && [ ! -e "$XDG_CONFIG_HOME/lem/push-record.jsonl" ]; then
  pass "the board's notifications: the machine's key is made once and kept to its owner, a device on the board's own page turns them on and off, another origin and an address that is no push service are refused, and the worker is served"
else
  fail "the board's notifications: $key / $added / $elsewhere / $not_a_service / $removed / $worker"
fi

# The start on demand: the foreground server ends with --stop; --ensure twice makes one server, which keeps its pid and
# port in Lem's home folder for bin/lem's look, and --stop ends it and its file.
stopped_fg=$("$PY" -B "$SERVE" --stop)
wait "$SERVE_PID" 2>/dev/null || true
SERVE_PID=""
first=$(env -u LEM_SERVE "$PY" -B "$SERVE" --ensure)
SERVE_PID=$(field 'd["pid"]' <<<"$first")
second=$(env -u LEM_SERVE "$PY" -B "$SERVE" --ensure)
pid_kept=$(cat "$XDG_CONFIG_HOME/lem/serve.pid" 2>/dev/null || true)
ended=$("$PY" -B "$SERVE" --stop)
soon test ! -e "$XDG_CONFIG_HOME/lem/serve.pid"
gone=$(code "$SERVER/api/server")
SERVE_PID=""
if [ "$(field 'd["stopped"]' <<<"$stopped_fg")" = True ] && [ "$(field '(d["running"], d["started"])' <<<"$first")" = "(True, True)" ] \
  && [ "$(field '(d["running"], d["started"], d["pid"])' <<<"$second")" = "(True, False, $(field 'd["pid"]' <<<"$first"))" ] \
  && [ "$(field '(d["stopped"], d["pid"])' <<<"$ended")" = "(True, $(field 'd["pid"]' <<<"$first"))" ] && [ "$gone" = 000 ] \
  && [ "$pid_kept" = "$(field 'd["pid"]' <<<"$first") $SERVE_PORT" ] && [ ! -e "$XDG_CONFIG_HOME/lem/serve.pid" ]; then
  pass "--stop ends the server that runs, --ensure starts one and keeps it at a second call with its pid and port in the home folder, and --stop then ends it and removes the file"
else
  fail "the start on demand: $stopped_fg / $first / $second / $ended / $gone / $pid_kept"
fi

finish
