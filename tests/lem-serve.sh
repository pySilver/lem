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
  && [ "$(field '[(w["name"], w["url"], w["waits"], w["building"], w["checks"]) for w in d]' <<<"$listed")" = "[('shop', '/$HOST/shop/', 5, 2, 1)]" ] \
  && [ "$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' "$SERVER/")" = "302 $BASE/" ]; then
  pass "/api/server names the server of this home folder and the machine's name, /api/workspaces counts what waits, what builds and what is in its checks, and / with one workspace goes to its board"
else
  fail "the server and its workspaces: $server / $listed"
fi

kanban=$(got "$BASE/")
said=$(words <<<"$kanban")
if [ "$(lanes <<<"$kanban")" = "{'you': ['gift-note-in-export', 'stock-on-product-page', 'refund-line-on-receipt'], 'build': ['refund-rounding', 'cart-total-after-coupon'], 'checks': ['coupon-has-a-slug'], 'done': ['footer-terms-typo', 'order-date-on-invoice', 'why-export-is-slow']}" ] \
  && grep -qF "The criteria wait for you" <<<"$said" && grep -qF "Investigating: an investigator reproduces the bug" <<<"$said" \
  && grep -qF "Landed: main: pull request #41 is merged" <<<"$said" && grep -qF "Landed: main: pull request #38 is merged" <<<"$said" \
  && grep -qF "Demo data." <<<"$said" && grep -qF "Read the breaker of gift-note-in-export" <<<"$said" && ! grep -qF 'id="card-fee-notice-to-merchants"' <<<"$kanban" && grep -qF 'data-agterm-url-value="/'"$HOST"'/shop/agterm"' <<<"$kanban"; then
  pass "the kanban puts each task in the column of who acts and a parked one in none, each card says its state in the board's words, the sidebar has what waits, and a page for this Mac carries the address of agterm's acts"
else
  fail "the kanban: $(lanes <<<"$kanban") / ${said:0:1500}"
fi

# The main listener reads nothing for a Host of another name, as a page of another site that points its own name at
# this machine would send (DNS rebinding); its own names read.
foreign=""
for path in /api/server /api/workspaces "/$HOST/shop/" "/$HOST/shop/tasks/order-date-on-invoice"; do foreign="$foreign $(code -H "Host: evil.example:$SERVE_PORT" "$SERVER$path")"; done
if [ "$foreign" = " 403 403 403 403" ] && [ "$(code -H "Host: localhost:$SERVE_PORT" "$SERVER/api/server")" = 200 ] && [ "$(code "$SERVER/api/server")" = 200 ] \
  && curl -s -H "Host: evil.example:$SERVE_PORT" "$SERVER/api/workspaces" | grep -qF "not the board's own"; then
  pass "the main listener reads nothing for a Host that is none of its own names, and its own names read"
else
  fail "the main listener's Host: $foreign"
fi

# lem project waiting lists the rows of the board's Waits for you, in their order, and counts them as the server does.
waiting=$(project --repo "$DEMO" waiting)
rows=$(got "$BASE/waits" | "$PY" -c 'import re, sys; print(re.findall(r"<article class=\"wrow [^\"]*\" id=\"wait-([a-z0-9-]+)\"", sys.stdin.read()))')
if [ "$(field '[r["key"].replace(":", "-") for r in d["rows"]]' <<<"$waiting")" = "$rows" ] && [ "$(field 'd["count"]' <<<"$waiting")" = 5 ] \
  && [ "$(field '(d["sessions"]["known"], len(d["breakers"]), len(d["criteria"]))' <<<"$waiting")" = "(True, 1, 1)" ]; then
  pass "lem project waiting lists the rows of the board's Waits for you in their order, with the count /api/workspaces gives"
else
  fail "waiting and the board: $(field 'd["rows"]' <<<"$waiting") / $rows"
fi

