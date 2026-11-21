#!/usr/bin/env bash
# Two machines under one address (lem_peers.py), as two board servers on this Mac: alpha, the entry, with the run's
# home folder and port (tests/lib.sh), and beta, with a home folder and a port of its own. The test's switches name
# each server's machine (LEM_SERVE_NAME) and give alpha its peers' addresses over plain http on loopback
# (LEM_SERVE_PEERS), so no check here runs the tailscale command. gamma is a port that takes a connection and never
# answers, as a machine that sleeps. The join, the list of both machines, a peer's pages, files and stream through
# alpha, the loop guard, and a machine that does not answer.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

BETA_PID=""
HOLE_PID=""
# the trap stops both servers and the silent port, then removes the folder; pid is the loop's own, set when it runs
# shellcheck disable=SC2154
trap 'stopped; for pid in $SERVE_PID $BETA_PID $HOLE_PID; do kill -TERM "$pid" 2>/dev/null; wait "$pid" 2>/dev/null || true; done; rm -rf "$WORK"' EXIT
free_port() { "$PY" -I -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()'; }
code() { curl -s -o /dev/null -w '%{http_code}' "$@" || true; }
got() { curl -fsS "$@"; }
words() { "$PY" -c 'import html, re, sys; t = sys.stdin.read(); t = re.sub(r"(?s)<(script|style|template|svg)\b.*?</\1>", " ", t); print(" ".join(html.unescape(re.sub(r"<[^>]+>", " ", t)).split()))'; }
# seconds URL: how long a GET of URL takes, in seconds
seconds() { curl -s -o /dev/null -w '%{time_total}' "$1"; }
# peer_links: the ends of the connections to beta's port that are open now; no_links: there are none
peer_links() { lsof -nP -iTCP:"$BETA_PORT" -sTCP:ESTABLISHED 2>/dev/null | grep -c -- "->127.0.0.1:" || true; }
no_links() { [ "$(peer_links)" = 0 ]; }
# lists TEXT: alpha's /api/workspaces holds TEXT now
lists() { curl -fsS "$ALPHA/api/workspaces" | grep -qF -- "$1"; }
# repo DIR TASK ASK: a repository that uses Lem, with one task whose criteria wait for the owner
repo() {
  git init -q -b main "$1" && commit "$1" init
  project --repo "$1" init --base main >/dev/null
  project --repo "$1" task-dir "$2" --ask "$3" >/dev/null
  project --repo "$1" state "$2" held "the criteria wait for the owner" >/dev/null
}

BETA_PORT=$(free_port)
HOLE_PORT=$(free_port)
BETA_HOME=$WORK/beta-config
# beta's repository is beta's: its task-dir puts it into beta's list of workspaces, never alpha's
XDG_CONFIG_HOME=$BETA_HOME repo "$WORK/beta/shop" gift-note "Print the gift note on the packing slip, on beta."
mkdir -p "$WORK/alpha/shop/.lem/state" && git init -q -b main "$WORK/alpha/shop" && commit "$WORK/alpha/shop" init
"$PY" -B "$SERVE" --add "$WORK/alpha/shop" >/dev/null
mkdir -p "$BETA_HOME/lem" && printf '[serve]\nport = %s\n' "$BETA_PORT" > "$BETA_HOME/lem/machine.toml"
XDG_CONFIG_HOME=$BETA_HOME "$PY" -B "$SERVE" --add "$WORK/beta/shop" >/dev/null
XDG_CONFIG_HOME=$BETA_HOME LEM_SERVE_NAME=beta "$PY" -B "$SERVE" > "$WORK/beta.out" 2>&1 &
BETA_PID=$!
# gamma: a socket that listens and never accepts, so a connection opens and no answer comes
"$PY" -I -c 'import socket, sys, time; s = socket.socket(); s.bind(("127.0.0.1", int(sys.argv[1]))); s.listen(8); time.sleep(600)' "$HOLE_PORT" &
HOLE_PID=$!
export LEM_SERVE_NAME=alpha LEM_SERVE_PEERS="beta=http://127.0.0.1:$BETA_PORT,gamma=http://127.0.0.1:$HOLE_PORT"
serve_up
ALPHA=http://127.0.0.1:$SERVE_PORT
BETA=http://127.0.0.1:$BETA_PORT
soon curl -fs -o /dev/null "$BETA/api/server"

# The join: it asks the machine once and says what it found; this machine's own name and a word that is no name are refused.
joined=$("$PY" -B "$SERVE" --join beta)
own=$("$PY" -B "$SERVE" --join alpha 2>&1 || true)
bad=$("$PY" -B "$SERVE" --join 'mac mini' 2>&1 || true)
listed=$(got "$ALPHA/api/workspaces")
index=$(got "$ALPHA/" | words)
if [ "$(field '(d["joined"], d["reachable"], d["workspaces"])' <<<"$joined")" = "('beta', True, ['shop'])" ] && grep -qF "this machine's own name" <<<"$own" \
  && grep -qF "no machine's name" <<<"$bad" && grep -qxF "beta = 4537" "$XDG_CONFIG_HOME/lem/machine.toml" \
  && [ "$(field '[(w["host"], w["name"], w["url"], w["waits"]) for w in d]' <<<"$listed")" = "[('alpha', 'shop', '/alpha/shop/', 0), ('beta', 'shop', '/beta/shop/', 1)]" ] \
  && grep -qF "2 repositories on 2 machines that use Lem. beta/shop" <<<"$index" && grep -qF "alpha/shop" <<<"$index"; then
  pass "--join asks the machine once and writes it into [peers], refuses this machine's own name and a word that is no name, and / and /api/workspaces list both machines' workspaces as HOST/WORKSPACE, what waits first"
else
  fail "the join and the list: $joined / $own / $bad / $listed / ${index:0:600}"
fi

# A peer's pages and files pass through alpha with the peer's text, with no agterm button, and an act on them is refused.
kanban=$(got "$ALPHA/beta/shop/")
task=$(got "$ALPHA/beta/shop/tasks/gift-note" | words)
style=$(grep -o '/beta/assets/board.css?v=[0-9a-f]*' <<<"$kanban" | head -n 1)
posted=$(curl -s -X POST -d '{}' "$ALPHA/beta/shop/agterm/type")
moved=$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' "$ALPHA/beta/shop")
if grep -qF "on beta" <<<"$task" && [ -n "$style" ] && [ "$(code "$ALPHA$style")" = 200 ] && grep -qF 'data-stream-url-value="/beta/shop/stream"' <<<"$kanban" \
  && ! grep -qF 'data-agterm-url-value' <<<"$kanban" && grep -qF 'id="ws-alpha-shop"' <<<"$kanban" && grep -qF "open beta's own board" <<<"$posted" \
  && [ "$moved" = "302 $ALPHA/beta/shop/" ]; then
  pass "a peer's kanban, task page and files come through alpha with the peer's text and assets, its switcher lists alpha's workspaces too, it has no agterm button, a redirect stays under /beta/, and an act is refused"
else
  fail "a peer's pages: ${task:0:400} / $style / $posted / $moved"
fi

# The loop guard: a request of another server is never forwarded, and its list holds this machine alone.
hop_list=$(curl -fsS -H 'Lem-Hop: 1' "$ALPHA/api/workspaces")
if [ "$(field '[w["host"] for w in d]' <<<"$hop_list")" = "['alpha']" ] && [ "$(code -H 'Lem-Hop: 1' "$ALPHA/beta/shop/")" = 404 ]; then
  pass "a request with Lem-Hop is never forwarded to a peer, and the list it gets holds this machine's workspaces alone"
else
  fail "the loop guard: $hop_list"
fi

# The stream of a peer's workspace through alpha: a refresh after an event there, and the peer's connection ends with the client's.
count=$(grep -c '' "$WORK/beta/shop/.lem/state/events.jsonl")
# one process reads the stream and stamps each line with the time it came, so that its end closes the connection
"$PY" -u -c 'import sys, time, urllib.request
reply = urllib.request.build_opener(urllib.request.ProxyHandler({})).open(sys.argv[1], timeout=20)
for line in reply:
    print(f"{time.time():.3f} {line.decode()}", end="", flush=True)' "$ALPHA/beta/shop/stream?since=$count" > "$WORK/stream.out" 2>/dev/null &
streamed=$!
soon grep -q ': open' "$WORK/stream.out"
links=$(peer_links)
written=$("$PY" -c 'import time; print(f"{time.time():.3f}")')
XDG_CONFIG_HOME=$BETA_HOME project --repo "$WORK/beta/shop" state gift-note building "a builder writes the slip" >/dev/null
soon grep -q 'turbo-stream' "$WORK/stream.out"
kill "$streamed" 2>/dev/null || true
wait "$streamed" 2>/dev/null || true
soon no_links
left=$(peer_links)
came=$(awk '/turbo-stream/ {print $1; exit}' "$WORK/stream.out")
if grep -qF "id: $((count + 1))" "$WORK/stream.out" && [ -n "$came" ] && [ "$links" -ge 1 ] && [ "$left" = 0 ]; then
  pass "a peer's stream through alpha delivers its refresh after an event there, and the peer's connection ends when the client hangs up"
  printf '     the event reached the client %.2f s after its write began\n' "$("$PY" -c 'import sys; print(float(sys.argv[1]) - float(sys.argv[2]))' "$came" "$written")"
else
  fail "a peer's stream: $(cat "$WORK/stream.out") / connections $links, then $left"
fi

# A machine that never answers is joined all the same; the list does not wait for it, and a stopped one shows its last answer.
silent=$("$PY" -B "$SERVE" --join gamma)
first=$(seconds "$ALPHA/")
soon lists '"host": "gamma"'
then_=$(seconds "$ALPHA/")
kill -TERM "$BETA_PID" && wait "$BETA_PID" 2>/dev/null || true
BETA_PID=""
soon lists '"url": "/beta/shop/", "waits": null'
dead=$(got "$ALPHA/")
after=$(seconds "$ALPHA/")
gone=$(curl -s -w ' %{http_code}' "$ALPHA/beta/shop/" | words)
if [ "$(field '(d["joined"], d["reachable"])' <<<"$silent")" = "('gamma', False)" ] && grep -qF "does not answer now" <<<"$silent" \
  && "$PY" -c 'import sys; sys.exit(not (float(sys.argv[1]) < 1.0 and float(sys.argv[2]) < 0.3 and float(sys.argv[3]) < 0.3))' "$first" "$then_" "$after" \
  && grep -qF 'id="space-beta-shop"' <<<"$dead" && grep -qF "last answer" <<<"$(words <<<"$dead")" && grep -qF 'id="space-gamma-machine"' <<<"$dead" \
  && grep -qF "beta is not reachable" <<<"$gone" && grep -qF " 502" <<<"$gone"; then
  pass "a machine that never answers is joined all the same and the list waits for it at most once, and a stopped one shows as not reachable with its last answer and its pages say so"
  printf '     the index with a silent peer: %s s at its first look, %s s after; with a stopped one: %s s\n' "$first" "$then_" "$after"
else
  fail "a machine that does not answer: $silent / $first $then_ $after / ${gone:0:300} / $(words <<<"$dead" | head -c 600)"
fi

finish
