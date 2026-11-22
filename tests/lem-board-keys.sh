#!/usr/bin/env bash
# The board's keys over its cards and rows, pressed in headless Chrome (tests/board-cdp.mjs, which needs Node) on the
# afternoon of tests/board-showcase.py, served as tests/lem-serve.sh serves it: a server of this run on its own port and
# home folder (tests/lib.sh), with the stand-in for agtermctl of lem-serve.sh first on its PATH. The Tasks view's mark
# (cursor.js): J, K and the arrows in a column, H, L and the arrows to the next column you can see, Enter and Escape,
# the mark through a morph, and no key in a field or with a modifier. The mark of "Waits for you": J, K and the arrows
# over its rows, Enter on a row answered in the task's session (the stand-in's `session select`) and on a merge row (the
# panel, no button), and the mark through a morph. The search over every card (search.js): Cmd-K and Ctrl-K, also from a
# field, and the search buttons open it, letters typed filter and order it, Enter, a click and Escape, and the box through
# a morph. A check adds to the demo's log only the state lines it needs, as a
# lead's `lem project state` and `lem session open` write them. Each check that needs Chrome prints a SKIP line of its
# own where Node or Chrome is missing.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

# A stand-in for agtermctl, first on the PATH of this block and of its server: it prints the tree of AGT_TREE and records
# each call in AGT_CALLS.
FAKE=$WORK/fake
mkdir -p "$FAKE"
cat > "$FAKE/agtermctl" <<'SH'
#!/bin/sh
echo "$*" >> "$AGT_CALLS"
case "$1" in tree) cat "$AGT_TREE" ;; session) [ "$2 $3" = "overlay open" ] && echo "{\"result\": {\"id\": \"NEW\"}}" ;; esac
exit 0
SH
chmod +x "$FAKE/agtermctl"
export PATH="$FAKE:$PATH" AGT_CALLS="$WORK/calls" AGT_TREE="$WORK/tree.json"
DEMO=$("$PY" -B tests/board-showcase.py --demo "$WORK/demo" | field 'd["repo"]')
LOG=$DEMO/.lem/state/events.jsonl
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
import json, sys
from datetime import datetime, timezone
log, task, status, text = sys.argv[1:]
with open(log, "a", encoding="utf-8") as out:
    out.write(json.dumps({"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": "task.state", "task": task, "status": status,
                          "text": text, "lines": [], "ask": text}) + "\n")
PY

# held.py LOG TASK SESSION ASK: a task the owner asked for, its session opened and its interview waiting for him, written
# now at the end of the demo's log
cat > "$WORK/held.py" <<'PY'
import json, sys
from datetime import datetime, timezone
log, task, session, ask = sys.argv[1:]
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
with open(log, "a", encoding="utf-8") as out:
    out.write(json.dumps({"ts": now, "event": "session.open", "task": task, "session": session, "name": task, "phase": "shape", "why": "new", "workspace": "demo"}) + "\n")
    out.write(json.dumps({"ts": now, "event": "task.state", "task": task, "status": "held", "text": "the interview waits for the owner", "lines": [], "ask": ask}) + "\n")
PY

TASKS_KEYS="J K ↑ ↓ move · H L ← → column · Enter open · Esc close"
WAITS_KEYS="J K ↑ ↓ move · Enter go"
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

# The spec of the Tasks view: each print step gives a label and the state, "MARK FOCUS PANEL": the task of the card
# with the mark, of the card whose link has the focus, and of the open panel, each "-" for none.
"$PY" - "$BASE" "$WORK" "$PY" "$LOG" > "$WORK/tasks.json" <<'PY'
import json, shlex, sys
base, work, py, log = sys.argv[1:]
STATE = ("(() => { const cur = document.querySelector('[data-js-cur]'); const focus = document.activeElement?.closest('article.tc');"
         " const panel = document.querySelector('#task > .panel');"
         " return [cur ? cur.dataset.task : '-', focus ? focus.dataset.task : '-', panel ? panel.dataset.task : '-'].join(' '); })()")
def until(label, cond):
    """a print step that waits up to 15 s for COND, then gives LABEL and the state"""
    return {"print": f"new Promise(done => {{ const end = Date.now() + 15000; const tick = () => (({cond}) || Date.now() > end) ? done([{json.dumps(label)}, {STATE}]) : setTimeout(tick, 100); tick(); }})"}
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
    *go(f"{base}/"), event("coupon-has-a-slug", "landed", "main: the change is merged"), until("emptied", "!document.querySelector('#col-checks article.tc')"),
    J, L, J, at("from-empty"),
    {"print": "['nearest', (() => { const mid = n => { const b = n.getBoundingClientRect(); return b.top + b.height / 2; }; const at = mid(document.querySelector('[data-js-cur]'));"
              " return [...document.querySelectorAll('#col-done article.tc')].sort((a, b) => Math.abs(mid(a) - at) - Math.abs(mid(b) - at))[0].dataset.task; })()]"},
    L, at("l-empty"), H, at("h-empty"),
    # the mark through a morph: a new card comes into its column, then the marked card moves to another column
    event("keys-new-task", "building", "task 1 of 2"), until("new-card", "document.querySelector('#col-build #card-keys-new-task')"),
    event("cart-total-after-coupon", "landing", "the checks start"), until("moved", "document.querySelector('#col-checks #card-cart-total-after-coupon')"),
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
    pass "the Tasks view's line of keys shows under the columns on a wide screen and is hidden on a phone"
  else
    fail "the line of keys in Chrome: $(seen "$out" line) / $(cat "$WORK/phone.out")"
  fi
}