T=$BASE/tasks/order-date-on-invoice
tabs=""
for tab in "" /criteria /checks /timeline /artifacts "?in=waits" "?in=done" /artifacts/report.md/; do tabs="$tabs $(code "$T$tab")"; done
overview=$(got "$T" | words)
frame=$(got -H 'Turbo-Frame: task' "$T")
for view in waits backlog activity "done"; do tabs="$tabs $(code "$BASE/$view")"; done
if [ "$tabs" = " 200 200 200 200 200 200 200 404 200 200 200 200" ] && grep -qF "What we are building" <<<"$overview" \
  && grep -qF "1 backlog item filed" <<<"$overview" && grep -qF "The invoice footer wraps on A5" <<<"$overview" \
  && grep -q '<turbo-frame id="task"' <<<"$frame" && ! grep -q 'id="col-you"' <<<"$frame"; then
  pass "a task's Overview and each of its tabs and each view answer, the list of older ended tasks too and a task over it, Overview names the backlog item the task's branch filed, a request of the frame gets the panel alone, and a file the task does not have is not found"
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

# The board of a task that ended long ago, after `lem project prune`: the task loses its working files (an agent's
# scratch, the review tool's archive of a round, a picture no document shows), and its Overview, its tabs, its
# documents, its records and the picture its report shows read as before. The server prunes no workspace of
# example tasks, so the prune runs here by hand, after the task's events were moved 400 days back.
TD=$STATE/tasks/order-date-on-invoice
mkdir -p "$TD/media" "$TD/reviews/order-date-on-invoice/01-initial/agents"
"$PY" -c 'import sys; [open(p, "wb").write(b"\x89PNG\r\n\x1a\n" + bytes(8)) for p in sys.argv[1:]]' "$TD/media/a.png" "$TD/media/b.png"
printf '%s\n' '# Report' '' 'The date under the number: ![the invoice](media/a.png)' > "$TD/report.md"
printf 'scratch\n' > "$TD/scratch.txt"
printf '# Round 1\n' > "$TD/reviews/order-date-on-invoice/01-initial/report.md"
printf '{}\n' > "$TD/reviews/order-date-on-invoice/01-initial/agents/a.jsonl"
"$PY" -c 'import json, os, sys
from datetime import datetime, timedelta, timezone
old = (datetime.now(timezone.utc) - timedelta(days=400)).strftime("%Y-%m-%dT%H:%M:%SZ")
lines = open(sys.argv[1], encoding="utf-8").read().split("\n")
for n, line in enumerate(lines):
    if line.strip() and json.loads(line).get("task") == "order-date-on-invoice":
        lines[n] = line.replace(json.loads(line)["ts"], old, 1)
# a new file in its place, so that the server, which reads the log on from where it stopped, reads it whole
open(sys.argv[1] + ".new", "w", encoding="utf-8").write("\n".join(lines))
os.replace(sys.argv[1] + ".new", sys.argv[1])' "$STATE/events.jsonl"
art_before=$(got "$T/artifacts" | words)
# card: the Done card of the task on the kanban on stdin
card() { "$PY" -c 'import re, sys; print(re.search(r"<article[^>]*id=\"card-order-date-on-invoice\".*?</article>", sys.stdin.read(), re.S)[0])'; }
card_before=$(got "$BASE/" | card)
version_before=$(log_version "$STATE/events.jsonl")
pruned_board=$(project --repo "$DEMO" prune)
ended_tabs=""
for tab in "" /criteria /checks /timeline /artifacts /artifacts/report.md/ /artifacts/task.md/ /media/a.png /media/b.png /artifacts/scratch.txt/; do ended_tabs="$ended_tabs $(code "$T$tab")"; done
art_after=$(got "$T/artifacts" | words)
card_after=$(got "$BASE/" | card)
summarized=$(got "$T" | words)
went=$(got "$T/checks" | words)
# a page that saw the log before the prune reconnects: the log is another file, so it is told at once
curl -sN --max-time 2 "$BASE/stream?since=$version_before" > "$WORK/stream-pruned.out" 2>/dev/null || true
if [ "$(field '[(t["task"], sorted(t["files"])) for t in d["tasks"]]' <<<"$pruned_board")" = "[('order-date-on-invoice', ['media/b.png', 'reviews/order-date-on-invoice/01-initial/agents/a.jsonl', 'scratch.txt'])]" ] \
  && [ "$(field '[(t["task"], t["status"]) for t in d["summarized"]]' <<<"$pruned_board")" = "[('order-date-on-invoice', 'landed')]" ] \
  && [ "$ended_tabs" = " 200 200 200 200 200 200 200 200 404 404" ] && grep -qF "scratch.txt" <<<"$art_before" && ! grep -qF "scratch.txt" <<<"$art_after" \
  && grep -qF "The task" <<<"$art_after" && grep -qF "Review round 01-initial" <<<"$art_after" && grep -qF "Report" <<<"$art_after" \
  && grep -qF "What we are building" <<<"$summarized" && grep -qF "became one summary: the task ended more than state.keep_days ago" <<<"$summarized" \
  && grep -qF "Its runs of the checks, its review rounds and the proposal’s reasons went with its events" <<<"$went" \
  && [ -n "$card_before" ] && [ "$card_before" = "$card_after" ] \
  && grep -qxF "id: $(log_version "$STATE/events.jsonl")" "$WORK/stream-pruned.out" && [ -f "$TD/state.md" ] && [ -f "$TD/criteria.json" ]; then
  pass "a task that ended long ago loses its working files to lem project prune and its events become one summary: its Done card is the same, its Overview says so, its tabs, its documents, its records and the picture a document shows still read, and a page that saw the old log is told at once"
