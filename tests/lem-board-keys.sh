#!/usr/bin/env bash
# The board's keys over its cards and rows, pressed in headless Chrome (tests/board-cdp.mjs, which needs Node) on the
# afternoon of tests/board-showcase.py, served as tests/lem-serve.sh serves it: a server of this run on its own port and
# home folder (tests/lib.sh), with the stand-in for agtermctl of lem-serve.sh first on its PATH. The Tasks view's mark
# (cursor.js): J, K and the arrows in a column, H, L and the arrows to the next column you can see, Enter and Escape,
# the mark through a morph, and no key in a field or with a modifier. The mark of "Waits for you": J, K and the arrows
# over its rows, Enter on a row answered in the task's session (the stand-in's `session select`) and on a merge row (the
# panel, no button, inside its task's stack), and the mark through a morph. The stack of a task with two things, which a
# click or a tap opens and closes, on a wide screen and at a phone's width. The search over every card (search.js): Cmd-K and Ctrl-K, also from a
# field, and the search buttons open it, letters typed filter and order it, Enter, a click and Escape, and the box through
# a morph. The confirm step of a merge, a park and an approval: on a phone an overlay whose button comes on when its
# text was read to the end, on a desktop and with no script as before; and the Drop of a breaker's row, which opens its
# confirm step as that overlay. Each kind of lem-ask card through the board's card route on a phone, the Tune card's
# values, and a card answered on a phone from its row. The arrow that folds the sidebar, in a wide window and in the
# drawer of a narrow one. The start of a task from a backlog item, which
# ends on the new task's page while the stream refreshes the backlog. The line of keys of each view at the window's
# foot, with a backlog longer than the window. A check adds to the demo's log only the state
# lines it needs, as a lead's `lem project state` and `lem session open` write them. Each check that needs Chrome
# prints a SKIP line of its own where Node or Chrome is missing.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

# A stand-in for agtermctl, first on the PATH of this block and of its server: it prints the tree of AGT_TREE, says of a
# card's page that no answer waits at the Mac, and records each call in AGT_CALLS.
FAKE=$WORK/fake
mkdir -p "$FAKE"
cat > "$FAKE/agtermctl" <<'SH'
#!/bin/sh
echo "$*" >> "$AGT_CALLS"
case "$1 $2 $3" in
  tree*) cat "$AGT_TREE" ;;
  "session overlay open") echo "{\"result\": {\"id\": \"NEW\"}}" ;;
  "session overlay result") echo "{\"ok\": true, \"result\": {\"pageOutcome\": {}}}" ;;
esac
exit 0
SH
chmod +x "$FAKE/agtermctl"
export PATH="$FAKE:$PATH" AGT_CALLS="$WORK/calls" AGT_TREE="$WORK/tree.json"
DEMO=$("$PY" -B tests/board-showcase.py --demo "$WORK/demo" | field 'd["repo"]')
LOG=$DEMO/.lem/state/events.jsonl

# A stand-in for `lem session` behind the server (LEM_SESSION_SCRIPT), for the start from a backlog item: `open SLUG
# --why new` logs the session.open of SLUG as session.py does, takes 2 s as agterm's calls of a real open may (an
# unmeasured estimate), records the call in START_CALLS and prints what session.py prints. Every other command is
# session.py's own, so the other checks of this block meet the real one.
cat > "$WORK/session-standin.py" <<'PY'
import json, os, sys, time
from datetime import datetime, timezone
args = sys.argv[1:]
verb = args[2:3]
if verb != ["open"] or args[4:6] != ["--why", "new"]:
    os.execv(sys.executable, [sys.executable, "-B", os.environ["REAL_SESSION"], *args])
slug = args[3]
with open(os.environ["START_LOG"], "a", encoding="utf-8") as out:
    out.write(json.dumps({"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": "session.open", "task": slug, "session": "S-START",
                          "name": slug, "phase": "shape", "why": "new", "workspace": "demo"}) + "\n")
time.sleep(2)
with open(os.environ["START_CALLS"], "a", encoding="utf-8") as calls:
    calls.write(" ".join(args[2:]) + "\n")
print(json.dumps({"task": slug, "session": "S-START", "name": slug, "phase": "shape", "already": False, "say": f"{slug}: a session opened"}))
PY
export LEM_SESSION_SCRIPT=$WORK/session-standin.py REAL_SESSION=$PWD/skills/lem/scripts/session.py START_LOG=$LOG START_CALLS=$WORK/start-calls
"$PY" -B "$SERVE" --add "$DEMO" >/dev/null
serve_up
SERVER=http://127.0.0.1:$SERVE_PORT
HOST=$(curl -fsS "$SERVER/api/server" | field 'd["host"]')
BASE=$SERVER/$HOST/shop
got() { curl -fsS "$@"; }
# words: the text of an HTML page on stdin, its tags taken out
words() { "$PY" -c 'import html, re, sys; t = sys.stdin.read(); t = re.sub(r"(?s)<(script|style|template|svg)\b.*?</\1>", " ", t); print(" ".join(html.unescape(re.sub(r"<[^>]+>", " ", t)).split()))'; }

# event.py LOG TASK STATUS TEXT: a state line of TASK, written now at the end of the demo's log
cat > "$WORK/event.py" <<'PY'
import json, sys, time
from datetime import datetime, timezone
log, task, status, text = sys.argv[1:]
with open(log, "a", encoding="utf-8") as out:
    out.write(json.dumps({"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": "task.state", "task": task, "status": status,
                          "text": text, "lines": [], "ask": text}) + "\n")
PY

# entries.py: the entries of "Waits for you" in the page on stdin, as JSON: `shown`, the ids of the rows and stacks you
# see while every stack is closed, in their order, and `stacks`, the ids of each stack's rows
cat > "$WORK/entries.py" <<'PY'
import json, re, sys
shown, stacks, inside = [], {}, None
for tag, name in re.findall(r'<(article class="wrow[^"]*"|details class="wstack[^"]*"|/details)(?: id="([^"]+)")?', sys.stdin.read()):
    if tag == "/details":
        inside = None
    elif tag.startswith("details"):
        shown.append(name)
        inside = stacks[name] = []
    else:
        (shown if inside is None else inside).append(name)
print(json.dumps({"shown": shown, "stacks": stacks}))
PY

# held.py LOG TASK SESSION ASK: a task the owner asked for, its session opened and its interview waiting for him, written
# now at the end of the demo's log
cat > "$WORK/held.py" <<'PY'
import json, sys, time
from datetime import datetime, timezone
log, task, session, ask = sys.argv[1:]
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
with open(log, "a", encoding="utf-8") as out:
    out.write(json.dumps({"ts": now, "event": "session.open", "task": task, "session": session, "name": task, "phase": "shape", "why": "new", "workspace": "demo"}) + "\n")
    out.write(json.dumps({"ts": now, "event": "task.state", "task": task, "status": "held", "text": "the interview waits for the owner", "lines": [], "ask": ask}) + "\n")
PY

TASKS_KEYS="J K ↑ ↓ move · H L ← → column · Enter open · Esc close"
WAITS_KEYS="J K ↑ ↓ move · Enter go or open"
kanban=$(got "$BASE/")
if words <<<"$kanban" | grep -qF "$TASKS_KEYS" && grep -qF '<div class="keys" id="kanban-keys">' <<<"$kanban" \
  && grep -qF 'data-controller="cursor"' <<<"$kanban"; then
  pass "the Tasks view says its keys in one line of the Backlog's look: $TASKS_KEYS"
else
  fail "the Tasks view's line of keys: $(words <<<"$kanban" | grep -oE '.{0,40}move.{0,80}' || true)"
fi
waits=$(got "$BASE/waits")
if words <<<"$waits" | grep -qF "$WAITS_KEYS" && grep -qF '<div class="keys" id="waits-keys">' <<<"$waits" \
  && grep -qF 'id="waits-list" data-controller="cursor"' <<<"$waits"; then
  pass "Waits for you says its keys in one line of the Backlog's look: $WAITS_KEYS"
else
  fail "the line of keys of Waits for you: $(words <<<"$waits" | grep -oE '.{0,40}move.{0,80}' || true)"
fi

# ---- in Chrome ----
NODE=$(command -v node || true)
CHROME_AT=${CHROME:-}
if [ -z "$CHROME_AT" ]; then
  for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" google-chrome chromium; do
    if [ -x "$c" ] || command -v "$c" >/dev/null 2>&1; then CHROME_AT=$c; break; fi
  done