# The checks of "Waits for you", after the Tasks view's: a task whose interview waits for the owner, with its session
# open (a demo marks a session live from the log alone), is added first. Each print step gives a label and the state,
# "MARK FOCUS PANEL": the id of the row with the mark, of the row whose link has the focus, and the task of the open
# panel, each "-" for none; a `calls-*` step gives the stand-in agtermctl's calls so far, joined by "|".
waits_view_checks() {
  local out=$WORK/waits.out held=order-search session=0F5EA2C1-0000-4000-8000-0000000000C1 rows first merge select
  "$PY" "$WORK/held.py" "$LOG" "$held" "$session" "Search the orders by customer name"
  rows=$(got "$BASE/waits" | grep -oE '<article class="wrow[^"]*" id="wait-[^"]+"' | sed -E 's/.*id="//; s/"$//' | tr '\n' ' ')
  : > "$AGT_CALLS"
  "$PY" - "$BASE" "$WORK" "$PY" "$LOG" "$AGT_CALLS" "$held" "$rows" > "$WORK/waits.json" <<'PY'
import json, shlex, sys
base, work, py, log, calls, held, ids = sys.argv[1:]
rows = ids.split()
mine, merge = f"wait-held-{held}", next((r for r in rows if r.startswith("wait-merge-")), "")
STATE = ("(() => { const cur = document.querySelector('#waits-list [data-js-cur]'); const focus = document.activeElement?.closest('article.wrow');"
         " const panel = document.querySelector('#task > .panel');"
         " return [cur ? cur.id : '-', focus ? focus.id : '-', panel ? panel.dataset.task : '-'].join(' '); })()")
def until(label, cond):
    """a print step that waits up to 15 s for COND, then gives LABEL and the state"""
    return {"print": f"new Promise(done => {{ const end = Date.now() + 15000; const tick = () => (({cond}) || Date.now() > end) ? done([{json.dumps(label)}, {STATE}]) : setTimeout(tick, 100); tick(); }})"}
def at(label):
    return {"print": f"[{json.dumps(label)}, {STATE}]"}
def where(label):
    return {"print": f"[{json.dumps(label)}, location.pathname + ' ' + (document.querySelector('#confirm') ? 'confirm' : 'no-confirm')]"}
def key(name, code=None):
    vk = {"Enter": 13, "Escape": 27}.get(name, 0)
    return {"key": name, "code": code or name, "vk": vk, "after": 100, **({"text": "\r"} if name == "Enter" else {})}
J, K = key("j", "KeyJ"), key("k", "KeyK")
def moves(src, dst):
    """the J or K presses that take the mark from row SRC to row DST"""
    a, b = rows.index(src), rows.index(dst)
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
    # Enter on a merge row opens the task's panel, and no button of the row is pressed; Escape gives the focus back to it
    *(moves(mine, merge) if merge else []), at("at-merge"), key("Enter"), until("merge-enter", "document.querySelector('#task > .panel')"), where("where-merge"),
    key("Escape"), until("merge-escape", gone), *seen_calls("calls-merge"),
    # the mark through a morph: a new row comes, then the marked row leaves
    *(moves(merge, mine) if merge else []), at("pre-morph"),
    sh(py, f"{work}/event.py", log, "keys-other-wait", "held", "the interview waits for the owner"), until("new-row", "document.querySelector('#wait-held-keys-other-wait')"),
    sh(py, f"{work}/event.py", log, held, "building", "task 1 of 2"), until("row-gone", f"!document.querySelector('#{mine}')"),
    J, at("after-gone"), {"print": "['first', document.querySelector('#waits-list article.wrow')?.id ?? '-']"},
]
print(json.dumps({"width": 1440, "height": 900, "steps": steps}))
PY
  drive "$WORK/waits.json" "$out"
  read -r first _ <<<"$rows"
  merge=$(tr ' ' '\n' <<<"$rows" | grep -m1 '^wait-merge-' || true)
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
    pass "Enter on a marked merge row opens the task's panel and presses none of the row's buttons, and Escape gives the focus back to the marked row"
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
def until(label, cond):
    """a print step that waits up to 15 s for COND, then gives LABEL and the state"""
    return {"print": f"new Promise(done => {{ const end = Date.now() + 15000; const tick = () => (({cond}) || Date.now() > end) ? done([{json.dumps(label)}, {STATE}]) : setTimeout(tick, 100); tick(); }})"}
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
    until("s-morph", "document.querySelector('#card-refund-note-wording') && document.querySelector('#sr-task-refund-note-wording')"),
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

if [ -z "$NODE" ]; then
  skip_function tasks_view_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
  skip_function waits_view_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
  skip_function search_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
elif [ -z "$CHROME_AT" ]; then
  skip_function tasks_view_checks "no Chrome here (set CHROME to the browser)"
  skip_function waits_view_checks "no Chrome here (set CHROME to the browser)"
  skip_function search_checks "no Chrome here (set CHROME to the browser)"
else
  tasks_view_checks
  waits_view_checks
  search_checks
fi

finish