else
  fail "the board of a pruned task: $ended_tabs / $(field '[(t["task"], t["files"]) for t in d["tasks"]]' <<<"$pruned_board" 2>&1) / $(cat "$WORK/stream-pruned.out") / ${card_before:0:400} / ${card_after:0:400} / ${summarized:0:600}"
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

# The search over every card (criteria 1, 2, 4 and 5 of docs/plans/2026-11-22-board-card-search.md): the Tasks view and
# "Activity" draw it closed, with its button in the bar and in the phone's bar, and its rows hold every card of the
# workspace in the order of the columns: a task of a column, the parked task, an ended task Done draws no card for and a
# backlog item, each with its chip. Twenty tasks that landed a minute ago put the afternoon's ended tasks past Done's cards.
"$PY" -c 'import json, sys
from datetime import datetime, timedelta, timezone
ts = (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
with open(sys.argv[1], "a", encoding="utf-8") as log:
    for n in range(1, 21):
        log.write(json.dumps({"ts": ts, "event": "task.state", "task": f"landed-now-{n:02d}", "status": "landed", "text": "merged", "lines": []}) + "\n")' "$STATE/events.jsonl"
# found: the search's box, its rows and the two buttons of a page on stdin, as one line
found() { "$PY" -c 'import re, sys
t = sys.stdin.read()
box = re.search(r"<div class=\"search\" id=\"search\"[^>]*>", t)
rows = re.findall(r"<a class=\"sr a-([a-z]+)\" id=\"sr-([a-z]+-[a-z0-9-]+)\"[^>]*>.*?<span class=\"pill sr-chip\"><i></i><span>([^<]*)</span>", t, re.S)
chips = {key: (actor, re.sub(r" \d{4}-\d{2}-\d{2}$", " DAY", chip)) for actor, key, chip in rows}
order = [key for _, key, _ in rows]
first = lambda key: order.index(key) if key in order else -1  # noqa: E731
buttons = [bool(re.search(r"<header class=\"" + bar + r"\">(?:(?!</header>).)*<button class=\"btn search-open[^>]*aria-label=\"[^\"]*Cmd-K", t, re.S)) for bar in ("bar", "mbar")]
print(bool(box) and "data-js-open" not in box[0], buttons, [chips.get(k) for k in ("task-stock-on-product-page", "task-fee-notice-to-merchants", "task-why-export-is-slow", "item-invoice-footer-wraps")],
      0 <= first("task-gift-note-in-export") < first("task-refund-rounding") < first("task-coupon-has-a-slug") < first("task-fee-notice-to-merchants") < first("task-landed-now-01") < first("item-invoice-footer-wraps"),
      "href=\"/" + sys.argv[1] + "/shop/backlog#item-invoice-footer-wraps\"" in t)' "$HOST"; }
search_kanban=$(got "$BASE/")
search_activity=$(got "$BASE/activity")
searched="True [True, True] [('you', 'Waits for you · held'), ('quiet', 'parked'), ('done', 'answered DAY'), ('gate', 'Backlog · worth: yes')] True True"
if [ "$(found <<<"$search_kanban")" = "$searched" ] && [ "$(found <<<"$search_activity")" = "$searched" ] \
  && ! grep -qF 'id="card-why-export-is-slow"' <<<"$search_kanban" && ! grep -qF 'id="card-fee-notice-to-merchants"' <<<"$search_kanban"; then
  pass "the Tasks view and Activity draw the search closed with its button in both bars, and its rows hold every card in the order of the columns: a task of a column, the parked task, an ended task Done has no card for and a backlog item, each with its chip"
else
  fail "the search over every card: $(found <<<"$search_kanban") / $(found <<<"$search_activity")"
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

# A task queued by his order after a task he dropped is one row of "Waits for you", in the sidebar and in the view, with
# the dropped task and the two words he types in any Lem session; it is the row lem project waiting gives, and after
# his word it is gone. A workspace of its own, so the demo afternoon and its pictures stay as they are.
ORD=$WORK/orders
git init -q -b main "$ORD" && commit "$ORD" init && project --repo "$ORD" init --base main >/dev/null
project --repo "$ORD" task-dir gift-note-in-export --ask "Add the gift note to the CSV export." >/dev/null
project --repo "$ORD" state gift-note-in-export building "lead: builder" >/dev/null
project --repo "$ORD" task-dir export-notes-in-order --ask "After gift-note-in-export: the export keeps the notes in their order." >/dev/null
project --repo "$ORD" state export-notes-in-order queued "the owner's order: \"After gift-note-in-export\"" "after: gift-note-in-export" "type: feat, because a new order" "then: the interview" >/dev/null
project --repo "$ORD" state gift-note-in-export dropped "the owner dropped it" >/dev/null
"$PY" -B "$SERVE" --add "$ORD" >/dev/null
OB=$SERVER/$HOST/orders
order_page=$(got "$OB/waits")
order_said=$(words <<<"$order_page")
order_side=$(got "$OB/")
order_rows=$("$PY" -c 'import re, sys; print(re.findall(r"<article class=\"wrow [^\"]*\" id=\"wait-([a-z0-9_-]+)\"", sys.stdin.read()))' <<<"$order_page")
order_list=$(project --repo "$ORD" waiting | field '([r["key"].replace(":", "-") for r in d["rows"]], [(t["task"], t["after"]) for t in d["after_dropped"]], d["count"])')
project --repo "$ORD" state export-notes-in-order dropped "the owner dropped it: /lem drop export-notes-in-order" >/dev/null
order_after=$(got "$OB/waits" | "$PY" -c 'import re, sys; print(re.findall(r"<article class=\"wrow [^\"]*\" id=\"wait-([a-z0-9_-]+)\"", sys.stdin.read()))')
"$PY" -B "$SERVE" --remove "$ORD" >/dev/null
if [ "$order_rows" = "['after_dropped-export-notes-in-order']" ] && [ "$order_list" = "(['after_dropped-export-notes-in-order'], [('export-notes-in-order', 'gift-note-in-export')], 1)" ] \
  && grep -qF "gift-note-in-export was dropped: your word starts or ends this task" <<<"$order_said" \
  && grep -qF "Where you answer: It waited for gift-note-in-export, which was dropped, so the result it waited for never came. Type " <<<"$order_said" \
  && grep -qF "start export-notes-in-order now" <<<"$order_said" && grep -qF "to start it without that result, or /lem drop export-notes-in-order to end it, in any Lem session of this repository." <<<"$order_said" \
  && grep -qF 'id="w-after_dropped-export-notes-in-order"' <<<"$order_side" && [ "$order_after" = "[]" ]; then
  pass "a task queued by his order after a task he dropped is one row of Waits for you, in the sidebar and the view, with the dropped task, \"start SLUG now\" and /lem drop SLUG in any Lem session, the same row lem project waiting gives, and after his word it is gone"
else
  fail "the row of a task queued after a dropped task: $order_rows / $order_list / $order_after / ${order_said:0:1200}"
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

# The stream: a refresh within seconds of a state block, and of a file of the open task written with no event. Its id is
# the log's version, its inode and its count of lines, which the page gives its stream.
version=$(log_version "$STATE/events.jsonl")
paged=$(got "$BASE/" | "$PY" -c 'import re, sys; print(re.search(r"data-stream-since-value=\"([^\"]*)\"", sys.stdin.read())[1])')
curl -sN --max-time 6 "$BASE/stream?since=$version" > "$WORK/stream.out" 2>/dev/null &
streamed=$!
soon grep -q ': open' "$WORK/stream.out"
project --repo "$DEMO" state cart-total-after-coupon building "an investigator reproduces the bug and finds its cause" "investigation: bug" >/dev/null
wait "$streamed" || true
grown=$(log_version "$STATE/events.jsonl")
curl -sN --max-time 4 "$BASE/stream?since=$grown&task=why-export-is-slow" > "$WORK/stream-task.out" 2>/dev/null &
streamed=$!
soon grep -q ': open' "$WORK/stream-task.out"
echo 'written by an agent, with no event' > "$STATE/tasks/why-export-is-slow/notes.md"
wait "$streamed" || true
if [ "$paged" = "$version" ] && [ "$grown" = "$(log_version "$STATE/events.jsonl")" ] && [ "$grown" = "${version%-*}-$(( ${version#*-} + 1 ))" ] \
  && grep -qxF "id: $grown" "$WORK/stream.out" && grep -qxF 'data: <turbo-stream action="refresh"></turbo-stream>' "$WORK/stream.out" \
  && grep -qxF 'data: <turbo-stream action="refresh"></turbo-stream>' "$WORK/stream-task.out"; then
  pass "the stream sends Turbo a refresh, its id the log's version (its inode and its line count, the one the page carries), within seconds of a state block, and of a file of the open task written with no event"
else
  fail "the stream: $paged / $version / $grown / $(cat "$WORK/stream.out") / $(cat "$WORK/stream-task.out")"
fi

# A refresh keeps what the owner types: on the phone, the words of a new task, and his line of why on a park's confirm
# step, stay in the form's field, with the focus, when the stream (or the poll while the stream is down) has Turbo morph
# the page into its new version. The pages are driven in headless Chrome (tests/board-cdp.mjs, which needs Node); the
# refresh is the one message the stream sends.
cdp_chrome=""
for c in google-chrome chromium chromium-browser "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
  if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then cdp_chrome=$c; break; fi
done
if [ -z "$cdp_chrome" ] || ! command -v node >/dev/null 2>&1; then
  skip "a refresh of the page keeps the words the owner types into the form of a new task and of a park on the phone, and the focus: no Chrome or no Node"
else
  "$PY" -c '
import json, sys
def typed(url, field, words):
    field = "document.querySelector(\"" + field + "\")"
    return [
        {"goto": url, "wait": 2500},
        {"eval": "addEventListener(\"turbo:morph\", () => { window.lemMorphed = true; }); " + field + ".focus(); "
                 "document.execCommand(\"insertText\", false, " + json.dumps(words) + ")"},
        {"eval": "Turbo.renderStreamMessage(\"<turbo-stream action=\\\"refresh\\\"></turbo-stream>\")", "after": 2500},
        {"print": "({morphed: Boolean(window.lemMorphed), words: " + field + "?.value ?? null, focused: document.activeElement?.name ?? null})"},
    ]
steps = typed(sys.argv[1], "#new-task textarea[name=words]", "Add the gift note to the CSV export") \
    + typed(sys.argv[2], "#confirm input[name=why]", "wait for the export new reader")
json.dump({"width": 390, "height": 844, "scale": 2, "mobile": True, "steps": steps}, open(sys.argv[3], "w"))
' "$BASE/new" "$BASE/tasks/gift-note-in-export/park" "$WORK/typing.json"
  mkdir -p "$WORK/chrome-tmp"
  typed=$(TMPDIR="$WORK/chrome-tmp" MAC_CHROMIUM_TMPDIR="$WORK/chrome-tmp" CHROME="$cdp_chrome" node tests/board-cdp.mjs "$WORK/typing.json" 2>&1 || true)
  if [ "$typed" = '{"morphed":true,"words":"Add the gift note to the CSV export","focused":"words"}
{"morphed":true,"words":"wait for the export new reader","focused":"why"}' ]; then
    pass "a refresh of the page keeps the words the owner types into the form of a new task and of a park on the phone, and the focus"
  else
    fail "a refresh and the words the owner types: $typed"
  fi
fi

# lem board, with a stand-in for agtermctl that prints a tree and records its calls: the board opens at the server's
# address as a page companion of the session's group, and is known by its workspace's address.
printf '%s\n' '{"result": {"tree": {"workspaces": [{"sessions": [{"id": "LEM", "foreground": ["/usr/local/bin/claude"]}, {"id": "OTHER"},' \
  '{"id": "PX", "content": "page", "parent": "LEM", "htmlOverlays": [{"url": "http://127.0.0.1:1/elsewhere/shop/", "page": "http://127.0.0.1:1/elsewhere/shop/"}]},' \
  "{\"id\": \"PA\", \"name\": \"Lem board\", \"content\": \"page\", \"parent\": \"LEM\", \"htmlOverlays\": [{\"url\": \"$BASE/\", \"page\": \"$BASE/backlog\"}]}]}]}}}" > "$WORK/tree.json"
opened() { : > "$AGT_CALLS"; env -u AGTERM_WINDOW_ID -u AGT_WINDOW_ID -u AGT_SESSION_ID -u AGT_SOCKET AGTERM_SESSION_ID="$1" AGTERM_SOCKET="$WORK/agterm.sock" "$PY" -B "$BOARD" --repo "$DEMO" "${@:2}"; }
kept=$(opened LEM)
kept_calls=$(cat "$AGT_CALLS")
fresh=$(opened OTHER --task stock-on-product-page --follow)
fresh_calls=$(cat "$AGT_CALLS")
moved=$(opened LEM --task stock-on-product-page)
moved_calls=$(cat "$AGT_CALLS")
if [ "$(field '(d["url"], d["companion"], d["reloaded"], d["name"], "removed" in d)' <<<"$kept")" = "('$BASE/', 'PA', True, 'Lem board · shop', False)" ] \
  && grep -qxF "session overlay reload --current --target PA --socket $WORK/agterm.sock" <<<"$kept_calls" && ! grep -q "PX\|overlay open\|session close" <<<"$kept_calls" \
  && [ "$(field '(d["companion"], d["parent"], d["reloaded"])' <<<"$fresh")" = "('NEW', 'OTHER', False)" ] && ! grep -qF "session close" <<<"$fresh_calls" \
  && grep -qxF "session overlay open --url $BASE/tasks/stock-on-product-page --persistent --js --companion --target OTHER --json --socket $WORK/agterm.sock" <<<"$fresh_calls" \
  && grep -qxF "session select --target NEW --socket $WORK/agterm.sock" <<<"$fresh_calls" \
  && grep -qxF "session close --target PA --socket $WORK/agterm.sock" <<<"$moved_calls" && grep -qF "overlay open --url $BASE/tasks/stock-on-product-page" <<<"$moved_calls"; then
  pass "lem board opens the server's address as a page companion: its workspace's board is reloaded where it stands, a task's board opens anew, and another repository's is left alone"
else
  fail "lem board: $kept / $kept_calls / $fresh / $fresh_calls / $moved_calls"
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