fi
# drive SPEC OUT: Chrome through the spec, what it printed into OUT
drive() { node tests/board-cdp.mjs "$1" > "$2" 2>&1 || true; }
# seen OUT LABEL: what the spec printed under LABEL, its print steps being [LABEL, VALUE]
seen() {
  "$PY" -c 'import json, sys
for line in open(sys.argv[1], encoding="utf-8"):
    try:
        got = json.loads(line)
    except ValueError:
        continue
    if isinstance(got, list) and got and got[0] == sys.argv[2]:
        print(got[1])
        break
else:
    print("nothing printed")' "$1" "$2"
}
# fact OUT LABEL EXPR: EXPR over the facts the spec printed under LABEL (d), "nothing printed" when it printed none
fact() { seen "$1" "$2" | "$PY" -c 'import ast, json, sys; t = sys.stdin.read().strip()
try:
    d = ast.literal_eval(t)
except (ValueError, SyntaxError):
    print("nothing printed"); sys.exit()
print(eval(sys.argv[1], {"d": d}))' "$3"; }

# The spec of the Tasks view: each print step gives a label and the state, "MARK FOCUS PANEL": the task of the card
# with the mark, of the card whose link has the focus, and of the open panel, each "-" for none.
"$PY" - "$BASE" "$WORK" "$PY" "$LOG" > "$WORK/tasks.json" <<'PY'
import json, shlex, sys
base, work, py, log = sys.argv[1:]
STATE = ("(() => { const cur = document.querySelector('[data-js-cur]'); const focus = document.activeElement?.closest('article.tc');"
         " const panel = document.querySelector('#task > .panel');"
         " return [cur ? cur.dataset.task : '-', focus ? focus.dataset.task : '-', panel ? panel.dataset.task : '-'].join(' '); })()")
# A wait for what the board's stream brings after a step of the check wrote it has no limit of its own (None):
# under the load of tests/all.sh the stream brought a proposal after the 15 s of the other waits (2026-11-23)
def until(label, cond, limit=15000):
    """a print step that waits up to LIMIT ms for COND, then gives LABEL and the state; with LIMIT None it has no
    limit of its own, so only the suite's time limit (LEM_TEST_LIMIT) ends a wait for a COND that never comes"""
    end = "Infinity" if limit is None else f"Date.now() + {limit}"
    return {"print": f"new Promise(done => {{ const end = {end}; const tick = () => (({cond}) || Date.now() > end) ? done([{json.dumps(label)}, {STATE}]) : setTimeout(tick, 100); tick(); }})"}
def at(label):
    return {"print": f"[{json.dumps(label)}, {STATE}]"}
def go(url):
    return [{"goto": url, "wait": 300}, until("ready", "document.readyState === 'complete' && window.Turbo && document.querySelector('#kanban')"), {"wait": 300}]
def key(name, code=None, **more):
    vk = {"Enter": 13, "Escape": 27}.get(name, 0)
    # a key's handler has run when the driver's call returns: what the page then loads, a print step waits for
    return {"key": name, "code": code or name, "vk": vk, "after": 100, **({"text": "\r"} if name == "Enter" else {}), **more}
J, K, H, L = key("j", "KeyJ"), key("k", "KeyK"), key("h", "KeyH"), key("l", "KeyL")
def event(task, status, text):
    return {"sh": " ".join(map(shlex.quote, [py, f"{work}/event.py", log, task, status, text]))}
fold = {"eval": "document.querySelector('#col-checks .col-head button').click()"}
steps = [
    # J, K and the arrows in a column; the line of keys on a wide screen
    *go(f"{base}/"), at("none"), J, at("j1"), J, at("j2"), K, at("k1"), key("ArrowDown"), at("down"), key("ArrowUp"), at("up"),
    {"print": "['line', (() => { const n = document.getElementById('kanban-keys'); return n && n.getClientRects().length ? n.textContent.replace(/\\s+/g, ' ').trim() : 'hidden'; })()]"},
    # H and L over a folded column, to the card at the height of the marked one
    *go(f"{base}/"), J, L, J, at("from"), fold, {"wait": 300}, L, at("l-fold"), H, at("h-fold"), key("ArrowRight"), at("right-fold"), key("ArrowLeft"), at("left-fold"), fold,
    # Enter and Escape, by the focused link, with the focus on no link, and after a click
    *go(f"{base}/"), J, J, key("Enter"), until("enter", "document.querySelector('#task > .panel')"), key("Escape"), until("escape", "!document.querySelector('#task > .panel')"),
    {"eval": "document.activeElement.blur()"}, key("Enter"), until("enter-blur", "document.querySelector('#task > .panel')"), key("Escape"), until("escape-blur", "!document.querySelector('#task > .panel')"),
    {"click": "#card-refund-rounding .tc-link"}, until("click", "document.querySelector('#task > .panel')"), key("Escape"), until("escape-click", "!document.querySelector('#task > .panel')"),
    # in the open panel the arrows are the panel's, and J moves the mark; Enter then opens the card J marked
    key("Enter"), until("panel", "document.querySelector('#task > .panel')"), key("ArrowDown"), at("panel-down"), J, at("panel-j"),
    key("Enter"), until("panel-enter", "document.querySelector('#task > .panel')?.dataset.task === 'cart-total-after-coupon'"), key("Escape"), until("panel-escape", "!document.querySelector('#task > .panel')"),
    # J in the open panel, then Escape: the focus goes to the card J marked, and Enter opens that card
    *go(f"{base}/"), J, key("Enter"), until("split-open", "document.querySelector('#task > .panel')"), J, at("split-j"),
    key("Escape"), until("split-escape", "!document.querySelector('#task > .panel')"),
    key("Enter"), until("split-enter", "document.querySelector('#task > .panel')?.dataset.task === 'stock-on-product-page'"), key("Escape"), until("split-close", "!document.querySelector('#task > .panel')"),
    # a click on a task's row in the sidebar moves the mark to its card, and Escape leaves the focus there
    {"click": ".wi[data-task='cart-total-after-coupon']"}, until("side", "document.querySelector('#task > .panel')?.dataset.task === 'cart-total-after-coupon'"),
    key("Escape"), until("side-escape", "!document.querySelector('#task > .panel')"),
    key("Enter"), until("side-enter", "document.querySelector('#task > .panel')?.dataset.task === 'cart-total-after-coupon'"), key("Escape"), until("side-close", "!document.querySelector('#task > .panel')"),
    # no key in a field (the park's line of why, a panel over the Tasks view) or with Cmd, Ctrl or Alt
    *go(f"{base}/tasks/gift-note-in-export/park"), J, at("field-before"), {"eval": "document.querySelector('#confirm input[name=why]').focus()"},
    key("j", "KeyJ", text="j"), {"print": "['field', document.querySelector('#confirm input[name=why]').value + ' ' + (document.querySelector('[data-js-cur]')?.dataset.task ?? '-')]"},
    {"eval": "document.activeElement.blur()"}, key("j", "KeyJ", modifiers=4), at("cmd"), key("j", "KeyJ", modifiers=2), at("ctrl"), key("j", "KeyJ", modifiers=1), at("alt"),
    key("ArrowDown", modifiers=2), at("ctrl-down"), J, at("plain"),
    # H and L over an empty column: the one task in its checks lands
    *go(f"{base}/"), event("coupon-has-a-slug", "landed", "main: the change is merged"), until("emptied", "!document.querySelector('#col-checks article.tc')", None),
    J, L, J, at("from-empty"),
    {"print": "['nearest', (() => { const mid = n => { const b = n.getBoundingClientRect(); return b.top + b.height / 2; }; const at = mid(document.querySelector('[data-js-cur]'));"
              " return [...document.querySelectorAll('#col-done article.tc')].sort((a, b) => Math.abs(mid(a) - at) - Math.abs(mid(b) - at))[0].dataset.task; })()]"},
    L, at("l-empty"), H, at("h-empty"),
    # the mark through a morph: a new card comes into its column, then the marked card moves to another column
    event("keys-new-task", "building", "task 1 of 2"), until("new-card", "document.querySelector('#col-build #card-keys-new-task')", None),
    event("cart-total-after-coupon", "landing", "the checks start"), until("moved", "document.querySelector('#col-checks #card-cart-total-after-coupon')", None),
    J, at("after-move"),
    # every column folded: no card to mark, and the down arrow stays the browser's (it scrolls)
    {"eval": "document.querySelectorAll('#kanban section.col:not(.folded) .col-head button').forEach(b => b.click())"}, {"wait": 300},
    {"eval": "window.lemKeys = []; window.addEventListener('keydown', ev => window.lemKeys.push(ev.defaultPrevented))"},
    key("ArrowDown"), {"print": "['no-card', [[...document.querySelectorAll('#kanban article.tc')].filter(n => n.getClientRects().length).length, ...window.lemKeys].join(' ')]"},
]
print(json.dumps({"width": 1440, "height": 900, "steps": steps}))
PY
printf '%s\n' '{"width": 390, "height": 844, "mobile": true, "steps": [' \
  "{\"goto\": \"$BASE/\", \"wait\": 2500}," \
  "{\"print\": \"['phone', (() => { const n = document.getElementById('kanban-keys'); return n ? (n.getClientRects().length ? 'shown' : 'hidden') : 'none'; })()]\"}" \
  ']}' > "$WORK/phone.json"

tasks_view_checks() {
  local out=$WORK/tasks.out near
  drive "$WORK/tasks.json" "$out"
  drive "$WORK/phone.json" "$WORK/phone.out"
  if [ "$(seen "$out" ready)" != "nothing printed" ] && [ "$(seen "$out" none)" = "- - -" ] \
    && [ "$(seen "$out" j1)" = "gift-note-in-export gift-note-in-export -" ] && [ "$(seen "$out" j2)" = "stock-on-product-page stock-on-product-page -" ] \
    && [ "$(seen "$out" k1)" = "gift-note-in-export gift-note-in-export -" ] && [ "$(seen "$out" down)" = "stock-on-product-page stock-on-product-page -" ] \
    && [ "$(seen "$out" up)" = "gift-note-in-export gift-note-in-export -" ]; then
    pass "with no mark J marks the first card of the first column, J and the down arrow move it to the next card of its column, K and the up arrow to the one before, and the focus goes with it"
  else
    fail "J, K and the arrows in a column: $(cat "$out")"
  fi
  if [ "$(seen "$out" from)" = "cart-total-after-coupon cart-total-after-coupon -" ] && [ "$(seen "$out" l-fold)" = "order-date-on-invoice order-date-on-invoice -" ] \
    && [ "$(seen "$out" h-fold)" = "cart-total-after-coupon cart-total-after-coupon -" ] && [ "$(seen "$out" right-fold)" = "order-date-on-invoice order-date-on-invoice -" ] \
    && [ "$(seen "$out" left-fold)" = "cart-total-after-coupon cart-total-after-coupon -" ]; then
    pass "from the second card of Building, L and the right arrow pass over the folded column to the second card of Done, at its height, and H and the left arrow come back"
  else
    fail "H, L and the arrows over a folded column: $(cat "$out")"
  fi
  near=$(seen "$out" nearest)
  if [ "$(seen "$out" from-empty)" = "cart-total-after-coupon cart-total-after-coupon -" ] && [ "$near" != "nothing printed" ] && [ "$(seen "$out" l-empty)" = "$near $near -" ] \
    && [ "$(seen "$out" h-empty)" = "cart-total-after-coupon cart-total-after-coupon -" ]; then
    pass "L and H pass over a column with no card, to the card of Done at the height of the marked one"
  else
    fail "H and L over an empty column: $(cat "$out")"
  fi
  if [ "$(seen "$out" enter)" = "stock-on-product-page - stock-on-product-page" ] && [ "$(seen "$out" escape)" = "stock-on-product-page stock-on-product-page -" ] \
    && [ "$(seen "$out" enter-blur)" = "stock-on-product-page - stock-on-product-page" ] && [ "$(seen "$out" escape-blur)" = "stock-on-product-page stock-on-product-page -" ] \
    && [ "$(seen "$out" click)" = "refund-rounding - refund-rounding" ] && [ "$(seen "$out" escape-click)" = "refund-rounding refund-rounding -" ]; then
    pass "Enter opens the panel of the marked card, by its focused link or with the focus on no link, a click on a card moves the mark there, and Escape closes the panel with the mark and the focus on that card"
  else
    fail "Enter and Escape: $(cat "$out")"
  fi
  if [ "$(seen "$out" panel)" = "refund-rounding - refund-rounding" ] && [ "$(seen "$out" panel-down)" = "refund-rounding - refund-rounding" ] \
    && [ "$(seen "$out" panel-j)" = "cart-total-after-coupon cart-total-after-coupon refund-rounding" ] \
    && [ "$(seen "$out" panel-enter)" = "cart-total-after-coupon - cart-total-after-coupon" ] && [ "$(seen "$out" panel-escape)" = "cart-total-after-coupon cart-total-after-coupon -" ]; then
    pass "with the focus in the open panel the down arrow moves no mark, J moves it to the next card, and Enter then opens that card's panel"
  else
    fail "the keys with the panel open: $(cat "$out")"
  fi
  if [ "$(seen "$out" split-open)" = "gift-note-in-export - gift-note-in-export" ] && [ "$(seen "$out" split-j)" = "stock-on-product-page stock-on-product-page gift-note-in-export" ] \
    && [ "$(seen "$out" split-escape)" = "stock-on-product-page stock-on-product-page -" ] && [ "$(seen "$out" split-enter)" = "stock-on-product-page - stock-on-product-page" ] \
    && [ "$(seen "$out" side)" = "cart-total-after-coupon - cart-total-after-coupon" ] && [ "$(seen "$out" side-escape)" = "cart-total-after-coupon cart-total-after-coupon -" ] \
    && [ "$(seen "$out" side-enter)" = "cart-total-after-coupon - cart-total-after-coupon" ]; then
    pass "after J in the open panel, or a click on a task's row in the sidebar, Escape puts the focus on the marked card, and Enter opens that card"
  else
    fail "the mark and the focus after Escape: $(cat "$out")"
  fi
  if [ "$(seen "$out" no-card)" = "0 false" ]; then
    pass "with every column folded no key marks a card, and the down arrow stays the browser's"
  else
    fail "the arrows with no card to mark (cards shown, then whether the down arrow was cancelled): $(seen "$out" no-card)"
  fi
  if [ "$(seen "$out" field-before)" = "gift-note-in-export gift-note-in-export gift-note-in-export" ] && [ "$(seen "$out" field)" = "j gift-note-in-export" ] \
    && [ "$(seen "$out" cmd)" = "gift-note-in-export - gift-note-in-export" ] && [ "$(seen "$out" ctrl)" = "gift-note-in-export - gift-note-in-export" ] \
    && [ "$(seen "$out" alt)" = "gift-note-in-export - gift-note-in-export" ] && [ "$(seen "$out" ctrl-down)" = "gift-note-in-export - gift-note-in-export" ] \
    && [ "$(seen "$out" plain)" = "stock-on-product-page stock-on-product-page gift-note-in-export" ]; then
    pass "J in a text field over the Tasks view types j and moves no mark, and J or an arrow with Cmd, Ctrl or Alt held moves none"
  else
    fail "the keys in a field and with a modifier: $(cat "$out")"
  fi
  if [ "$(seen "$out" emptied)" != "nothing printed" ] && [ "$(seen "$out" new-card)" = "cart-total-after-coupon cart-total-after-coupon -" ] \
    && [ "$(seen "$out" moved)" = "- - -" ] && [ "$(seen "$out" after-move)" = "gift-note-in-export gift-note-in-export -" ]; then
    pass "the mark stays on its card when a new task's card comes into its column, goes when its card moves to another column, and the next key marks the first card"
  else
    fail "the mark through a morph: $(cat "$out")"
  fi
  if [ "$(seen "$out" line)" = "$TASKS_KEYS" ] && [ "$(seen "$WORK/phone.out" phone)" = hidden ]; then
    pass "the Tasks view's line of keys shows under the columns, at the window's foot, on a wide screen and is hidden on a phone"
  else
    fail "the line of keys in Chrome: $(seen "$out" line) / $(cat "$WORK/phone.out")"
  fi
}

# The checks of "Waits for you", after the Tasks view's: a task whose interview waits for the owner, with its session
# open (a demo marks a session live from the log alone), is added first. Each print step gives a label and the state,
# "MARK FOCUS PANEL": the id of the row or stack with the mark, of the row or stack whose link or summary has the focus,
# and the task of the open panel, each "-" for none; a `calls-*` step gives the stand-in agtermctl's calls so far,
# joined by "|". The merge row of the afternoon is inside the stack of its task, which a click opens first.
waits_view_checks() {
  local out=$WORK/waits.out held=order-search session=0F5EA2C1-0000-4000-8000-0000000000C1 entries first merge select
  "$PY" "$WORK/held.py" "$LOG" "$held" "$session" "Search the orders by customer name"
  entries=$(got "$BASE/waits" | "$PY" "$WORK/entries.py")
  : > "$AGT_CALLS"
  "$PY" - "$BASE" "$WORK" "$PY" "$LOG" "$AGT_CALLS" "$held" "$entries" > "$WORK/waits.json" <<'PY'
import json, shlex, sys
base, work, py, log, calls, held, entries = sys.argv[1:]
entries = json.loads(entries)
rows = entries["shown"]
mine = f"wait-held-{held}"
merge = next((r for ids in [rows, *entries["stacks"].values()] for r in ids if r.startswith("wait-merge-")), "")
# the stack the merge row is in, and the entries you see once it is open
stack = next((s for s, ids in entries["stacks"].items() if merge in ids), "")
opened = [r for e in rows for r in ([e, *entries["stacks"][e]] if e == stack else [e])]
STATE = ("(() => { const cur = document.querySelector('#waits-list [data-js-cur]'); const focus = document.activeElement?.closest('article.wrow, details.wstack');"
         " const panel = document.querySelector('#task > .panel');"
         " return [cur ? cur.id : '-', focus ? focus.id : '-', panel ? panel.dataset.task : '-'].join(' '); })()")
# A wait for what the board's stream brings after a step of the check wrote it has no limit of its own (None):
# under the load of tests/all.sh the stream brought a proposal after the 15 s of the other waits (2026-11-23)
def until(label, cond, limit=15000):
    """a print step that waits up to LIMIT ms for COND, then gives LABEL and the state; with LIMIT None it has no
    limit of its own, so only the suite's time limit (LEM_TEST_LIMIT) ends a wait for a COND that never comes"""
    end = "Infinity" if limit is None else f"Date.now() + {limit}"
    return {"print": f"new Promise(done => {{ const end = {end}; const tick = () => (({cond}) || Date.now() > end) ? done([{json.dumps(label)}, {STATE}]) : setTimeout(tick, 100); tick(); }})"}
def at(label):
    return {"print": f"[{json.dumps(label)}, {STATE}]"}
def where(label):
    return {"print": f"[{json.dumps(label)}, location.pathname + ' ' + (document.querySelector('#confirm') ? 'confirm' : 'no-confirm')]"}
def key(name, code=None):
    vk = {"Enter": 13, "Escape": 27}.get(name, 0)
    return {"key": name, "code": code or name, "vk": vk, "after": 100, **({"text": "\r"} if name == "Enter" else {})}
J, K = key("j", "KeyJ"), key("k", "KeyK")
def moves(src, dst, over=rows):
    """the J or K presses that take the mark from entry SRC to entry DST, over the entries OVER you see"""
    a, b = over.index(src), over.index(dst)
    return [J] * (b - a) if b > a else [K] * (a - b)
def sh(*argv):
    return {"sh": " ".join(map(shlex.quote, argv))}
def seen_calls(label):
    # the stand-in's calls, a second after the press: the jump posts to the server, which runs agtermctl
    return [{"wait": 1000}, sh(py, "-c", "import json, sys; print(json.dumps([sys.argv[1], '|'.join(open(sys.argv[2]).read().split(chr(10))).strip('|')]))", label, calls)]
gone = "!document.querySelector('#task > .panel')"
steps = [
    {"goto": f"{base}/waits", "wait": 300},
    until("ready", f"document.readyState === 'complete' && window.Turbo && document.querySelector('#{mine}')"), {"wait": 300},
    # J, K and the arrows over the rows; the line of keys
    at("none"), J, at("j1"), J, at("j2"), K, at("k1"), key("ArrowDown"), at("down"), key("ArrowUp"), at("up"),
    {"print": "['line', (() => { const n = document.getElementById('waits-keys'); return n && n.getClientRects().length ? n.textContent.replace(/\\s+/g, ' ').trim() : 'hidden'; })()]"},
    # Enter on the row whose interview waits: by its focused verb, with the focus on no link, then a click on the verb
    *moves(rows[0], mine), at("at-held"), key("Enter"), *seen_calls("calls-enter"), at("after-enter"), where("where-enter"),
    {"eval": "document.activeElement.blur()"}, key("Enter"), *seen_calls("calls-blur"), at("after-blur"),
    {"click": f"#{mine} .wr-verb"}, *seen_calls("calls-click"), at("after-click"), where("where-click"),
    # Enter on a merge row opens the task's panel, and no button of the row is pressed; Escape gives the focus back to it.
    # A merge row in a stack: a click on the stack's summary opens it and marks it, and J goes on into its rows
    *((moves(mine, stack) + [{"click": f"#{stack} > summary", "after": 300}, *moves(stack, merge, opened)]) if stack else moves(mine, merge) if merge else []),
    at("at-merge"), key("Enter"), until("merge-enter", "document.querySelector('#task > .panel')"), where("where-merge"),
    key("Escape"), until("merge-escape", gone), *seen_calls("calls-merge"),
    # the mark through a morph: a new row comes, then the marked row leaves
    *(moves(merge, mine, opened if stack else rows) if merge else []), at("pre-morph"),
    sh(py, f"{work}/event.py", log, "keys-other-wait", "held", "the interview waits for the owner"), until("new-row", "document.querySelector('#wait-held-keys-other-wait')", None),
    sh(py, f"{work}/event.py", log, held, "building", "task 1 of 2"), until("row-gone", f"!document.querySelector('#{mine}')", None),
    J, at("after-gone"), {"print": "['first', document.querySelector('#waits-list article.wrow')?.id ?? '-']"},
]
print(json.dumps({"width": 1440, "height": 900, "steps": steps}))
PY
  drive "$WORK/waits.json" "$out"
  first=$(field 'd["shown"][0]' <<<"$entries")
  merge=$(field 'next((r for ids in [d["shown"], *d["stacks"].values()] for r in ids if r.startswith("wait-merge-")), "")' <<<"$entries")
  mine=wait-held-$held
  if [ "$(seen "$out" ready)" != "nothing printed" ] && [ -n "$first" ] && [ "$(seen "$out" none)" = "- - -" ] \
    && [ "$(seen "$out" j1)" = "$first $first -" ] && [ "$(seen "$out" k1)" = "$first $first -" ] && [ "$(seen "$out" up)" = "$first $first -" ] \
    && [ "$(seen "$out" j2)" != "$first $first -" ] && [ "$(seen "$out" j2)" = "$(seen "$out" down)" ] && [ "$(seen "$out" line)" = "$WAITS_KEYS" ]; then
    pass "on Waits for you, with no mark J marks the first row, J and the down arrow move it to the next row, K and the up arrow to the one before, the focus goes with it, and the line of keys shows"
  else
    fail "J, K and the arrows over the rows: $(cat "$out")"
  fi
  select="session select --target $session"
  if [ "$(seen "$out" at-held)" = "$mine $mine -" ] && [ "$(seen "$out" calls-enter)" = "$select" ] && [ "$(seen "$out" after-enter)" = "$mine $mine -" ] \
    && [ "$(seen "$out" calls-blur)" = "$select|$select" ] && [ "$(seen "$out" after-blur)" = "$mine - -" ] \
    && [ "$(seen "$out" calls-click)" = "$select|$select|$select" ] && [ "$(seen "$out" after-click)" = "$mine $mine -" ] \
    && [ "$(seen "$out" where-enter)" = "/$HOST/shop/waits no-confirm" ] && [ "$(seen "$out" where-click)" = "/$HOST/shop/waits no-confirm" ]; then
    pass "Enter on the marked row whose interview waits, by its focused verb or with the focus on no link, and a click on its verb each switch agterm to the task's session and open no panel"
  else
    fail "Enter on a row answered in the session: $(cat "$out") / calls: $(cat "$AGT_CALLS")"
  fi
  if [ -n "$merge" ] && [ "$(seen "$out" at-merge)" = "$merge $merge -" ] && [ "$(seen "$out" merge-enter)" = "$merge - ${merge#wait-merge-}" ] \
    && [ "$(seen "$out" where-merge)" = "/$HOST/shop/tasks/${merge#wait-merge-} no-confirm" ] && [ "$(seen "$out" merge-escape)" = "$merge $merge -" ] \
    && [ "$(seen "$out" calls-merge)" = "$select|$select|$select" ]; then
    pass "Enter on a marked merge row, in its task's stack that a click opened, opens the task's panel and presses none of the row's buttons, and Escape gives the focus back to the marked row"
  else
    fail "Enter on a merge row ($merge): $(cat "$out")"
  fi
  if [ "$(seen "$out" pre-morph)" = "$mine $mine -" ] && [ "$(seen "$out" new-row)" = "$mine $mine -" ] && [ "$(seen "$out" row-gone)" = "- - -" ] \
    && [ "$(seen "$out" first)" != "-" ] && [ "$(seen "$out" after-gone)" = "$(seen "$out" first) $(seen "$out" first) -" ]; then
    pass "the mark stays on its row when a new row comes into Waits for you, goes when its row leaves, and the next key marks the first row"
  else
    fail "the mark of a row through a morph: $(cat "$out")"
  fi
}

# The stack of a task with two or more things that wait for the owner (criterion 2 of
# docs/plans/2026-11-23-one-row-for-a-merge-call.md): refund-line-on-receipt, whose merge review calls the owner and whose
# merge waits for him, is one stack, closed as the page comes. A click on its summary opens it, with each thing its own row,
# its own time and its own button, the Merge button on the merge row; a second click closes it. On a wide screen with a
# mouse, and at a phone's width with a finger. Each print step gives a label and the stack's facts: whether it is open,
# the rows of it you see, the top line of each (its verb and its time), the buttons you see on its merge row, and its
# summary's words.
stack_checks() {
  local out=$WORK/stack
  "$PY" - "$BASE" "$WORK" <<'PY'
import json, sys
base, work = sys.argv[1:]
FACTS = ("(() => { const s = document.querySelector('#wait-stack-refund-line-on-receipt'); if (!s) return 'no stack';"
         " const seen = n => n.getClientRects().length > 0, words = n => n.innerText.replace(/\\s+/g, ' ').trim();"
         " const rows = [...s.querySelectorAll('article.wrow')].filter(seen);"
         " return {open: s.open, rows: rows.map(n => n.id), tops: rows.map(n => words(n.querySelector('.wr-top'))),"
         " merge: [...s.querySelectorAll('#wait-merge-refund-line-on-receipt .wr-acts .btn')].filter(seen).map(words),"
         " head: words(s.querySelector('summary'))}; })()")
def at(label):
    return {"print": f"[{json.dumps(label)}, {FACTS}]"}
for name, size, tap in (("wide", {"width": 1440, "height": 900}, False), ("phone", {"width": 390, "height": 844, "mobile": True}, True)):
    click = {"click": "#wait-stack-refund-line-on-receipt > summary", "after": 500, **({"tap": True} if tap else {})}
    steps = [{"goto": f"{base}/waits", "wait": 300},
             {"print": "new Promise(done => { const end = Date.now() + 15000; const tick = () => (document.readyState === 'complete' && window.Turbo"
                       " && document.querySelector('#wait-stack-refund-line-on-receipt')) || Date.now() > end ? done(['ready', 'yes']) : setTimeout(tick, 100); tick(); })"},
             {"wait": 300}, at("closed"), click, at("opened"), click, at("closed-again")]
    with open(f"{work}/stack-{name}.json", "w", encoding="utf-8") as spec:
        json.dump({**size, "steps": steps}, spec)
PY
  drive "$WORK/stack-wide.json" "$out-wide.out"
  drive "$WORK/stack-phone.json" "$out-phone.out"
  if stack_ok "$out-wide.out"; then
    pass "on a wide screen the stack of refund-line-on-receipt comes closed with its title, its first thing and 2 things; a click opens it on its two rows, each with its verb and its time and the Merge button on the merge row, and a second click closes it"
  else
    fail "the stack on a wide screen: $(cat "$out-wide.out")"
  fi
  if stack_ok "$out-phone.out"; then
    pass "at a phone's width a tap opens the stack of refund-line-on-receipt on its two rows, each with its time and the Merge button on the merge row, and a second tap closes it"
  else
    fail "the stack at a phone's width: $(cat "$out-phone.out")"
  fi
}
# stack_ok OUT: whether the stack's facts in OUT are closed, then open on its two rows, then closed again
stack_ok() {
  local rows="['wait-review-refund-line-on-receipt', 'wait-merge-refund-line-on-receipt']"
  [ "$(fact "$1" closed '(d["open"], d["rows"], d["merge"])')" = "(False, [], [])" ] \
    && [ "$(fact "$1" closed 'd["head"]')" = "Refund line on receipt 2 things Read the merge review · Waits for the merge" ] \
    && [ "$(fact "$1" opened '(d["open"], d["rows"], d["merge"])')" = "(True, $rows, ['Merge…'])" ] \
    && [ "$(fact "$1" opened '[__import__("re").sub(r" \d+[smhd]( \d+[smh])?$", "", t) for t in d["tops"]] == ["Read the merge review", "Merge the pull request #44"] and all(t[-1] in "smhd" for t in d["tops"])')" = True ] \
    && [ "$(fact "$1" closed-again '(d["open"], d["rows"], d["merge"])')" = "(False, [], [])" ]
}

# The checks of the search over every card (search.js, criteria 1, 3, 6 and 7 of docs/plans/2026-11-22-board-card-search.md),
# after those of "Waits for you": the tasks the criteria name are added to the demo's log first, as a lead's `lem project
# state` writes them, and the backlog item into the demo's backlog folder. Each `s-*` print step gives a label and the
# state, "OPEN | FOCUS | TYPED | PANEL | ROWS": whether the box is open, "field" when its field has the focus, what the
# field holds, the task of the open panel ("-" for none), and the first six rows shown in their order, the marked one
# with a "*" before its name.
search_checks() {
  local out=$WORK/search.out phone=$WORK/search-phone.out item=boards-done-column
  "$PY" "$WORK/event.py" "$LOG" board-card-search held "the criteria wait for the owner"
  "$PY" "$WORK/event.py" "$LOG" clear-a-reported-deadline building "task 1 of 2"
  "$PY" "$WORK/event.py" "$LOG" old-export-fix parked "the owner parked it"
  printf -- "---\nworth: yes\nadded: 2026-11-22\n---\n\n# The board's done column has no limit\n\nDone keeps every card.\n" > "$DEMO/docs/backlog/$item.md"
  "$PY" - "$BASE" "$WORK" "$PY" "$LOG" "$item" > "$WORK/search.json" <<'PY'
import json, shlex, sys
base, work, py, log, item = sys.argv[1:]
STATE = ("(() => { const box = document.getElementById('search'); const q = box?.querySelector('[data-search-target=query]');"
         " const panel = document.querySelector('#task > .panel');"
         " const rows = [...document.querySelectorAll('#search-list a.sr:not([data-js-out])')].slice(0, 6).map(r => (r.hasAttribute('data-js-cur') ? '*' : '') + r.dataset.slug);"
         " return [box?.hasAttribute('data-js-open') ? 'open' : 'closed', q && document.activeElement === q ? 'field' : 'away', q?.value ?? '',"
         " panel ? panel.dataset.task : '-', rows.join(',')].join(' | '); })()")
# A wait for what the board's stream brings after a step of the check wrote it has no limit of its own (None):
# under the load of tests/all.sh the stream brought a proposal after the 15 s of the other waits (2026-11-23)
def until(label, cond, limit=15000):
    """a print step that waits up to LIMIT ms for COND, then gives LABEL and the state; with LIMIT None it has no
    limit of its own, so only the suite's time limit (LEM_TEST_LIMIT) ends a wait for a COND that never comes"""
    end = "Infinity" if limit is None else f"Date.now() + {limit}"
    return {"print": f"new Promise(done => {{ const end = {end}; const tick = () => (({cond}) || Date.now() > end) ? done([{json.dumps(label)}, {STATE}]) : setTimeout(tick, 100); tick(); }})"}
def at(label):
    return {"print": f"[{json.dumps(label)}, {STATE}]"}
def ask(label, expr):
    return {"print": f"[{json.dumps(label)}, {expr}]"}
def key(name, code=None, **more):
    vk = {"Enter": 13, "Escape": 27}.get(name, 0)
    return {"key": name, "code": code or name, "vk": vk, "after": 100, **({"text": "\r"} if name == "Enter" else {}), **more}
def typed(text):
    """the keys of TEXT, each typed as a keyboard types it"""
    return [key(c, "Space" if c == " " else f"Key{c.upper()}", text=c) for c in text]
CMD_K, CTRL_K, ESC = key("k", "KeyK", modifiers=4), key("k", "KeyK", modifiers=2), key("Escape")
def go(url, ready):
    return [{"goto": url, "wait": 300}, until("ready", f"document.readyState === 'complete' && window.Turbo && document.querySelector('#search') && {ready}"), {"wait": 300}]
rank = ("(() => { const ids = [...document.querySelectorAll('#search-list a.sr:not([data-js-out])')].map(r => r.dataset.slug);"
        " return [ids.indexOf('board-card-search'), ids.indexOf('clear-a-reported-deadline')].join(' '); })()")
shown = "[...document.querySelectorAll('#search-list a.sr:not([data-js-out])')].map(r => r.dataset.slug).join(',')"
steps = [
    # Cmd-K on Activity: the box, the cursor in it, the tasks that have not ended, the first marked
    *go(f"{base}/activity", "true"), at("s-before"), CMD_K, at("s-cmdk"),
    ask("s-empty", "(() => { const rows = [...document.querySelectorAll('#search-list a.sr')]; const out = rows.filter(r => !r.hasAttribute('data-js-out'));"
                   " return [out.length > 0 && out.every(r => r.dataset.open), rows.some(r => !r.dataset.open && r.hasAttribute('data-js-out'))].join(' '); })()"),
    # the rule as letters typed: crdsrch, then card, then the words of a parked task and of a backlog item
    *typed("crdsrch"), at("s-crdsrch"),
    {"eval": "document.querySelector('#search [data-search-target=query]').select()"}, *typed("card"), ask("s-card", rank),
    {"eval": "document.querySelector('#search [data-search-target=query]').select()"}, *typed("export"), ask("s-export", shown),
    {"eval": "document.querySelector('#search [data-search-target=query]').select()"}, *typed("done col"), ask("s-donecol", shown),
    {"eval": "document.querySelector('#search [data-search-target=query]').select()"}, *typed("zzqx"),
    ask("s-none", "(() => { const n = document.querySelector('#search .search-none'); return [document.querySelectorAll('#search-list a.sr:not([data-js-out])').length, n.getClientRects().length > 0].join(' '); })()"),
    ask("s-rule", "[LemKit.match('crdsrch', 'Board card search'), LemKit.match('card', 'Board card search'), LemKit.match('card', 'Clear a reported deadline'),"
                  " LemKit.match('CARD S', 'board card search'), LemKit.match('dc', 'cd'), LemKit.match('', 'any')].join(' ')"),
    # Escape closes it with no pick; the arrows move the mark
    ESC, at("s-esc-none"),
    CMD_K, *typed("card"), key("ArrowDown"), at("s-down"), key("ArrowUp"), key("ArrowUp"), at("s-up"), ESC,
    # Enter on crdsrch: the box goes and the task's panel opens beside the view
    CMD_K, *typed("crdsrch"), key("Enter"), until("s-enter", "document.querySelector('#task > .panel')"),
    # Escape in the box with the panel open: the box goes, the panel stays, and the focus goes back where it was
    {"eval": "window.lemBefore = document.activeElement"}, CMD_K, *typed("old"), ESC, at("s-escape"),
    ask("s-back", "String(document.activeElement === window.lemBefore && document.activeElement !== document.body)"),
    # a click on a backlog item's row: the Backlog view, with that item open and under the cursor
    CMD_K, *typed("done col"), {"click": f"#sr-item-{item}"},
    until("s-item", f"location.pathname.endsWith('/backlog') && document.getElementById('item-{item}')?.open"),
    ask("s-item-at", f"(() => {{ const n = document.getElementById('item-{item}'); const b = n.getBoundingClientRect();"
                     f" return [location.hash, n.open, n.hasAttribute('data-js-cur'), b.top >= 0 && b.top < innerHeight].join(' '); }})()"),
    # / on the Backlog is still its filter's key; Cmd-K and Ctrl-K open the box from that field, and Escape gives it back
    {"eval": "document.activeElement.blur()"}, key("/", "Slash", text="/"),
    ask("s-slash", "[document.activeElement?.id ?? '-', document.getElementById('search').hasAttribute('data-js-open')].join(' ')"),
    CMD_K, at("s-cmdk-field"), ESC, ask("s-esc-field", "document.activeElement?.id ?? '-'"), CTRL_K, at("s-ctrlk"), ESC,
    # the search button of the bar
    {"click": ".bar .search-open"}, at("s-button"), ESC,
    # a new event while the box is open: it stays open with the letters, and the new card's row is filtered too
    *go(f"{base}/", "document.querySelector('#kanban')"), CMD_K, *typed("crdsrch"),
    {"sh": " ".join(map(shlex.quote, [py, f"{work}/event.py", log, "refund-note-wording", "building", "task 1 of 2"]))},
    until("s-morph", "document.querySelector('#card-refund-note-wording') && document.querySelector('#sr-task-refund-note-wording')", None),
    ask("s-morph-new", "String(document.getElementById('sr-task-refund-note-wording')?.hasAttribute('data-js-out'))"),
]
print(json.dumps({"width": 1440, "height": 900, "steps": steps}))
PY
  "$PY" - "$BASE" > "$WORK/search-phone.json" <<'PY'
import json, sys
base = sys.argv[1]
STATE = ("(() => { const box = document.getElementById('search'); const q = box?.querySelector('[data-search-target=query]');"
         " return [box?.hasAttribute('data-js-open') ? 'open' : 'closed', q && document.activeElement === q ? 'field' : 'away'].join(' '); })()")
print(json.dumps({"width": 390, "height": 844, "mobile": True, "steps": [
    {"goto": f"{base}/", "wait": 2500}, {"print": f"['p-before', {STATE}]"}, {"click": ".mbar .search-open"}, {"print": f"['p-button', {STATE}]"}]}))
PY
  drive "$WORK/search.json" "$out"
  drive "$WORK/search-phone.json" "$phone"
  local cmdk crdsrch down up
  cmdk=$(seen "$out" s-cmdk)
  down=$(seen "$out" s-down) up=$(seen "$out" s-up)
  down=${down##*| } up=${up##*| }
  if [ "$(seen "$out" s-before | cut -d'|' -f1-4)" = "closed | away |  | - " ] && [[ $cmdk == "open | field |  | - | *"* ]] && [[ ${cmdk##*| } == \** ]] \
    && [ "$(seen "$out" s-empty)" = "true true" ]; then
    pass "Cmd-K on Activity opens the search with the cursor in its field, listing the tasks that have not ended with the first one marked"
  else
    fail "Cmd-K on Activity: $(cat "$out")"
  fi
  if [ "$(seen "$out" s-slash)" = "bl-q-shop false" ] && [ "$(seen "$out" s-cmdk-field | cut -d'|' -f1-2)" = "open | field " ] \
    && [ "$(seen "$out" s-esc-field)" = "bl-q-shop" ] && [ "$(seen "$out" s-ctrlk | cut -d'|' -f1-2)" = "open | field " ] \
    && [ "$(seen "$out" s-button | cut -d'|' -f1-2)" = "open | field " ] \
    && [ "$(seen "$phone" p-before)" = "closed away" ] && [ "$(seen "$phone" p-button)" = "open field" ]; then
    pass "/ on the Backlog still goes to its filter, Cmd-K and Ctrl-K open the search from that field and Escape gives the focus back to it, and the search button opens it on a large screen and on a phone"
  else
    fail "the keys from a field and the buttons: $(cat "$out") / phone: $(cat "$phone")"
  fi
  crdsrch=$(seen "$out" s-crdsrch)
  if [[ $crdsrch == "open | field | crdsrch | - | *board-card-search"* ]] && [[ $crdsrch != *",*"* ]] \
    && "$PY" -c 'import sys; a, b = map(int, sys.argv[1].split()); sys.exit(not (0 <= a < b))' "$(seen "$out" s-card)" \
    && [ "$(seen "$out" s-none)" = "0 true" ] && [ "$(seen "$out" s-rule)" = "11 4 16 6  0" ] \
    && [[ $down == [^*]*,\** ]] && [[ $up == \*board-card-search,* ]]; then
    pass "crdsrch lists Board card search first and marks it, card lists it above Clear a reported deadline, letters no title holds say so, and the arrows move the mark"
  else
    fail "the match and its order: $(cat "$out")"
  fi
  if [[ ",$(seen "$out" s-export)," == *",old-export-fix,"* ]] && [[ ",$(seen "$out" s-donecol)," == *",$item,"* ]] \
    && [[ ",$(seen "$out" s-export),$(seen "$out" s-donecol)," != *",board-card-search,"* ]]; then
    pass "export finds the parked task Old export fix, and done col finds the backlog item The board's done column has no limit, and neither lists Board card search"
  else
    fail "a parked task and a backlog item: $(cat "$out")"
  fi
  if [ "$(seen "$out" s-enter | cut -d'|' -f1,4)" = "closed | board-card-search " ]; then
    pass "Enter on crdsrch closes the box and opens the panel of board-card-search beside the view"
  else
    fail "Enter on a result: $(cat "$out")"
  fi
  if [ "$(seen "$out" s-esc-none | cut -d'|' -f1,4)" = "closed | - " ] && [ "$(seen "$out" s-escape | cut -d'|' -f1,3,4)" = "closed |  | board-card-search " ] \
    && [ "$(seen "$out" s-back)" = "true" ]; then
    pass "Escape closes the box with no pick and empties it, an open panel stays open, and the focus goes back where it was"
  else
    fail "Escape in the box: $(cat "$out")"
  fi
  if [ "$(seen "$out" s-item | cut -d'|' -f1)" = "closed " ] && [ "$(seen "$out" s-item-at)" = "#item-$item true true true" ]; then
    pass "a click on a backlog item's row closes the box and shows the Backlog view with that item open, under the cursor and in view"
  else
    fail "a click on a backlog item: $(cat "$out")"
  fi
  if [ "$(seen "$out" s-morph | cut -d'|' -f1-3)" = "open | field | crdsrch " ] && [[ "$(seen "$out" s-morph)" == *"| *board-card-search"* ]] \
    && [ "$(seen "$out" s-morph-new)" = "true" ]; then
    pass "a new event while the box is open keeps it open with the letters typed and the mark, and the new task's row is filtered by them too"
  else
    fail "the box through a morph: $(cat "$out")"
  fi
}

# The confirm step of a merge, which on a phone is an overlay whose button comes on when its text was read to the end
# (lem_board_task.py `merge_step`, the `sheet` controller, board.css). The demo writes no landing record, so a merge step
# has no button: merge.py writes what land.py keeps and logs for an open task. `merge.py landing STATE TASK PR TIP`: its
# landing.json with the proposed tip and the pull request; `merge.py review LOG TASK`: a review's careful call;
# `merge.py proposed LOG TASK TIP N`: a proposal of TIP that is not green for the first N of the demo's four reasons
# (green for 0); `merge.py open LOG TASK PR`: the state open with the pull request; `merge.py started LOG TASK`: whether
# a merge.start of TASK comes into the log within 20 s (land.py logs it only for the tip proposed now, `--tip`).
cat > "$WORK/merge.py" <<'PY'
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
REASONS = ["decision 1 was taken without the owner (Where the refund line goes on the receipt): \"B: a line of its own under the items, then the total\", by the dialectic",
           "the owner did not approve the criteria: they were approved while the task ran without the owner",
           "the bar is lower in `tests/test_receipt.py` (one assertion fewer)",
           "two rounds reviewed it: the last one left no must-fix, and round 1 left 1 must-fix that pull request #44 answers"]
verb, where, task, *more = sys.argv[1:]
def log(event, **fields):
    with open(where, "a", encoding="utf-8") as out:
        out.write(json.dumps({"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": event, "task": task, **fields}) + "\n")
if verb == "landing":
    pr, tip = more
    folder = Path(where) / "tasks" / task
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "landing.json").write_text(json.dumps({"pr": {"number": int(pr), "url": f"https://github.com/acme/shop/pull/{pr}"}, "proposed": tip,
                                                     "title": f"feat: {task}", "branch": f"feat/{task}"}, indent=2) + "\n")
elif verb == "review":
    log("review", attempt=3, round=3, kind="round", verdict="clean", must_fix=0, should=0, nit=0, answered=["codex", "claude"], silent=[], ran=[], left_out=[],
        careful=True, careful_why="the total under the refund is money the customer pays")
elif verb == "proposed":
    tip, n = more
    log("proposed", green=int(n) == 0, not_green=REASONS[:int(n)], tip=tip[:9])
elif verb == "open":
    log("task.state", status="open", text=f"pull request https://github.com/acme/shop/pull/{more[0]}", lines=["not green"], ask=task)
elif verb == "started":
    def started():
        return any(json.loads(line).get("event") == "merge.start" and json.loads(line).get("task") == task for line in open(where, encoding="utf-8"))
    end = time.time() + 20
    while time.time() < end and not started():
        time.sleep(0.2)
    print(json.dumps(["started", started()]))
PY

# The checks of the confirm step, after the other checks of the block: pull request 44 of refund-line-on-receipt, not
# green for four reasons and careful, at a phone's width with a height where its text goes on below the screen (390 x
# 664) and at 390 x 844, where it fits; a green open task of the check's own; a desktop's screen; and the page with its
# scripts off, whose click posts the form to the server's guard, which takes it.
confirm_checks() {
  local refund=refund-line-on-receipt green=coupon-code-in-email tip moved shorter out=$WORK/confirm
  tip=$(git -C "$DEMO" rev-parse "feat/$refund")
  moved=1111111111111111111111111111111111111111 shorter=2222222222222222222222222222222222222222
  "$PY" "$WORK/merge.py" landing "$DEMO/.lem/state" "$refund" 44 "$tip"
  "$PY" "$WORK/merge.py" review "$LOG" "$refund"
  "$PY" "$WORK/merge.py" proposed "$LOG" "$green" 3333333333333333333333333333333333333333 0
  "$PY" "$WORK/merge.py" open "$LOG" "$green" 45
  "$PY" "$WORK/merge.py" landing "$DEMO/.lem/state" "$green" 45 3333333333333333333333333333333333333333
  "$PY" - "$BASE" "$WORK" "$PY" "$LOG" "$DEMO/.lem/state" "$refund" "$green" "$moved" "$shorter" <<'PY'
import json, shlex, sys
base, work, py, log, state, refund, green, moved, shorter = sys.argv[1:]
step = f"{base}/tasks/{refund}/merge?in=waits"
# the card's facts: whether the controller marked it, its position, the head's, the button's and Back's top and bottom,
# the parts of the body in their order, the facts in theirs, the button's aria-disabled and label, the body's scroll and
# its height and its content's, whether the note's end is below the body's, and the class of what has the focus; on a page
# without the parts (the base commit's), the error, so that the print step ends and the check fails
FACTS = ("(() => { try { const c = document.querySelector('#confirm'), body = c.querySelector('.cf-body'), b = c.querySelector('.cf-foot button'), note = c.querySelector('.cf-note');"
         " const at = n => n ? [Math.round(n.getBoundingClientRect().top), Math.round(n.getBoundingClientRect().bottom)] : null;"
         " return {sheet: c.hasAttribute('data-js-sheet'), position: getComputedStyle(c).position, head: at(c.querySelector('.cf-head .eyebrow')), headWords: c.querySelector('.cf-head').textContent.trim(),"
         " button: at(b), back: at(c.querySelector('.cf-foot a.btn')), backWords: c.querySelector('.cf-foot a.btn').textContent.trim(), screen: innerHeight,"
         " parts: [...body.children].map(n => n.className.split(' ').find(k => ['cf-first', 'reasons', 'cf-careful-why', 'cf-facts', 'cf-note'].includes(k)) ?? n.className).join(' '),"
         " facts: [...body.querySelectorAll('.cf-facts dt')].map(n => n.id.replace('cf-dt-', '')).join(' '),"
         " disabled: b.getAttribute('aria-disabled'), label: b.textContent.trim(), top: Math.round(body.scrollTop), height: body.clientHeight, content: body.scrollHeight,"
         " noteBelow: note.getBoundingClientRect().bottom > body.getBoundingClientRect().bottom + 1, noteEnd: Math.round(note.getBoundingClientRect().bottom), buttonTop: Math.round(b.getBoundingClientRect().top),"
         " fixed: [c, ...c.querySelectorAll('*')].some(n => ['fixed', 'sticky'].includes(getComputedStyle(n).position)), focus: document.activeElement?.className ?? '-',"
         " commit: c.querySelector('#cf-dd-commit .mono')?.textContent ?? '-' }; } catch (e) { return {error: String(e)}; } })()")
def until(label, cond, limit=15000):
    """a print step that waits up to LIMIT ms for COND, then gives LABEL and the card's facts; with LIMIT None it has no
    limit of its own, so only the suite's time limit (LEM_TEST_LIMIT) ends a wait for a COND that never comes"""
    end = "Infinity" if limit is None else f"Date.now() + {limit}"
    return {"print": f"new Promise(done => {{ const end = {end}; const tick = () => (({cond}) || Date.now() > end) ? done([{json.dumps(label)}, {FACTS}]) : setTimeout(tick, 100); tick(); }})"}
def at(label):
    return {"print": f"[{json.dumps(label)}, {FACTS}]"}
def sh(*argv):
    return {"sh": " ".join(map(shlex.quote, argv))}
def acts(label):
    return sh(py, "-c", "import json, sys; print(json.dumps([sys.argv[1], sum('\"board.act\"' in line for line in open(sys.argv[2]))]))", label, log)
ready = "document.readyState === 'complete' && document.querySelector('#confirm[data-js-sheet]')"
to_end = {"eval": "(() => { const b = document.querySelector('#confirm .cf-body'); b.scrollTop = b.scrollHeight; })()", "after": 500}
specs = {
    # the text goes on below the screen: the button is off and a tap posts nothing, then on at the end; a new proposal,
    # and one that brings a shorter text to a body scrolled to just above its end, each start the read again at the top.
    # The wait for each proposal has no limit of its own: under the load of tests/all.sh the board's stream brought the
    # first one after the 15 s of the other waits (2026-11-23), and the read after it is what the check is about
    "gate": {"width": 390, "height": 664, "mobile": True, "steps": [
        {"goto": step, "wait": 300}, until("open", ready), {"wait": 300}, at("opened"),
        acts("acts-before"), {"click": "#confirm .cf-foot button"}, {"wait": 700}, {"print": "['tapped', location.pathname + location.search]"}, acts("acts-after"), at("after-tap"),
        to_end, at("end"),
        sh(py, f"{work}/merge.py", "landing", state, refund, "44", moved), sh(py, f"{work}/merge.py", "proposed", log, refund, moved, "4"),
        until("moved", f"document.querySelector('#cf-dd-commit .mono')?.textContent === '{moved[:12]}'", None), {"wait": 400}, at("moved-after"),
        {"eval": "(() => { const b = document.querySelector('#confirm .cf-body'); b.scrollTop = b.scrollHeight - b.clientHeight - 12; })()", "after": 500}, at("near"),
        sh(py, f"{work}/merge.py", "landing", state, refund, "44", shorter), sh(py, f"{work}/merge.py", "proposed", log, refund, shorter, "3"),
        until("shorter", f"document.querySelector('#cf-dd-commit .mono')?.textContent === '{shorter[:12]}'", None), {"wait": 400}, at("shorter-after"),
    ]},
    # the screen of criterion 1, where the text of #44 fits
    "phone": {"width": 390, "height": 844, "mobile": True, "steps": [{"goto": step, "wait": 300}, until("open", ready), {"wait": 300}, at("phone")]},
    "green": {"width": 390, "height": 844, "mobile": True, "steps": [{"goto": f"{base}/tasks/{green}/merge?in=waits", "wait": 300}, until("open", ready), {"wait": 300}, at("green")]},
    "desk": {"width": 1440, "height": 900, "steps": [{"goto": step, "wait": 300}, until("open", ready), {"wait": 300}, at("desk")]},
    # with no script: no controller, so no overlay; the click posts the form, and the server's guard takes it
    "noscript": {"width": 390, "height": 844, "mobile": True, "noscript": True, "posts": True, "steps": [
        {"goto": step, "wait": 2500},
        {"print": "['page', (() => { const p = document.querySelector('.panel'); return [typeof window.Turbo, p.scrollHeight > p.clientHeight].join(' '); })()]"}, at("off"),
        {"click": "#confirm .cf-foot button"}, {"wait": 1500}, {"print": "['answer', document.body.innerText.slice(0, 300)]"}, sh(py, f"{work}/merge.py", "started", log, refund)]},
}
for name, spec in specs.items():
    with open(f"{work}/confirm-{name}.json", "w", encoding="utf-8") as out:
        json.dump(spec, out)
PY
  # the order: the phone's, the green task's and the desktop's look before the gate's proposals move #44, and the merge last
  drive "$WORK/confirm-phone.json" "$out-phone.out"
  drive "$WORK/confirm-green.json" "$out-green.out"
  drive "$WORK/confirm-desk.json" "$out-desk.out"
  drive "$WORK/confirm-gate.json" "$out-gate.out"
  drive "$WORK/confirm-noscript.json" "$out-noscript.out"
  local phone=$out-phone.out gate=$out-gate.out
  if [ "$(fact "$phone" phone 'd["sheet"] and d["position"] == "fixed" and d["head"][0] >= 0 and d["button"][1] <= d["screen"] and d["back"][1] <= d["screen"] and d["back"][0] > d["button"][0]')" = True ] \
    && [ "$(fact "$phone" phone 'd["headWords"]')" = "Merge #44 · confirm" ] && [ "$(fact "$phone" phone 'd["backWords"]')" = Back ] \
    && [ "$(fact "$phone" phone 'd["parts"]')" = "cf-first reasons cf-careful-why cf-facts cf-note" ] && [ "$(fact "$phone" phone 'd["facts"]')" = "pr commit branch into as" ] \
    && [ "$(fact "$gate" opened 'd["focus"]')" = cf-head ]; then
    pass "on a phone of 390 x 844 the merge step of #44 is an overlay: the head Merge #44 · confirm at its top and the focus on it, the body in the order green or not green, the reasons, Careful:, the facts and the note, and the button and Back inside the screen"
  else
    fail "the merge step's overlay on a phone: $(cat "$phone") / $(seen "$gate" opened)"
  fi
  if [ "$(fact "$gate" opened 'd["sheet"] and d["noteBelow"] and d["button"][1] <= d["screen"]')" = True ] && [ "$(fact "$gate" opened 'd["disabled"], d["label"]')" = "('true', 'Read to the end ↓')" ] \
    && [ "$(seen "$gate" tapped)" = "/$HOST/shop/tasks/$refund/merge?in=waits" ] && [ "$(seen "$gate" acts-before)" = "$(seen "$gate" acts-after)" ] && [ "$(seen "$gate" acts-after)" != "nothing printed" ] \
    && [ "$(fact "$gate" after-tap 'd["label"]')" = "Read to the end ↓" ] \
    && [ "$(fact "$gate" end 'd["disabled"], d["label"]')" = "(None, 'Merge pull request #44')" ]; then
    pass "while the text of #44 goes on below the screen its button is off and reads Read to the end ↓, a tap on it posts nothing, and after the body is scrolled to its end it reads Merge pull request #44 and is on"
  else
    fail "the button gated by the read: $(cat "$gate")"
  fi
  if [ "$(fact "$gate" moved-after 'd["commit"], d["top"], d["disabled"], d["label"]')" = "('${moved:0:12}', 0, 'true', 'Read to the end ↓')" ] \
    && [ "$(fact "$gate" near 'd["top"] > 0 and d["disabled"] == "true"')" = True ] \
    && [ "$(fact "$gate" shorter-after 'd["commit"], d["top"], d["content"] > d["height"], d["disabled"], d["label"]')" = "('${shorter:0:12}', 0, True, 'true', 'Read to the end ↓')" ]; then
    pass "a new proposal of #44 after its read brings the body back to its top with the button off, and so does one with a shorter text that comes while the body stands just above its end"
  else
    fail "the read after a morph to another text: $(seen "$gate" moved-after) / $(seen "$gate" near) / $(seen "$gate" shorter-after)"
  fi
  if [ "$(fact "$out-green.out" green 'd["sheet"], d["position"], d["content"] <= d["height"], d["disabled"], d["label"]')" = "(True, 'fixed', True, None, 'Merge pull request #45')" ]; then
    pass "the merge step of a green pull request whose text fits on a phone's screen has its button on from the first look"
  else
    fail "the green merge step on a phone: $(cat "$out-green.out")"
  fi
  if [ "$(fact "$out-desk.out" desk 'd["sheet"], d["fixed"], d["disabled"], d["label"], d["buttonTop"] > d["noteEnd"], d["headWords"], d["backWords"]')" = "(True, False, None, 'Merge pull request #44', True, 'Merge #44 · confirm', 'Back')" ]; then
    pass "on a desktop's screen of 1440 x 900 the merge step of #44 has no fixed part, and its button is on, below its text in the page"
  else
    fail "the merge step on a desktop: $(cat "$out-desk.out")"
  fi
  if [ "$(seen "$out-noscript.out" page)" = "undefined true" ] \
    && [ "$(fact "$out-noscript.out" off 'd["sheet"], d["fixed"], d["disabled"], d["label"], d["buttonTop"] > d["noteEnd"]')" = "(False, False, None, 'Merge pull request #44', True)" ] \
    && [ "$(seen "$out-noscript.out" post)" = "$BASE/tasks/$refund/merge confirm=yes&tip=$shorter&in=waits" ] && [ "$(seen "$out-noscript.out" started)" = True ]; then
    pass "with no script the merge step of #44 is one page that scrolls, its button is on at the end of its text, and its click posts the form with confirm=yes and the commit the page showed, which the server's guard takes: land.py starts the merge of that commit"
  else
    fail "the merge step with no script: $(cat "$out-noscript.out")"
  fi
}

# Drop on a phone (criterion 6 of board-answers-a-card): on "Waits for you" at 390 x 844 the breaker's row of
# gift-note-in-export holds its one answer form; the owner writes a note and taps Drop…, and the panel opens the
# confirm step as the overlay a park's step is, which asks "Drop gift-note-in-export?" with Confirm and the note he
# wrote, and the row's key in the address. The tap posts nothing: the drop waits for his Confirm. Before step_checks,
# which park the task.
drop_checks() {
  local out=$WORK/drop.out
  "$PY" - "$BASE" "$PY" "$LOG" > "$WORK/drop.json" <<'PY'
import json, shlex, sys
base, py, log = sys.argv[1:]
row = "article[id^='wait-breaker-gift-note-in-export-1-']"
facts = ("(() => { const c = document.querySelector('#confirm'); if (!c) return {error: 'no step'}; const b = c.querySelector('.cf-foot button[type=submit]'), f = c.querySelector('.cf-foot form');"
         " return {where: location.pathname + location.search, sheet: c.hasAttribute('data-js-sheet'), position: getComputedStyle(c).position, head: c.querySelector('.cf-head').textContent.trim(),"
         " label: b.textContent.trim(), disabled: b.getAttribute('aria-disabled'), action: f.getAttribute('action'), option: f.querySelector('input[name=option]').value,"
         " confirm: f.querySelector('input[name=confirm]').value, note: f.querySelector('textarea[name=words]').value, key: f.querySelector('input[name=key]').value,"
         " inScreen: b.getBoundingClientRect().bottom <= innerHeight }; })()")
acts = {"sh": " ".join(map(shlex.quote, [py, "-c", "import json, sys; print(json.dumps(['acts', sum('\"board.act\"' in line for line in open(sys.argv[1]))]))", log]))}
steps = [
    {"goto": f"{base}/waits", "wait": 300},
    {"print": "new Promise(done => { const end = Date.now() + 15000; const tick = () => ((document.readyState === 'complete' && window.Turbo"
              f" && document.querySelector(\"{row} form.answer-form\")) || Date.now() > end) ? done(['ready', Boolean(document.querySelector(\"{row} form.answer-form\"))]) : setTimeout(tick, 100); tick(); }})"},
    {"wait": 800},
    {"print": f"['row', [...document.querySelectorAll(\"{row} form.answer-form button\")].map(b => b.textContent.trim()).join(' | ')]"},
    acts, {"eval": f"document.querySelector(\"{row} textarea[name=words]\").value = 'the export goes another way'", "after": 200},
    {"click": f"{row} button[formaction$='/drop']", "tap": True, "after": 300},
    {"print": "new Promise(done => { const end = Date.now() + 15000; const tick = () => ((document.querySelector('#confirm[data-js-sheet]')"
              f" && location.pathname.endsWith('/drop')) || Date.now() > end) ? done(['step', {facts}]) : setTimeout(tick, 100); tick(); }})"},
    {"wait": 700}, {**acts, "sh": acts["sh"].replace("'acts'", "'acts-after'")},
]
print(json.dumps({"width": 390, "height": 844, "mobile": True, "steps": steps}))
PY
  drive "$WORK/drop.json" "$out"
  if [ "$(seen "$out" ready)" = True ] && [ "$(seen "$out" row)" = "Help | Park… | Drop…" ] \
    && [ "$(fact "$out" step 'd["where"].split("?")[0], d["sheet"], d["position"], d["head"], d["label"], d["disabled"], d["inScreen"]')" = "('/$HOST/shop/tasks/gift-note-in-export/drop', True, 'fixed', 'Drop gift-note-in-export?', 'Confirm', None, True)" ] \
    && [ "$(fact "$out" step 'd["action"], d["option"], d["confirm"], d["note"], d["key"].startswith("breaker:gift-note-in-export:1:"), "key=breaker" in d["where"]')" = "('/$HOST/shop/tasks/gift-note-in-export/answer', 'drop', 'yes', 'the export goes another way', True, True)" ] \
    && [ "$(seen "$out" acts)" = "$(seen "$out" acts-after)" ] && [ "$(seen "$out" acts)" != "nothing printed" ]; then
    pass "on a phone the breaker's row has Help, Park… and Drop…; a tap on Drop… opens the overlay that asks Drop gift-note-in-export? with Confirm and the note the owner wrote in the row, and posts nothing"
  else
    fail "Drop's confirm on a phone: $(cat "$out")"
  fi
}

# Each kind of card on a phone (criterion 5 of board-answers-a-card): each of the ten templates of lem-ask, rendered as
# lem-ask renders it and kept as a card of refund-rounding's live session as lem-ask keeps it (`lem_cards.keep`, page
# T-NAME), opened through the board's card route at 390 x 844 with a phone's touch. For each question of each card the
# look's facts: the page's width and the window's, each element past the window's edges outside a box that scrolls
# sideways (a wide table's), each box that clips its text or hides the end of a line of code, each option and control smaller than WCAG 2.2's minimum target of 24 px or not
# what a tap at its center hits, the key hints and the "Discuss in chat" shown, and the smallest text of a chart or a
# diagram, in px as drawn; then a tap on each option, its pick before and after. The same pick page from its file, as
# agterm shows it, at a desktop's 1440 px keeps its keys and "Discuss in chat". The stand-in agtermctl says that no
# answer waits at the Mac (`session overlay result`), as agterm does for an open page.
CARD=4F9A1C2E-7B3D-4E8F-A1B2-C3D4E5F60718  # the showcase's card of refund-rounding (tests/board-showcase.py CARD_PAGE)
RR=$DEMO/.lem/state/tasks/refund-rounding
cat > "$WORK/kinds.py" <<'PY'
import json, os, sys
verb, base, tdir, work = sys.argv[1:5]
NAMES = sorted(f[:-5] for f in os.listdir(tdir) if f.endswith(".json"))
if verb == "keep":
    # each template as a card of the task's live session: the session of the showcase's own card
    import subprocess
    from pathlib import Path
    task = Path(sys.argv[5])
    sys.path.insert(0, sys.argv[6])
    import lem_cards
    session = json.loads(next((task / "cards").glob("*.json")).read_text())["session"]
    for name in NAMES:
        page = f"{work}/{name}.html"
        subprocess.run([sys.executable, "-B", sys.argv[7], "render", f"{tdir}/{name}.json", "-o", page], check=True, capture_output=True)
        lem_cards.keep(task, f"T-{name}", Path(page).read_bytes(), json.loads(Path(f"{tdir}/{name}.json").read_text()), session)
    sys.exit()
LOOK = r"""(() => { const W = innerWidth, d = document.documentElement;
 const name = n => n.tagName.toLowerCase() + (typeof n.className === 'string' && n.className.trim() ? '.' + n.className.trim().split(/\s+/).join('.') : '');
 const shown = n => n.getClientRects().length > 0 && getComputedStyle(n).visibility !== 'hidden';
 const sideways = n => { for (let p = n.parentElement; p; p = p.parentElement) if (['auto', 'scroll'].includes(getComputedStyle(p).overflowX)) return true; return false; };
 const all = [...document.querySelectorAll('.hd *')].filter(shown);
 const over = all.filter(n => !(n.closest('svg') && n.tagName.toLowerCase() !== 'svg') && !sideways(n)).filter(n => { const b = n.getBoundingClientRect(); return b.right > W + 0.5 || b.left < -0.5; }).map(name);
 const clipped = all.filter(n => (['hidden', 'clip'].includes(getComputedStyle(n).overflowX) || n.matches('.hd-code')) && n.scrollWidth > n.clientWidth + 1).map(name);
 const taps = [...document.querySelectorAll('.hd-q.cur .hd-opt, .hd-q.cur .hd-toggle, .hd-q.cur .hd-ctl input, .hd-q.cur .hd-seg button, .hd-q.cur .hd-ctl-r, .hd-q.cur textarea, .hd-q.cur .hd-replay, .hd-tab, .hd-foot .hd-btn')].filter(shown).map(n => {
   n.scrollIntoView({block: 'center'}); const b = n.getBoundingClientRect(), at = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
   return {n: name(n), w: Math.round(b.width), h: Math.round(b.height), hit: Boolean(at && (n.contains(at) || at.contains(n)))}; });
 const fonts = [...document.querySelectorAll('.hd-q.cur svg')].filter(v => shown(v) && !v.closest('.hd-prev') && v.viewBox.baseVal && v.viewBox.baseVal.width).flatMap(v => {
   const k = v.getBoundingClientRect().width / v.viewBox.baseVal.width;
   return [...v.querySelectorAll('text, foreignObject span, foreignObject p')].filter(t => t.textContent.trim() && shown(t)).map(t => parseFloat(getComputedStyle(t).fontSize) * k); });
 scrollTo(0, 0);
 return {page: [d.scrollWidth, d.clientWidth], over, clipped, small: taps.filter(t => t.w < 24 || t.h < 24).map(t => `${t.n} ${t.w}x${t.h}`), missed: taps.filter(t => !t.hit).map(t => t.n),
   taps: taps.length, keys: [...document.querySelectorAll('.hd-keys, .hd-tabkey, .hd-btn kbd')].filter(shown).length,
   chat: [...document.querySelectorAll('.hd-btn')].filter(n => shown(n) && /chat/i.test(n.textContent)).length, smallest: fonts.length ? Math.round(Math.min(...fonts) * 10) / 10 : null}; })()"""
def until(label, cond):
    return {"print": f"new Promise(done => {{ const end = Date.now() + 15000; const tick = () => (({cond}) || Date.now() > end) ? done([{json.dumps(label)}, Boolean({cond})]) : setTimeout(tick, 100); tick(); }})"}
drawn = "document.readyState === 'complete' && document.querySelector('.hd-foot') && [...document.querySelectorAll('.hd-q.cur .hd-mermaid')].every(m => m.querySelector('svg') || m.classList.contains('err'))"
if verb == "spec":
    steps = []
    for name in NAMES:
        spec = json.load(open(f"{tdir}/{name}.json"))
        qs = spec.get("questions") or [spec]
        steps += [{"goto": f"{base}/tasks/refund-rounding/cards/T-{name}/", "wait": 300}, until(f"ready:{name}", drawn), {"wait": 300}]
        for qi, q in enumerate(qs):
            if len(qs) > 1:
                steps += [{"click": f".hd-tab:nth-child({qi + 1})", "tap": True, "after": 300}, until(f"tab:{name}:{qi}", drawn)]
            steps.append({"print": f"['look:{name}:{qi}', {LOOK}]"})
            for k in range(len(q.get("options") or [])):
                # the tap on the option's name, as a finger picks it (a compare card's pros and cons take no pick), and 700 ms
                # apart: two taps within Chrome's double-click time at the same place, the screen's middle, would send the card
                sel = f".hd-q.cur .hd-opts > .hd-opt:nth-child({k + 1})"
                on = f"document.querySelector('{sel}')?.classList.contains('on') ?? null"
                steps += [{"print": f"['before:{name}:{qi}:{k}', {on}]"}, {"click": f"{sel} .hd-label", "tap": True, "after": 700}, {"print": f"['after:{name}:{qi}:{k}', {on}]"}]
                if (q.get("mode") or "single") == "multi":
                    # a second tap gives the pick back, so that a question's `max` never refuses the next option
                    steps.append({"click": f"{sel} .hd-label", "tap": True, "after": 700})
    print(json.dumps({"width": 390, "height": 844, "mobile": True, "steps": steps}))
    # the page outside the board: the pick card from its file, as agterm shows it, on a desktop's screen
    desk = [{"goto": f"file://{work}/pick.html", "wait": 300}, until("ready", drawn), {"print": f"['desk', {LOOK}]"}]
    json.dump({"width": 1440, "height": 900, "steps": desk}, open(f"{work}/kinds-desk.json", "w"))
if verb == "judge":
    # what the drive printed, against the rule: one line of what is wrong for each question, nothing when all holds
    seen = {}
    for line in open(f"{work}/kinds.out", encoding="utf-8"):
        try:
            got = json.loads(line)
        except ValueError:
            continue
        if isinstance(got, list) and len(got) == 2 and isinstance(got[0], str):
            seen[got[0]] = got[1]
    wrong = []
    for name in NAMES:
        spec = json.load(open(f"{tdir}/{name}.json"))
        for qi, q in enumerate(spec.get("questions") or [spec]):
            d = seen.get(f"look:{name}:{qi}")
            if not isinstance(d, dict):
                wrong.append(f"{name} {qi + 1}: nothing printed"); continue
            if d["page"][0] > d["page"][1]:
                wrong.append(f"{name} {qi + 1}: the page is {d['page'][0]} px wide in a window of {d['page'][1]}")
            for key, what in (("over", "past the screen's edge"), ("clipped", "clips its text or hides a line's end"), ("small", "under 24 px"), ("missed", "not hit by a tap at its center")):
                if d[key]:
                    wrong.append(f"{name} {qi + 1}: {what}: {', '.join(d[key][:4])}")
            if d["keys"] or d["chat"]:
                wrong.append(f"{name} {qi + 1}: {d['keys']} key hints and {d['chat']} Discuss in chat shown")
            if d["smallest"] is not None and d["smallest"] < 10:
                wrong.append(f"{name} {qi + 1}: a chart's text is {d['smallest']} px")
            if not d["taps"]:
                wrong.append(f"{name} {qi + 1}: no option or control")
            for k in range(len(q.get("options") or [])):
                before, after = seen.get(f"before:{name}:{qi}:{k}"), seen.get(f"after:{name}:{qi}:{k}")
                if after is None or (before == after and after is not True):
                    wrong.append(f"{name} {qi + 1}: a tap on option {k + 1} picked nothing ({before} then {after})")
    desk = seen.get("desk-look")
    if not (isinstance(desk, dict) and desk["keys"] and desk["chat"] == 1):
        wrong.append(f"the pick page from its file on a desktop: {desk}")
    print("; ".join(wrong) or "ok")
PY
card_kinds_checks() {
  local judged
  "$PY" -B "$WORK/kinds.py" keep - "$PWD/skills/lem-ask/templates" "$WORK" "$RR" "$PWD/skills/lem/scripts" "$PWD/skills/lem-ask/bin/lem-ask"
  "$PY" -B "$WORK/kinds.py" spec "$BASE" "$PWD/skills/lem-ask/templates" "$WORK" > "$WORK/kinds.json"
  drive "$WORK/kinds.json" "$WORK/kinds.out"
  drive "$WORK/kinds-desk.json" "$WORK/kinds-desk.out"
  sed 's/^\["desk",/["desk-look",/' "$WORK/kinds-desk.out" >> "$WORK/kinds.out"
  judged=$("$PY" -B "$WORK/kinds.py" judge - "$PWD/skills/lem-ask/templates" "$WORK")
  if [ "$judged" = ok ]; then
    pass "each of the ten templates of lem-ask, put up as a card of a task's session, opens through the board's card route on a phone of 390 x 844 with nothing past the screen's edges and no box that clips its text or hides a line of code's end, its charts' text at 10 px or more, every option and control at least 24 px each way and hit by a tap at its center, a tap on each option picks it, and no key hint and no Discuss in chat; the same page from its file on a desktop keeps its keys and Discuss in chat"
  else
    fail "each kind of card on a phone: $judged"
  fi
}

# The Tune card on a phone (criterion 5 and the plan talk's question 8 of board-answers-a-card): on the board's card route
# at 390 x 844 the owner taps the preset Soft, moves the corner radius to 20 by a finger's drag (the slider's own input
# event), and taps Submit. The board takes those values as his answer: the card's end, from the board, holds the values
# with radius 20, no preset kept, and Soft as the preset he started from. After card_kinds_checks, which keep the card.
card_tune_checks() {
  local out=$WORK/tune.out
  "$PY" - "$BASE" "$RR" > "$WORK/tune.json" <<'PY'
import json, shlex, sys
base, task = sys.argv[1:]
end = f"{task}/cards/T-tune.end.json"
read = "import json, sys, time\nfor _ in range(50):\n    try:\n        d = json.load(open(sys.argv[1])); break\n    except (OSError, ValueError):\n        time.sleep(0.2)\nelse:\n    d = None\nprint(json.dumps(['end', d and [d['status'], d['from'], d['answer']['answers']]]))"
print(json.dumps({"width": 390, "height": 844, "mobile": True, "steps": [
    {"goto": f"{base}/tasks/refund-rounding/cards/T-tune/", "wait": 1500},
    {"click": ".hd-opts > .hd-opt:nth-child(2) .hd-label", "tap": True, "after": 700},
    {"eval": "(() => { const r = document.querySelector('.hd-ctl.range input[type=range]'); r.value = 20; r.dispatchEvent(new Event('input', {bubbles: true})); })()"},
    {"print": "['picked', [document.querySelector('.hd-ctl-v').textContent, document.querySelectorAll('.hd-opt.on').length]]"},
    {"click": ".hd-foot .hd-btn.primary", "tap": True, "after": 1500},
    {"print": "['answered', document.querySelector('.hd-done')?.textContent ?? '-']"},
    {"sh": " ".join(map(shlex.quote, [sys.executable, "-c", read, end]))}]}))
PY
  drive "$WORK/tune.json" "$out"
  if [ "$(seen "$out" picked)" = "['20px', 0]" ] && [ "$(seen "$out" answered)" = "Your answer is on record: the task’s session takes it." ] \
    && [ "$(fact "$out" end 'd[0], d[1], d[2]["answer"]["values"]["radius"], d[2]["answer"]["values"]["gap"], d[2]["answer"]["selected"], d[2]["answer"].get("from")')" = "('answered', 'board', 20, 16, [], 'soft')" ]; then
    pass "on a phone the Tune card takes a tap on the preset Soft, a slider moved to a corner radius of 20 and a tap on Submit, and the board takes those values as the owner's answer: radius 20 with Soft's gap of 16, no preset kept, and Soft as where he started"
  else
    fail "the Tune card on a phone: $(cat "$out")"
  fi
}

# A card answered on a phone (the phone half of criteria 1 and 3 of board-answers-a-card, and 2's row that leaves): on
# "Waits for you" at 390 x 844, with an iPhone's user agent, the row of refund-rounding's card shows its question, in the
# task's stack, which a tap opens; a tap on the row opens the card's step as the overlay of the whole screen, with the same page as in agterm, both options and the
# note field, and no key hint or Discuss in chat. A note with no pick is refused with the board's line, nothing is
# recorded and the row stays; Only the total with a note is on record as the owner's from the phone, the page says so,
# and the row leaves the list with no reload. After card_tune_checks.
card_phone_checks() {
  local out=$WORK/card-phone.out
  "$PY" - "$BASE" "$RR" "$CARD" > "$WORK/card-phone.json" <<'PY'
import json, shlex, sys
base, task, card = sys.argv[1:]
row, frame = f"#wait-card-refund-rounding-{card}", f"#card-frame-{card}"
doc = f"document.querySelector('{frame}')?.contentDocument"
def until(label, cond, value):
    return {"print": f"new Promise(done => {{ const end = Date.now() + 15000; const tick = () => (({cond}) || Date.now() > end) ? done([{json.dumps(label)}, {value}]) : setTimeout(tick, 100); tick(); }})"}
def note(text):
    return {"eval": f"(() => {{ const t = {doc}.querySelector('.hd-q.cur textarea'); t.value = {json.dumps(text)}; t.dispatchEvent(new t.ownerDocument.defaultView.Event('input', {{bubbles: true}})); }})()"}
def tap(sel, after=600):
    return {"click": sel, "frame": frame, "tap": True, "after": after}
ended = "import json, os, sys\nf = sys.argv[1]\nd = json.load(open(f)) if os.path.exists(f) else None\nprint(json.dumps([sys.argv[2], d and [d['status'], d['from'], d['device'], d['answer']['answers']['answer']]]))"
def end(label):
    return {"sh": " ".join(map(shlex.quote, [sys.executable, "-c", ended, f"{task}/cards/{card}.end.json", label]))}
LOOK = (f"(() => {{ const d = {doc}, step = document.getElementById('card-step'); const shown = n => n.getClientRects().length > 0;"
        " return {sheet: step?.hasAttribute('data-js-sheet') ?? false, position: step ? getComputedStyle(step).position : '-', prompt: d.querySelector('.hd-prompt').textContent,"
        " options: [...d.querySelectorAll('.hd-opt .hd-label')].map(n => n.firstChild.textContent.trim()), note: Boolean(d.querySelector('.hd-q.cur textarea')),"
        " keys: [...d.querySelectorAll('.hd-keys, .hd-tabkey, .hd-btn kbd')].filter(shown).length, chat: [...d.querySelectorAll('.hd-btn')].filter(n => shown(n) && /chat/i.test(n.textContent)).length}; })()")
print(json.dumps({"width": 390, "height": 844, "mobile": True,
                  "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1", "steps": [
    {"goto": f"{base}/waits", "wait": 300},
    until("row", f"document.readyState === 'complete' && window.Turbo && document.querySelector('{row} a.wr-verb')", f"document.querySelector('{row} a.wr-verb')?.textContent.trim() ?? '-'"),
    {"wait": 800},
    # the cards card_kinds_checks kept make refund-rounding a task of two or more things, so its row is in the task's
    # stack, closed as the page comes: a tap on the stack's summary opens it first
    {"click": "#wait-stack-refund-rounding:not([open]) > summary", "tap": True, "after": 500},
    {"eval": "window.lemStay = 1"},
    {"click": f"{row} a.wr-verb", "tap": True, "after": 300},
    until("opened", f"document.getElementById('card-step')?.hasAttribute('data-js-sheet') && {doc}?.querySelector('.hd-opt')", "location.pathname"),
    {"wait": 500}, {"print": f"['look', {LOOK}]"},
    # a note with no pick: the board refuses it, says so on the page, and records nothing
    # (a note shows the review of his answer first, then Send posts it)
    note("why not both?"), tap(".hd-foot .hd-btn.primary", 700), tap(".hd-foot .hd-btn.primary", 1500),
    {"print": f"['refused', {doc}.querySelector('.hd-status').textContent]"}, end("end-refused"),
    {"print": f"['stays', Boolean(document.querySelector('{row}'))]"},
    # back to the question from the review: Only the total, with a note, its review, then Send
    tap(".hd-ritem", 700), note("as the receipts do"), tap(".hd-q.cur .hd-opts > .hd-opt:nth-child(2) .hd-label", 700), tap(".hd-foot .hd-btn.primary", 700),
    {"print": f"['review', {doc}.querySelector('.hd-review.cur .hd-chip')?.textContent ?? '-']"}, tap(".hd-foot .hd-btn.primary", 300),
    until("said", f"{doc}?.querySelector('.hd-done')", f"{doc}?.querySelector('.hd-done')?.textContent ?? '-'"), end("end-taken"),
    until("gone", f"!document.querySelector('{row}')", "[Boolean(document.querySelector('" + row + "')), window.lemStay === 1]")]}))
PY
  drive "$WORK/card-phone.json" "$out"
  if [ "$(seen "$out" row)" = "Round each line of a refund, or only its total?" ] && [[ $(seen "$out" opened) == "/$HOST/shop/tasks/refund-rounding/card/$CARD" ]] \
    && [ "$(fact "$out" look 'd["sheet"], d["position"], d["prompt"], d["options"], d["note"], d["keys"], d["chat"]')" = "(True, 'fixed', 'Round each line of a refund, or only its total?', ['Each line', 'Only the total'], True, 0, 0)" ]; then
    pass "on a phone the row of refund-rounding's card in Waits for you shows its question, and a tap on it opens the same page as in agterm over the whole screen, with Each line, Only the total and the note field, and no key hint or Discuss in chat"
  else
    fail "the card's row and page on a phone: $(cat "$out")"
  fi
  if [ "$(seen "$out" refused)" = "A question goes to the task’s session, at the Mac: nothing was recorded." ] && [ "$(seen "$out" end-refused)" = None ] \
    && [ "$(seen "$out" stays)" = True ]; then
    pass "on a phone a note with no pick on the card is refused: the page says that a question goes to the task's session at the Mac, nothing is recorded, and the row stays"
  else
    fail "a note with no pick on a phone: $(cat "$out")"
  fi
  if [ "$(seen "$out" review)" = "Only the total" ] && [ "$(seen "$out" said)" = "Your answer is on record: the task’s session takes it." ] \
    && [ "$(fact "$out" end-taken 'd[0], d[1], d[2], d[3]["selected"], d[3]["text"]')" = "('answered', 'board', 'phone', ['total'], 'as the receipts do')" ] \
    && [ "$(seen "$out" gone)" = "[False, True]" ]; then
    pass "on a phone Only the total with the note as the receipts do is on record as the owner's answer from the phone, the page says so, and the row leaves Waits for you with no reload"
  else
    fail "the card answered on a phone: $(cat "$out")"
  fi
}

# The park step of gift-note-in-export and the approval of the criteria of stock-on-product-page, which on a phone take
# the confirm step's overlay (lem_board_task.py `confirm_card`, the `sheet` controller, board.css). The criteria of
# stock-on-product-page changed from the owner's note, so their card shows criterion 1's text before beside its new
# text, one under the other on a phone and side by side on a desktop, above Yes and No with a note (criteria 2, 3 and 4
# of criteria-change-asks-again); on a phone of 390 x 844 a No with no note, after the read to the end, is refused on
# the page and posts no act. The gate's checks use 390 x 400, where the text of each goes on below the body's end.
# Last in the block: with no script its checks park the one task and approve the criteria of the other with its Yes. `acted.py LOG TASK ACT` prints whether a board.act of ACT on TASK comes into the log
# within 20 s (serve.py `asked_from` logs it after the act's script ran).
cat > "$WORK/acted.py" <<'PY'
import json, sys, time
log, task, act = sys.argv[1:]
def acted():
    return any(e.get("event") == "board.act" and e.get("task") == task and e.get("act") == act for e in map(json.loads, open(log, encoding="utf-8")))
end = time.time() + 20
while time.time() < end and not acted():
    time.sleep(0.2)
print(json.dumps(["acted", acted()]))
PY
step_checks() {
  local park=gift-note-in-export stock=stock-on-product-page out=$WORK/steps
  "$PY" - "$BASE" "$WORK" "$PY" "$LOG" "$park" "$stock" <<'PY'
import json, shlex, sys
base, work, py, log, park, stock = sys.argv[1:]
PARK, STOCK = f"{base}/tasks/{park}/park?in=waits", f"{base}/tasks/{stock}/criteria?in=waits"
CARD = {"park": "#confirm", "approve": "#approve-card"}
def facts(card):
    """the card's facts: whether the controller marked it, its position, the head's top and words, the button's and Back's
    top and bottom (null when not drawn) and Back's words, the button's aria-disabled and label, the body's scroll, its
    height and its content's, the bottom of the body's text that is drawn, whether it goes on below the body's end, whether
    a part of the card is fixed, the class of what has the focus, and the plain text of the criteria where it is drawn; on a
    page without the parts (the base commit's), the error, so that the print step ends and the check fails"""
    return ("(() => { try { const c = document.querySelector('" + card + "'), body = c.querySelector('.cf-body'), b = c.querySelector('.cf-foot button[type=submit]'), back = c.querySelector('.cf-foot a.btn');"
            " const at = n => n && n.getClientRects().length ? [Math.round(n.getBoundingClientRect().top), Math.round(n.getBoundingClientRect().bottom)] : null;"
            " const end = Math.max(...[...body.children].filter(n => n.getClientRects().length).map(n => n.getBoundingClientRect().bottom)), plain = c.querySelector('pre.cf-plain');"
            " return {sheet: c.hasAttribute('data-js-sheet'), position: getComputedStyle(c).position, head: at(c.querySelector('.cf-head')), headWords: c.querySelector('.cf-head').textContent.replace(/\\s+/g, ' ').trim(),"
            " button: at(b), back: at(back), backWords: back.textContent.trim(), screen: innerHeight, disabled: b.getAttribute('aria-disabled'), label: b.textContent.trim(),"
            " top: Math.round(body.scrollTop), height: body.clientHeight, content: body.scrollHeight, textEnd: Math.round(end), textBelow: end > body.getBoundingClientRect().bottom + 1,"
            " fixed: [c, ...c.querySelectorAll('*')].some(n => ['fixed', 'sticky'].includes(getComputedStyle(n).position)), focus: document.activeElement?.className ?? '-',"
            " plain: plain && plain.getClientRects().length ? plain.textContent.split('\\n')[0] : null }; } catch (e) { return {error: String(e)}; } })()")
def until(label, step, cond):
    """a print step that waits up to 15 s for COND, then gives LABEL and the facts of STEP's card"""
    return {"print": f"new Promise(done => {{ const end = Date.now() + 15000; const tick = () => (({cond}) || Date.now() > end) ? done([{json.dumps(label)}, {facts(CARD[step])}]) : setTimeout(tick, 100); tick(); }})"}
def at(label, step):
    return {"print": f"[{json.dumps(label)}, {facts(CARD[step])}]"}
def sh(*argv):
    return {"sh": " ".join(map(shlex.quote, argv))}
def acts(label):
    return sh(py, "-c", "import json, sys; print(json.dumps([sys.argv[1], sum('\"board.act\"' in line for line in open(sys.argv[2]))]))", label, log)
def open_(step, url):
    # the approval's criteria come from its markdown block, which the browser draws after the page
    return [{"goto": url, "wait": 300}, until(f"{step}-ready", step, f"document.readyState === 'complete' && document.querySelector('{CARD[step]}[data-js-sheet]') && document.querySelector('{CARD[step]} .cf-body').textContent.trim()"), {"wait": 500}]
def to_end(step):
    return {"eval": f"(() => {{ const b = document.querySelector('{CARD[step]} .cf-body'); b.scrollTop = b.scrollHeight; }})()", "after": 500}
def gate(step, url):
    return [*open_(step, url), at(f"{step}-opened", step), acts(f"{step}-acts-before"), {"click": f"{CARD[step]} .cf-foot button[type=submit]"}, {"wait": 700},
            {"print": f"['{step}-tapped', location.pathname + location.search]"}, acts(f"{step}-acts-after"), at(f"{step}-after-tap", step), to_end(step), at(f"{step}-end", step)]
# the two sides of the changed criterion: how many, one under the other with one left edge, side by side on one top,
# each inside the screen, and whether the overlay's body has nothing wider than itself
PAIRS = ("(() => { const s = [...document.querySelectorAll('#approve-card .cf-pair.cf-changed .cf-side')].map(n => n.getBoundingClientRect()), body = document.querySelector('#approve-card .cf-body');"
         " return {sides: s.length, stacked: s.length === 2 && Math.round(s[0].left) === Math.round(s[1].left) && s[1].top >= s[0].bottom - 1,"
         " beside: s.length === 2 && Math.round(s[0].top) === Math.round(s[1].top) && s[1].left >= s[0].right - 1, inside: s.every(r => r.left >= 0 && r.right <= innerWidth),"
         " wide: body.scrollWidth <= body.clientWidth + 1, labels: [...document.querySelectorAll('#approve-card .cf-pair .cf-label')].map(n => n.textContent.trim())}; })()")
def looks(width, height, label, then=(), **more):
    return {"width": width, "height": height, **more, "steps": [*open_("park", PARK), at(f"park-{label}", "park"), *open_("approve", STOCK), at(f"approve-{label}", "approve"),
                                                               {"print": f"['pairs-{label}', {PAIRS}]"}, *then]}
# a No with no note on the phone, after the read to the end: refused on the page, and no act in the log
NOTE_SAID = "document.querySelector('#act-note')?.textContent.replace(/\\s+/g, ' ').trim()"
BARE_NO = [to_end("approve"), acts("no-acts-before"), {"click": "#approve-card .cf-foot button[value=no]"}, {"wait": 700},
           {"print": f"new Promise(done => {{ const end = Date.now() + 15000; const tick = () => (({NOTE_SAID}) || Date.now() > end) ? done(['no-said', {NOTE_SAID} ?? null]) : setTimeout(tick, 100); tick(); }})"},
           acts("no-acts-after")]
specs = {
    "gate": {"width": 390, "height": 400, "mobile": True, "steps": [*gate("park", PARK), *gate("approve", STOCK)]},
    "fit": looks(390, 844, "fit", mobile=True, then=BARE_NO),
    "desk": looks(1440, 900, "desk"),
    # with no script: no controller, so no overlay; each click posts its form, and the act runs
    "noscript": {"width": 390, "height": 844, "mobile": True, "noscript": True, "posts": True, "steps": [
        {"goto": STOCK, "wait": 2500}, at("approve-off", "approve"), {"click": "#approve-card .cf-foot button[type=submit]"}, {"wait": 1500}, sh(py, f"{work}/acted.py", log, stock, "approve"),
        {"goto": PARK, "wait": 2500}, at("park-off", "park"), {"click": "#confirm .cf-foot button[type=submit]"}, {"wait": 1500}, sh(py, f"{work}/acted.py", log, park, "park")]},
}
for name, spec in specs.items():
    with open(f"{work}/steps-{name}.json", "w", encoding="utf-8") as out:
        json.dump(spec, out)
PY
  drive "$WORK/steps-gate.json" "$out-gate.out"
  drive "$WORK/steps-fit.json" "$out-fit.out"
  drive "$WORK/steps-desk.json" "$out-desk.out"
  drive "$WORK/steps-noscript.json" "$out-noscript.out"
  local gate=$out-gate.out
  # gated STEP LABEL: the overlay of STEP opened with its text below the body's end and its button off, a tap posted
  # nothing, and the scroll to the end turned the button on with LABEL
  gated() {
    [ "$(fact "$gate" "$1-opened" 'd["sheet"] and d["position"] == "fixed" and d["head"][0] >= 0 and d["button"][1] <= d["screen"] and d["back"][1] <= d["screen"] and d["textBelow"]')" = True ] \
      && [ "$(fact "$gate" "$1-opened" 'd["disabled"], d["label"], d["backWords"], d["focus"]')" = "('true', 'Read to the end ↓', 'Back', 'cf-head')" ] \
      && [ "$(seen "$gate" "$1-acts-before")" = "$(seen "$gate" "$1-acts-after")" ] && [ "$(seen "$gate" "$1-acts-after")" != "nothing printed" ] \
      && [ "$(fact "$gate" "$1-after-tap" 'd["label"]')" = "Read to the end ↓" ] \
      && [ "$(fact "$gate" "$1-end" 'd["disabled"], d["label"], d["textBelow"]')" = "(None, '$2', False)" ]
  }
  if gated park "Park the task" && [ "$(seen "$gate" park-tapped)" = "/$HOST/shop/tasks/$park/park?in=waits" ] \
    && [ "$(fact "$gate" park-opened 'd["headWords"]')" = "Park · breaker 1" ]; then
    pass "on a phone whose screen the park's text goes on below, Park… on gift-note-in-export opens the overlay with its head, its text and a button that is off and reads Read to the end ↓, a tap on it posts nothing, and after the text is scrolled to its end it reads Park the task and is on"
  else
    fail "the park step's overlay on a phone: $(cat "$gate")"
  fi
  if gated approve "Yes" && [ "$(seen "$gate" approve-tapped)" = "/$HOST/shop/tasks/$stock/criteria?in=waits" ] \
    && [[ "$(fact "$gate" approve-opened 'd["headWords"]')" == "The criteria wait for your yes"* ]]; then
    pass "on a phone whose screen the criteria go on below, the approval of stock-on-product-page opens the overlay with its head, the criteria and a button that is off and reads Read to the end ↓, a tap on it posts nothing, and after the criteria are scrolled to their end it reads Yes and is on"
  else
    fail "the approval's overlay on a phone: $(cat "$gate")"
  fi
  if [ "$(fact "$out-fit.out" park-fit 'd["sheet"], d["position"], d["content"] <= d["height"], d["disabled"], d["label"]')" = "(True, 'fixed', True, None, 'Park the task')" ] \
    && [ "$(fact "$out-fit.out" approve-fit 'd["sheet"], d["position"], d["content"] <= d["height"], d["disabled"], d["label"], d["back"][1] <= d["screen"]')" = "(True, 'fixed', True, None, 'Yes', True)" ]; then
    pass "on a phone of 390 x 844, where the whole text of each fits, the park step and the approval open the overlay with the button on from the first look, the approval's Yes, No and Back in the screen"
  else
    fail "the park step and the approval whose text fits: $(cat "$out-fit.out")"
  fi
  if [ "$(fact "$out-fit.out" pairs-fit 'd["sides"], d["stacked"], d["inside"], d["wide"], d["labels"]')" = "(2, True, True, True, ['Before · criterion 1', 'Now · criterion 1'])" ] \
    && [ "$(fact "$out-desk.out" pairs-desk 'd["sides"], d["beside"], d["inside"]')" = "(2, True, True)" ]; then
    pass "the card of criteria that changed from the owner's note shows criterion 1's text before and its new text, one under the other on a phone of 390 px with nothing wider than the overlay, and side by side on a desktop"
  else
    fail "the text before beside the new: $(seen "$out-fit.out" pairs-fit) / $(seen "$out-desk.out" pairs-desk)"
  fi
  if [ "$(seen "$out-fit.out" no-said)" = "Not done. No needs your words: what should the criteria say? Nothing was recorded." ] \
    && [ "$(seen "$out-fit.out" no-acts-before)" = "$(seen "$out-fit.out" no-acts-after)" ] && [ "$(seen "$out-fit.out" no-acts-after)" != "nothing printed" ]; then
    pass "on a phone, No with no note on the criteria of stock-on-product-page, after the read to the end, is refused on the page with the words it needs, and no act comes into the log"
  else
    fail "a No with no note on a phone: $(seen "$out-fit.out" no-said) / $(seen "$out-fit.out" no-acts-before) / $(seen "$out-fit.out" no-acts-after)"
  fi
  if [ "$(fact "$out-desk.out" park-desk 'd["fixed"], d["disabled"], d["label"], d["button"][0] > d["textEnd"], d["backWords"], d["back"] is not None')" = "(False, None, 'Park the task', True, 'Back', True)" ] \
    && [ "$(fact "$out-desk.out" approve-desk 'd["fixed"], d["disabled"], d["label"], d["button"][0] > d["textEnd"], d["back"]')" = "(False, None, 'Yes', True, None)" ]; then
    pass "on a desktop's screen of 1440 x 900 the park step and the approval have no fixed part and their button is on, below their text in the page, and the approval shows no Back"
  else
    fail "the park step and the approval on a desktop: $(cat "$out-desk.out")"
  fi
  if [ "$(fact "$out-noscript.out" approve-off 'd["sheet"], d["fixed"], d["disabled"], d["plain"], d["textEnd"] < d["button"][0]')" = "(False, False, None, '## Acceptance criteria', True)" ] \
    && grep -qE "^\[\"post\",\"$BASE/tasks/$stock/answer key=criterion%3A$stock%3A[0-9]{8}T[0-9]{6}Z&digest=[0-9a-f]{16}&tab=criteria&in=waits&words=&option=yes\"\]$" "$out-noscript.out" && [ "$(fact "$out-noscript.out" park-off 'd["sheet"], d["fixed"], d["disabled"], d["label"], d["button"][0] > d["textEnd"]')" = "(False, False, None, 'Park the task', True)" ] \
    && grep -qE "^\[\"post\",\"$BASE/tasks/$park/park in=waits&key=breaker%3A$park%3A1%3A[0-9]{8}T[0-9]{6}Z&why=\"\]$" "$out-noscript.out" && [ "$(grep -c '^\["acted", true\]$' "$out-noscript.out")" = 2 ]; then
    pass "with no script on a phone the approval shows the criteria as plain text above its Yes and the park step its text above its button, each button is on, and each click posts its form, the approval's Yes with the key of the criteria's row and the digest, the park's with the key of the breaker's row, and the act runs: the board.act of the approval and of the park come into the log"
  else
    fail "the park step and the approval with no script: $(cat "$out-noscript.out")"
  fi
}

# The arrow that folds the sidebar, in one window whose width changes: at 1200 px a click folds the sidebar to its rail;
# at 700 px the drawer of that folded sidebar shows the arrow, and a click on it gives the drawer the whole sidebar with
# its links; back at 1200 px the sidebar is open with the arrow that folds it. Each print step gives a label and the
# facts: the shell folded, the drawer open, the arrow shown and what it says, and the links of Views shown of all of them.
side_fold_checks() {
  local out=$WORK/fold.out
  "$PY" - "$BASE" > "$WORK/fold.json" <<'PY'
import json, sys
base = sys.argv[1]
FACTS = ("(() => { const shell = document.getElementById('shell'), arrow = document.getElementById('side-fold');"
         " const shown = n => Boolean(n && n.checkVisibility({checkVisibilityCSS: true})); const links = [...document.querySelectorAll('#views a.vbtn')];"
         " return {railed: shell.classList.contains('railed'), drawer: shell.hasAttribute('data-js-drawer'), arrow: shown(arrow),"
         " says: arrow ? arrow.getAttribute('aria-label') : '-', links: links.filter(shown).length, of: links.length}; })()")
def at(label):
    return {"print": f"[{json.dumps(label)}, {FACTS}]"}
steps = [
    {"goto": f"{base}/", "wait": 300},
    {"print": "new Promise(done => { const end = Date.now() + 15000; const tick = () => ((document.readyState === 'complete' && window.Turbo"
              " && document.querySelector('#side-fold')) || Date.now() > end) ? done(['ready', location.pathname]) : setTimeout(tick, 100); tick(); })"},
    {"wait": 300}, at("wide-open"),
    {"click": "#side-fold", "after": 400}, at("wide-folded"),
    {"size": [700, 900]},
    {"click": ".mbar [data-action='drawer#open']", "after": 500}, at("narrow-drawer"),
    {"click": "#side-fold", "after": 500}, at("narrow-unfolded"),
    {"size": [1200, 900]}, at("wide-again"),
]
print(json.dumps({"width": 1200, "height": 900, "steps": steps}))
PY
  drive "$WORK/fold.json" "$out"
  if [ "$(fact "$out" wide-folded "(d['railed'], d['arrow'], d['says'], d['links'])")" = "(True, True, 'Unfold the sidebar', 0)" ] \
    && [ "$(fact "$out" narrow-drawer "(d['railed'], d['drawer'], d['arrow'], d['says'])")" = "(True, True, True, 'Unfold the sidebar')" ] \
    && [ "$(fact "$out" narrow-unfolded "(d['railed'], d['drawer'], d['links'] == d['of'] > 0)")" = "(False, True, True)" ]; then
    pass "a sidebar folded in a window 1200 px wide shows in the drawer of a window 700 px wide the arrow that unfolds it, and a click on it gives the drawer the whole sidebar with its links"
  else
    fail "the folded sidebar in the drawer of a narrow window: $(cat "$out")"
  fi
  if [ "$(fact "$out" wide-open "(d['railed'], d['arrow'], d['says'], d['links'] == d['of'] > 0)")" = "(False, True, 'Fold the sidebar', True)" ] \
    && [ "$(fact "$out" wide-again "(d['railed'], d['arrow'], d['says'], d['links'] == d['of'] > 0)")" = "(False, True, 'Fold the sidebar', True)" ]; then
    pass "in a window 1200 px wide the arrow folds the sidebar, and after the unfold in a narrow window's drawer the sidebar is open there with the arrow that folds it"
  else
    fail "the fold and the unfold in a wide window: $(cat "$out")"
  fi
}

# The start of a task from a backlog item, last in the block since its new task is a card of the Tasks view: a click on
# "Start a task" of export-in-one-query posts the item, and while the server opens its session the task's lines come
# into the log, so the stream sends the page a refresh during the post. The page ends on the new task's page, never
# back on the backlog with the button as it was.
start_checks() {
  local item=export-in-one-query out=$WORK/start.out
  "$PY" - "$BASE" "$item" > "$WORK/start.json" <<'PY'
import json, sys
base, item = sys.argv[1:]
where = ("(() => { const b = document.querySelector('#item-" + item + " button[type=submit]');"
         " return location.pathname + ' | ' + (b ? b.textContent.trim() : '-'); })()")
steps = [
    {"goto": f"{base}/backlog", "wait": 300},
    {"print": "new Promise(done => { const end = Date.now() + 15000; const tick = () => ((document.readyState === 'complete' && window.Turbo"
              f" && document.querySelector('#item-{item}')) || Date.now() > end) ? done(['ready', location.pathname]) : setTimeout(tick, 100); tick(); }})"},
    {"wait": 1000},
    {"eval": f"document.getElementById('item-{item}').open = true", "after": 300},
    {"click": f"#item-{item} button[type=submit]", "after": 100},
    {"print": f"new Promise(done => {{ const end = Date.now() + 15000; const tick = () => (location.pathname.endsWith('/tasks/{item}') || Date.now() > end)"
              f" ? done(['started', {where}]) : setTimeout(tick, 100); tick(); }})"},
]
print(json.dumps({"width": 1440, "height": 900, "steps": steps}))
PY
  drive "$WORK/start.json" "$out"
  if [ "$(seen "$out" started)" = "/$HOST/shop/tasks/$item | -" ] && grep -qxF "open $item --why new" "$WORK/start-calls"; then
    pass "a click on Start a task of a backlog item opens the task's session and ends on the new task's page, also when the stream refreshes the backlog while the post waits for the session"
  else
    fail "the start from a backlog item (where the page ended | its button): $(cat "$out") / session calls: $(cat "$WORK/start-calls" 2>/dev/null || echo none)"
  fi
}

# The line of keys at the foot of the window, last in the block since it adds 24 items to the demo's backlog: on Backlog,
# with more items than the window holds, the line shows before any scroll, between the view and the status line at the
# window's foot, and the last item scrolls into view above it; W, then T, show the line of Waits for you and of Tasks at
# the same place, and Activity's too. Each print step gives a view and "ID TOP BOTTOM STATUS-TOP WINDOW-HEIGHT".
foot_checks() {
  local out=$WORK/foot.out i top
  for i in $(seq -w 1 24); do
    printf -- '---\nworth: later\nadded: 2026-11-23\n---\n\n# Demo item %s of a long backlog\n\nOne of many, so that the list is longer than the window.\n' "$i" > "$DEMO/docs/backlog/long-$i.md"
  done
  "$PY" - "$BASE" > "$WORK/foot.json" <<'PY'
import json, sys
base = sys.argv[1]
FOOT = ("(() => { const n = document.querySelector('.main > .keys'); if (!n) return 'none'; const b = n.getBoundingClientRect();"
        " return [n.id, Math.round(b.top), Math.round(b.bottom), Math.round(document.getElementById('status').getBoundingClientRect().top), innerHeight].join(' '); })()")
def until(label, cond):
    return {"print": f"new Promise(done => {{ const end = Date.now() + 15000; const tick = () => (({cond}) || Date.now() > end) ? done([{json.dumps(label)}, {FOOT}]) : setTimeout(tick, 100); tick(); }})"}
def key(name, code):
    return {"key": name, "code": code, "vk": 0, "after": 100}
VIEW = "document.getElementById('backlog-view')"
steps = [
    {"goto": f"{base}/backlog?read=1", "wait": 300},
    until("backlog", "document.readyState === 'complete' && window.Turbo && document.querySelectorAll('.bl-item').length > 24"),
    {"print": f"['scroll', [{VIEW}.scrollTop, {VIEW}.scrollHeight > {VIEW}.clientHeight].join(' ')]"},
    {"eval": f"{VIEW}.scrollTop = {VIEW}.scrollHeight"},
    {"print": "['last', (() => { const items = document.querySelectorAll('.bl-item'); return [Math.round(items[items.length - 1].getBoundingClientRect().bottom),"
              " Math.round(document.querySelector('.main > .keys').getBoundingClientRect().top)].join(' '); })()]"},
    key("w", "KeyW"), until("waits", "location.pathname.endsWith('/waits') && document.getElementById('waits-keys')"),
    key("t", "KeyT"), until("tasks", "document.getElementById('kanban-keys')"),
    {"goto": f"{base}/activity", "wait": 300}, until("activity", "document.readyState === 'complete' && document.getElementById('activity-keys')"),
]
print(json.dumps({"width": 1440, "height": 900, "steps": steps}))
PY
  drive "$WORK/foot.json" "$out"
  # the line of Backlog sits on the status line, which ends at the window's foot; each other view's at the same place
  top=$(seen "$out" backlog | "$PY" -c 'import sys; p = sys.stdin.read().split()
print(p[1] if len(p) == 5 and p[0] == "backlog-keys" and p[2] == p[3] and int(p[3]) < int(p[4]) < int(p[3]) + 60 else "wrong")')
  if [ "$top" != wrong ] && [ "$(seen "$out" scroll)" = "0 true" ] \
    && seen "$out" last | "$PY" -c 'import sys; a, b = map(int, sys.stdin.read().split()); sys.exit(0 if a <= b else 1)' \
    && [ "$(seen "$out" waits | cut -d' ' -f1,2)" = "waits-keys $top" ] && [ "$(seen "$out" tasks | cut -d' ' -f1,2)" = "kanban-keys $top" ] \
    && [ "$(seen "$out" activity | cut -d' ' -f1,2)" = "activity-keys $top" ]; then
    pass "with more backlog items than the window holds, Backlog's line of keys shows at the window's foot over the status line before any scroll, the last item scrolls into view above it, and W, T and Activity show their line at the same place"
  else
    fail "the line of keys at the window's foot (view: id top bottom status-top window-height): $(cat "$out")"
  fi
}

if [ -z "$NODE" ]; then
  skip_function foot_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
  skip_function tasks_view_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
  skip_function waits_view_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
  skip_function stack_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
  skip_function search_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
  skip_function confirm_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
  skip_function drop_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
  skip_function card_kinds_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
  skip_function card_tune_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
  skip_function card_phone_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
  skip_function step_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
  skip_function side_fold_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
  skip_function start_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
elif [ -z "$CHROME_AT" ]; then
  skip_function foot_checks "no Chrome here (set CHROME to the browser)"
  skip_function tasks_view_checks "no Chrome here (set CHROME to the browser)"
  skip_function waits_view_checks "no Chrome here (set CHROME to the browser)"
  skip_function stack_checks "no Chrome here (set CHROME to the browser)"
  skip_function search_checks "no Chrome here (set CHROME to the browser)"
  skip_function confirm_checks "no Chrome here (set CHROME to the browser)"
  skip_function drop_checks "no Chrome here (set CHROME to the browser)"
  skip_function card_kinds_checks "no Chrome here (set CHROME to the browser)"
  skip_function card_tune_checks "no Chrome here (set CHROME to the browser)"
  skip_function card_phone_checks "no Chrome here (set CHROME to the browser)"
  skip_function step_checks "no Chrome here (set CHROME to the browser)"
  skip_function side_fold_checks "no Chrome here (set CHROME to the browser)"
  skip_function start_checks "no Chrome here (set CHROME to the browser)"
else
  tasks_view_checks
  waits_view_checks
  stack_checks
  search_checks
  confirm_checks
  drop_checks
  card_kinds_checks
  card_tune_checks
  card_phone_checks
  step_checks
  side_fold_checks
  start_checks
  foot_checks
fi

finish
