#!/usr/bin/env bash
# The board's keys over its cards and rows, pressed in headless Chrome (tests/board-cdp.mjs, which needs Node) on the
# afternoon of tests/board-showcase.py, served as tests/lem-serve.sh serves it: a server of this run on its own port and
# home folder (tests/lib.sh), with the stand-in for agtermctl of lem-serve.sh first on its PATH. The Tasks view's mark
# (cursor.js): J, K and the arrows in a column, H, L and the arrows to the next column you can see, Enter and Escape,
# the mark through a morph, and no key in a field or with a modifier. A check adds to the demo's log only the state
# lines it needs, as a lead's `lem project state` writes them. Each check that needs Chrome prints a SKIP line of its
# own where Node or Chrome is missing.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

# A stand-in for agtermctl, first on the PATH of this block and of its server: it prints the tree of AGT_TREE and records
# each call in AGT_CALLS.
FAKE=$WORK/fake
mkdir -p "$FAKE"
# shellcheck disable=SC2016  # the stand-in's own variables, expanded when it runs
printf '%s\n' '#!/bin/sh' 'echo "$*" >> "$AGT_CALLS"' 'case "$1" in tree) cat "$AGT_TREE" ;; session) [ "$2 $3" = "overlay open" ] && echo "{\"result\": {\"id\": \"NEW\"}}" ;; esac' 'exit 0' > "$FAKE/agtermctl"
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

TASKS_KEYS="J K ↑ ↓ move · H L ← → column · Enter open · Esc close"
kanban=$(got "$BASE/")
if words <<<"$kanban" | grep -qF "$TASKS_KEYS" && grep -qF '<div class="keys" id="kanban-keys">' <<<"$kanban" \
  && grep -qF 'data-controller="cursor"' <<<"$kanban"; then
  pass "the Tasks view says its keys in one line of the Backlog's look: $TASKS_KEYS"
else
  fail "the Tasks view's line of keys: $(words <<<"$kanban" | grep -oE '.{0,40}move.{0,80}' || true)"
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

if [ -z "$NODE" ]; then
  skip_function tasks_view_checks "no Node here to drive Chrome (tests/board-cdp.mjs)"
elif [ -z "$CHROME_AT" ]; then
  skip_function tasks_view_checks "no Chrome here (set CHROME to the browser)"
else
  tasks_view_checks
fi

finish
