#!/usr/bin/env bash
# lem-ask: the spec checks, the guards, file-sourced blocks, and every shipped template and demo
# rendering without a runtime error. Opens no overlay and no browser window.
set -eEuo pipefail

cd "$(dirname "$0")/.."
# shellcheck source-path=SCRIPTDIR source=checks.sh
. tests/checks.sh
# lem-ask's module, and Lem's one entry, which runs it as `lem-ask` does: `"$PY" -I -B "$MAIN" lem-ask ARGS...`
B=src/lem/ask.py
MAIN=src/lem/__main__.py
SKILL=skills/lem-ask
WORK=$(mktemp -d)
export XDG_CONFIG_HOME="$WORK/config"  # the owner's status (`lem_state.owner_mark`) of this run, never the home directory's
trap 'stopped; rm -rf "$WORK"' EXIT
# The real interpreter, resolved before HOME moves: a version-manager shim reads its config from HOME.
# Every call below passes -B: importing bin/lem-ask must not leave a __pycache__ in the plugin (and -I
# ignores PYTHONDONTWRITEBYTECODE).
PY=$(python3 -I -c 'import sys; print(sys.executable)')
# The mermaid bundle is fetched once and kept outside the run, in Lem's own cache of the real
# HOME (~/.cache/lem, or $XDG_CACHE_HOME/lem): each run copies it into its private HOME, and a run
# that downloaded it puts it there. lem-ask checks the bundle's sha256 at every read, so a copy is as
# good as a download.
MERMAID_CACHE=${XDG_CACHE_HOME:-$HOME/.cache}/lem
# A private HOME keeps any personal defaults out of the run; agterm is unset so nothing can reach a
# real session. The temporary folder is the run's too, also Chrome's, which on macOS reads
# MAC_CHROMIUM_TMPDIR and not TMPDIR (measured on 2026-11-17): each run of Chrome left a
# com.google.Chrome.* folder in the user's temporary folder.
export HOME="$WORK/home" TMPDIR="$WORK/tmp" MAC_CHROMIUM_TMPDIR="$WORK/tmp"
unset AGTERM_ENABLED AGTERM_SESSION_ID AGTERM_SOCKET CLAUDE_CODE_SESSION_ATTENDED XDG_CACHE_HOME
mkdir -p "$HOME/.cache/lem" "$TMPDIR"
for f in "$MERMAID_CACHE"/mermaid-*.min.js; do
  if [ -f "$f" ]; then cp "$f" "$HOME/.cache/lem/"; fi
done

skipped=0
# The checks of this file: each call of pass in it, but seven of them run once for each item, so
# they count each item: every template and demo rendered, every call of expect (and of bad and
# stub, which call it), of refuses, of check and of card below; and before the pages are loaded,
# each page and each markdown case. A call whose name is a variable is a helper's own, inside its
# definition.
helpers=$(grep -cE '^[[:space:]]*(bad|expect|refuses|check|stub|card) "[^$]' "$SUITE_FILE")
specs=("$SKILL"/templates/*.json "$SKILL"/demos/*.json)
collected "$(($(count_checks "$SUITE_FILE") - 7 + helpers + ${#specs[@]}))"

# expect NAME CODE STATUS -- CMD...: CMD exits CODE and prints JSON whose status is STATUS.
expect() {
  local name=$1 code=$2 status=$3 out got
  shift 4
  set +e
  out=$("$@" 2>/dev/null)
  got=$?
  set -e
  if [ "$got" != "$code" ]; then fail "$name: exit $got, want $code: $out"; return; fi
  if ! printf '%s' "$out" | "$PY" -I -B -c 'import json,sys; sys.exit(json.load(sys.stdin).get("status") != sys.argv[1])' "$status"; then
    fail "$name: status is not $status: $out"; return
  fi
  pass "$name"
}

if "$PY" -I -B -c 'import ast,sys; ast.parse(open(sys.argv[1]).read(), sys.argv[1])' "$B"; then pass "bin/lem-ask parses"; else fail "bin/lem-ask parses"; fi
if [ -x "$B" ]; then pass "bin/lem-ask is executable"; else fail "bin/lem-ask is executable"; fi

# Every template and demo renders.
for f in "${specs[@]}"; do
  n=$(basename "$f" .json)
  if "$PY" -I -B "$MAIN" lem-ask render "$f" -o "$WORK/$n.html" >/dev/null 2>"$WORK/$n.err"; then pass "render $n"; else fail "render $n: $(cat "$WORK/$n.err")"; fi
done
for f in "$HOME"/.cache/lem/mermaid-*.min.js; do
  if [ -f "$f" ] && [ ! -f "$MERMAID_CACHE/${f##*/}" ]; then mkdir -p "$MERMAID_CACHE" && cp "$f" "$MERMAID_CACHE/"; fi
done

# Malformed specs fail with the JSON error contract, never a traceback.
bad() { printf '%s' "$2" > "$WORK/bad.json"; expect "rejects $1" 1 error -- "$PY" -I -B "$MAIN" lem-ask render "$WORK/bad.json" -o "$WORK/bad.html"; }
bad "invalid JSON" 'nope'
bad "a non-object question" '{"questions": ["x"]}'
bad "a non-list options" '{"prompt": "p", "options": "x"}'
bad "a non-object option" '{"prompt": "p", "options": [1]}'
bad "duplicate option ids" '{"prompt": "p", "options": ["a", "a"]}'
bad "duplicate question ids" '{"questions": [{"id": "x", "prompt": "a"}, {"id": "x", "prompt": "b"}]}'
bad "ten options" '{"prompt": "p", "options": ["1","2","3","4","5","6","7","8","9","10"]}'
bad "a missing prompt" '{"options": ["a"]}'
bad "a missing code file" '{"prompt": "p", "context": {"code": {"file": "no/such/file.py"}}}'
bad "a misspelled question key" '{"questions": [{"prompt": "p", "subtitel": "x", "options": ["Yes", "No"]}]}'
bad "a misspelled option key" '{"prompt": "p", "options": [{"label": "Yes", "detial": "x"}]}'
bad "options that only count" '{"prompt": "Approve?", "mode": "multi", "options": ["Criterion 1", "Criterion 2"]}'
bad "a counting label with nothing else" '{"prompt": "p", "options": [{"id": "a", "label": "Option A"}, {"id": "b", "label": "Cache it"}]}'
bad "lines past the end" "{\"prompt\": \"p\", \"context\": {\"code\": {\"file\": \"$PWD/$B\", \"lines\": \"9000-9001\"}}}"
# Every field this script reads itself has its type checked: a wrong one is the error contract, never a traceback.
bad "controls that are not a list" '{"prompt": "p", "controls": 5}'
bad "a control that is not an object" '{"prompt": "p", "controls": ["radius"]}'
bad "a question id that is not a string" '{"questions": [{"id": ["a"], "prompt": "p"}]}'
bad "an option id that is not a string" '{"prompt": "p", "options": [{"id": ["a"], "label": "Cache it"}, "Keep it"]}'
bad "a file that is not a string" '{"prompt": "p", "context": {"code": {"file": 5}}}'
bad "a size that is no percent" '{"prompt": "p", "size": "big"}'
bad "a size past 100" '{"prompt": "p", "size": 150}'
# A field the page shows takes the type the page reads: a label of null showed as the option's id
# ("o1"), and a prompt of 5 showed as "5". Each field a person reads, and each switch the page reads.
bad "an option label that is null" '{"prompt": "p", "options": [{"label": null, "subtitle": "s"}, "Keep it"]}'
bad "an option label that is a number" '{"prompt": "p", "options": [{"label": 5}, "Keep it"]}'
bad "a prompt that is a number" '{"prompt": 5, "options": ["Yes", "No"]}'
bad "a prompt of a question that is a list" '{"questions": [{"prompt": ["p"], "options": ["Yes", "No"]}]}'
bad "a header that is a number" '{"questions": [{"prompt": "p", "header": 3, "options": ["Yes", "No"]}]}'
bad "a hint that is an object" '{"prompt": "p", "hint": {"md": "x"}, "options": ["Yes", "No"]}'
bad "a recommendation that is a number" '{"prompt": "p", "recommendation": 1, "options": ["Yes", "No"]}'
bad "a subtitle that is a list" '{"prompt": "p", "options": [{"label": "Yes", "subtitle": ["s"]}, "No"]}'
bad "a badge that is a number" '{"prompt": "p", "options": [{"label": "Yes", "badge": 1}, "No"]}'
bad "recommended that is a number" '{"prompt": "p", "options": [{"label": "Yes", "recommended": 1}, "No"]}'
bad "tags that are a string" '{"prompt": "p", "options": [{"label": "Yes", "tags": "risky"}, "No"]}'
bad "pros that are a string" '{"prompt": "p", "options": [{"label": "Yes", "pros": "fast"}, "No"]}'
bad "cons with a number in them" '{"prompt": "p", "options": [{"label": "Yes", "cons": ["slow", 2]}, "No"]}'
bad "default that is a string" '{"prompt": "p", "options": [{"label": "Yes", "default": "yes"}, "No"]}'
bad "values that are a list" '{"prompt": "p", "controls": [{"id": "r", "label": "Radius"}], "options": [{"label": "Soft", "values": [1]}]}'
bad "a mode the page does not know" '{"prompt": "p", "mode": "multiple", "options": ["Yes", "No"]}'
bad "a layout the page does not know" '{"prompt": "p", "layout": "table", "options": ["Yes", "No"]}'
bad "optional that is a string" '{"prompt": "p", "optional": "yes", "options": ["Yes", "No"]}'
bad "min that is a string" '{"prompt": "p", "mode": "multi", "min": "2", "options": ["Yes", "No"]}'
bad "text that is a string" '{"prompt": "p", "text": "a note", "options": ["Yes", "No"]}'
bad "a title that is a number" '{"title": 5, "prompt": "p", "options": ["Yes", "No"]}'
bad "a width the page does not know" '{"prompt": "p", "width": "wide", "options": ["Yes", "No"]}'
bad "a control label that is a number" '{"prompt": "p", "controls": [{"id": "r", "label": 5}]}'
bad "a control type the page does not know" '{"prompt": "p", "controls": [{"id": "r", "label": "Radius", "type": "slider"}]}'
bad "a spec that is not UTF-8" $'{"prompt": "caf\xe9?", "options": ["Yes", "No"]}'
printf '{"prompt": "p", "options": ["Yes", "No"]}' > "$WORK/plain.json"
expect "rejects an output in a folder that is not there" 1 error -- "$PY" -I -B "$MAIN" lem-ask render "$WORK/plain.json" -o "$WORK/no/such/folder/x.html"

# The personal defaults are the table [ask] of Lem's home settings file, $XDG_CONFIG_HOME/lem/settings.toml.
# style_of FOLDER: the style of the page rendered with FOLDER as XDG_CONFIG_HOME
style_of() {
  XDG_CONFIG_HOME="$1" "$PY" -I -B "$MAIN" lem-ask render "$WORK/plain.json" -o "$WORK/styled.html" >/dev/null 2>&1 || true
  "$PY" -I -B -c 'import json,re,sys; print(json.loads(re.search(r"id=\"hd-spec\">(.*?)</script>", open(sys.argv[1]).read()).group(1))["style"])' "$WORK/styled.html" 2>/dev/null || true
}
mkdir -p "$WORK/styled/lem" "$HOME/.config/lem-ask"
printf '[ask]\nstyle = "minimal"\n' > "$WORK/styled/lem/settings.toml"
got=$(style_of "$WORK/styled")
if [ "$got" = minimal ]; then pass "a style under [ask] of the home settings file is the style of the next page, in place of refined"
else fail "a style under [ask] of the home settings file is the style of the next page: the page's style is ${got:-none}"; fi
# the file of an older lem-ask, which nothing reads any more
printf '{"style": "bold"}' > "$HOME/.config/lem-ask/defaults.json"
got=$(style_of "$WORK/config")
if [ "$got" = refined ]; then pass "with no [ask], the page is refined, and ~/.config/lem-ask/defaults.json is not read"
else fail "with no [ask], the page is refined, and ~/.config/lem-ask/defaults.json is not read: the page's style is ${got:-none}"; fi
mkdir -p "$WORK/taken/lem"
printf '[ask]\nreview = true\nsize = 90\nbrowser = false\n\n[ask.status]\nasking = ["blocked", "--sound", "default"]\nanswered = ["active"]\n' > "$WORK/taken/lem/settings.toml"
if XDG_CONFIG_HOME="$WORK/taken" "$PY" -I -B "$MAIN" lem-ask render "$WORK/plain.json" -o "$WORK/taken.html" >/dev/null 2>&1 && grep -q '"review": true' "$WORK/taken.html"; then
  pass "an [ask] of every key, with review = true, is taken"
else fail "an [ask] of every key, with review = true, is taken"; fi
# refuses NAME TOML WANT...: lem-ask refuses a home settings file of TOML as an error that names the file and holds each WANT
refuses() {
  local name=$1 out got
  mkdir -p "$WORK/refused/lem"
  printf '%s\n' "$2" > "$WORK/refused/lem/settings.toml"
  shift 2
  set +e
  out=$(XDG_CONFIG_HOME="$WORK/refused" "$PY" -I -B "$MAIN" lem-ask render "$WORK/plain.json" -o "$WORK/plain.html" 2>/dev/null)
  got=$?
  set -e
  if [ "$got" != 1 ]; then fail "$name: exit $got, want 1: $out"; return; fi
  if ! printf '%s' "$out" | "$PY" -I -B -c 'import json,sys; r=json.load(sys.stdin); sys.exit(r.get("status") != "error" or not all(w in r.get("error", "") for w in sys.argv[1:]))' \
      "$WORK/refused/lem/settings.toml" "$@"; then
    fail "$name: the error does not name the file and say $*: $out"; return
  fi
  pass "$name"
}
refuses "refuses a browser under [ask] that is a date, named as TOML writes it" $'[ask]\nbrowser = 2026-11-23' "\`browser\` is true or false, not 2026-11-23"
refuses "refuses a style under [ask] the page does not know" $'[ask]\nstyle = "minmal"' "\`style\` is \"refined\" or \"minimal\" or \"bold\" or \"terminal\", not \"minmal\""
refuses "refuses a review under [ask] the page does not know" $'[ask]\nreview = "sometimes"' "\`review\`" 'not "sometimes"'
refuses "refuses a size under [ask] that is no percent" $'[ask]\nsize = "big"' "\`size\`" 'not "big"'
refuses "refuses a status glyph under [ask] that is not a list" $'[ask.status]\nasking = "blocked"' "\`status.asking\`" 'not "blocked"'
refuses "refuses a misspelled key under [ask]" $'[ask]\nstlye = "bold"' "did you mean \`style\`?"
refuses "refuses an ask that is not a table" 'ask = 5' 'not 5'
refuses "refuses a home settings file that does not read as TOML" '[ask' 'does not read as TOML'
expect "refuses a relative XDG_CONFIG_HOME" 1 error -- env XDG_CONFIG_HOME=config "$PY" -I -B "$MAIN" lem-ask render "$WORK/plain.json" -o "$WORK/plain.html"

# A counting label is fine once the option carries its text, and a key starting with "_" is the author's own.
printf '{"prompt": "Approve?", "_data": 1, "options": [{"label": "Criterion 1", "detail": "The operator approves by hand."}, "Yes"]}' > "$WORK/carried.json"
if "$PY" -I -B "$MAIN" lem-ask render "$WORK/carried.json" -o "$WORK/carried.html" >/dev/null; then pass "a counting label carrying its text passes"; else fail "a counting label carrying its text passes"; fi
# A question's own context is shown on the page (checked in the browser below).
printf '{"questions": [{"id": "a", "prompt": "First?", "context": "QCTX-MARKER-ONE", "options": ["Yes", "No"]}, {"id": "b", "prompt": "Second?", "body": "QCTX-MARKER-TWO", "options": ["Yes", "No"]}]}' > "$WORK/qctx.json"
"$PY" -I -B "$MAIN" lem-ask render "$WORK/qctx.json" -o "$WORK/qctx.html" >/dev/null
# The same with one question: a `questions` list of one keeps that question's context, and a spec that
# is one question shows its context once and its body.
printf '{"questions": [{"id": "a", "prompt": "Only?", "context": "QCTX-MARKER-SOLO", "options": ["Yes", "No"]}]}' > "$WORK/qctx-one.json"
"$PY" -I -B "$MAIN" lem-ask render "$WORK/qctx-one.json" -o "$WORK/qctx-one.html" >/dev/null
printf '{"prompt": "Only?", "context": "QCTX-MARKER-TOP", "body": "QCTX-MARKER-BODY", "options": ["Yes", "No"]}' > "$WORK/qctx-flat.json"
"$PY" -I -B "$MAIN" lem-ask render "$WORK/qctx-flat.json" -o "$WORK/qctx-flat.html" >/dev/null

# Markdown an agent writes by habit, each case a page of its own (checked in the browser below). md-owner
# is the table of /lem init's last page on 2026-11-16, which showed as raw "| | |" and "|---|---|" lines.
MDCASES=$(cat <<'PY'
import json, os, sys
cases = {
    "md-owner": "| | |\n|---|---|\n| Outcome | Lem builds Lem: each change ... |\n| Careful paths | `land.py`, `criteria.py`, ... |",
    "md-header": "| Name | Value |\n| :--- | ---: |\n| a | **b** |",
    "md-pipe-code": "| Op | Note |\n|---|---|\n| `a|b` | x \\| y |",
    "md-no-delim": "a | b | c\nd | e | f",
    "md-hr": "above\n\n---\n\nbelow",
    "md-h4": "#### Deep heading\n##### Deeper",
    "md-nested": "- top\n  - child\n    more of the child\n- next",
    "md-tilde": "~~~\ncode here\n~~~",
    "md-task": "- [ ] open\n- [x] done",
    "md-plus": "+ one\n+ two",
    "md-start": "3. three\n4. four",
    # An md block with a mermaid fence beside a python one: the fence is a chart and the page carries the bundle.
    "md-mermaid": {"md": "```mermaid\nflowchart TD\n  A[\"Start\"] --> B[\"End\"]\n```\n\n```python\nprint(\"py-fence\")\n```"},
}
for name, text in cases.items():
    with open(os.path.join(sys.argv[1], name + ".json"), "w") as f:
        json.dump({"prompt": "p", "context": text, "options": ["Yes", "No"]}, f)
print(" ".join(cases))
PY
)
MDNAMES=$("$PY" -I -B -c "$MDCASES" "$WORK")
for n in $MDNAMES; do
  "$PY" -I -B "$MAIN" lem-ask render "$WORK/$n.json" -o "$WORK/$n.html" >/dev/null 2>"$WORK/$n.err"
done
# The bundle goes into the page of a mermaid fence in markdown, and into no page that has no mermaid.
BUNDLED=$(cat <<'PY'
import glob, sys
bundle = glob.glob(sys.argv[1] + "/mermaid-*.min.js")
if not bundle:
    sys.exit(2)
head = open(bundle[0], encoding="utf-8").read(400)
fence, none = (head in open(f, encoding="utf-8").read() for f in sys.argv[2:4])
print(f"the fence's page carries the bundle: {fence}; the page with no mermaid carries it: {none}")
sys.exit(0 if fence and not none else 1)
PY
)
set +e
why=$("$PY" -I -B -c "$BUNDLED" "$HOME/.cache/lem" "$WORK/md-mermaid.html" "$WORK/md-tilde.html")
got=$?
set -e
if [ "$got" = 0 ]; then pass "a mermaid fence in an md block puts the mermaid bundle on the page, and a page with no mermaid gets none"
elif [ "$got" = 2 ]; then skip "the mermaid bundle of a fence: the mermaid bundle could not be downloaded"
else fail "the mermaid bundle of a fence: $why"; fi
if [ ! -e "$HOME/.cache/lem-ask" ]; then pass "every page so far wrote nothing under ~/.cache/lem-ask/"
else fail "every page so far wrote nothing under ~/.cache/lem-ask/: $(ls -A "$HOME/.cache/lem-ask")"; fi

# A table wider than the window, in a table block, in a key-value block and in markdown, and a grid
# of options whose preview holds a long path with no space in it (checked in the browser below).
WIDE=$(cat <<'PY'
import json, sys
cell = "a cell with a long text that needs room"
md = "| " + " | ".join(f"Column {i}" for i in range(10)) + " |\n|" + "---|" * 10 + "\n| " + " | ".join([cell] * 10) + " |"
path = "skills/lem/scripts/" + "a_very_long_module_name_with_no_space_in_it_" * 4 + ".py"
spec = {"questions": [
    {"id": "t", "prompt": "Wide tables?", "context": [{"table": {"columns": [f"Column {i}" for i in range(10)], "rows": [[cell] * 10]}},
     {"kv": [["key", "/" + "x" * 300]]}, {"md": md}], "options": ["Yes", "No"]},
    {"id": "g", "prompt": "Which file?", "layout": "grid", "columns": 3,
     "options": [{"id": f"o{i}", "label": f"File {i}", "preview": {"md": f"`{path}`"}} for i in range(3)]}]}
json.dump(spec, open(sys.argv[1], "w"))
PY
)
"$PY" -I -B -c "$WIDE" "$WORK/wide.json"
"$PY" -I -B "$MAIN" lem-ask render "$WORK/wide.json" -o "$WORK/wide.html" >/dev/null

# An unattended run never opens anything.
expect "refuses an unattended run" 3 unattended -- env CLAUDE_CODE_SESSION_ATTENDED=0 "$PY" -I -B "$MAIN" lem-ask q "Which?" A B
# Outside agterm it opens nothing unless the browser is asked for: the agent runs lem-ask without checking first.
expect "exit 3 outside agterm" 3 no-agterm -- "$PY" -I -B "$MAIN" lem-ask q "Which?" A B

# {"file": …} blocks carry the file's own lines, numbered, under the path.
printf 'a\nb\nc\nd\n' > "$WORK/src.py"
printf '{"prompt": "p", "context": {"code": {"file": "src.py", "lines": "2-3"}}, "options": ["a"]}' > "$WORK/file.json"
"$PY" -I -B "$MAIN" lem-ask render "$WORK/file.json" -o "$WORK/file.html" >/dev/null
if "$PY" -I -B - "$WORK/file.html" <<'PY'
import json, re, sys
html = open(sys.argv[1], encoding="utf-8").read()
spec = json.loads(re.search(r'id="hd-spec">(.*?)</script>', html, re.S).group(1).replace("<\\/", "</"))
c = spec["context"]
sys.exit(not (c["code"] == "b\nc" and c["start"] == 2 and c["title"] == "src.py:2-3" and c["lang"] == "py"))
PY
then pass "code from a file"; else fail "code from a file"; fi

# `q` reads "*Label|subtitle|why".
if "$PY" -I -B - "$B" <<'PY'
import argparse, importlib.machinery, importlib.util, sys
sys.path.insert(0, sys.argv[1].rsplit("/lem/", 1)[0])  # src, the folder of Lem's package, which lem-ask imports from
loader = importlib.machinery.SourceFileLoader("lem-ask", sys.argv[1])
mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("lem-ask", loader))
loader.exec_module(mod)
a = argparse.Namespace(prompt="Which?", options=["*Redis|runs already|no new service", "PG|one table", "*JWT"],
                       multi=False, context=None, title=None)
o = mod.quick_spec(a)["options"]
sys.exit(not (o[0]["recommended"] == "no new service" and o[0]["subtitle"] == "runs already"
              and "recommended" not in o[1] and o[2]["recommended"] is True))
PY
then pass "q option syntax"; else fail "q option syntax"; fi

# The agterm paths, with agtermctl stubbed: an agterm error ends a wait at once instead of after
# the full timeout, and an occupied overlay slot is exit 5, naming the page when it is a question page.
stub() {
  local name=$1 code=$2 status=$3
  shift 3
  expect "$name" "$code" "$status" -- "$PY" -I -B -c "$STUB" "$B" "$@"
}
STUB=$(cat <<'PY'
import importlib.machinery, importlib.util, json, os, sys, types
sys.path.insert(0, sys.argv[1].rsplit("/lem/", 1)[0])  # src, the folder of Lem's package, which lem-ask imports from
loader = importlib.machinery.SourceFileLoader("lem-ask", sys.argv[1])
mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("lem-ask", loader))
loader.exec_module(mod)
scenario = sys.argv[2]
os.environ.update(AGTERM_SESSION_ID="S1", AGTERM_ENABLED="1")
os.environ.pop("AGTERM_WINDOW_ID", None)
mod.time.sleep = lambda s: None
calls = []
def reply(stdout, code=0):
    return types.SimpleNamespace(stdout=stdout, stderr="", returncode=code)
def outcome(o):
    return reply(json.dumps({"ok": True, "result": {"pageOutcome": {"pageID": "P1", "outcome": o, "value": json.dumps({"status": "answered", "answers": {}})}}}))
def tree(file):
    return reply(json.dumps({"ok": True, "result": {"tree": {"workspaces": [{"sessions": [
        {"id": "S1", "htmlOverlays": [{"file": file, "id": "P0"}]}]}]}}}))
def ctl(*args, check=True):
    calls.append(args)
    if scenario == "invalid":
        return reply('{"ok":false,"error":"invalid page id"}', 1)
    if scenario == "silent":
        if len(calls) > 5:
            sys.exit(9)  # still polling: the wait never gave up
        return reply("")
    if scenario == "answered":
        return outcome("pending") if len(calls) < 3 else outcome("submitted")
    if scenario == "dismissed":
        return outcome("dismissed")
    if args[0] == "tree":
        return tree(os.path.join(mod.OUTDIR, "x.html") if scenario in ("busy-own", "close-own", "close-named", "close-refused") else "/elsewhere/review.html")
    if args[:3] == ("session", "overlay", "close"):
        if scenario == "close-refused":
            return reply('{"ok":false,"error":"no overlay is open"}', 1)
        if scenario != "close-own" or args[args.index("--target") + 1] != "S1":
            sys.exit(7)  # it closed an overlay that is not this session's own question page
        return reply('{"ok":true}')
    return reply('{"ok":false,"error":"overlay already open"}', 1)
mod.ctl = ctl
if scenario.startswith("close"):
    mod.agtermctl = lambda: "/usr/bin/true"  # in_agterm() also wants the binary; CI runners have none
    mod.close_page("P9" if scenario == "close-named" else None)
    sys.exit(8)  # close_page returned instead of exiting
if scenario.startswith("busy"):
    a = types.SimpleNamespace(follow=False, size=None, full=False, chromeless=False)
    mod.open_overlay("/x.html", a, {"prompt": "p"})
    sys.exit(8)  # open_overlay returned instead of exiting
sys.exit(mod.wait_page("P1", 30, status=False))
PY
)
stub "wait stops on an agterm error" 1 error invalid
stub "wait stops when agterm goes silent" 1 error silent
stub "wait returns the answer" 0 answered answered
stub "wait reports a dismissal" 2 dismissed dismissed
stub "busy names a pending question page" 5 busy busy-own
stub "busy with another tool's overlay" 5 busy busy-other
# close: a card whose answer came from the owner's inbox closes, and only a question page of lem-ask's own
# on this session; another tool's overlay, or another question than the one named, is left up (exit 7 if not).
stub "close closes this session's own question page" 0 closed close-own
stub "close leaves another tool's overlay up" 0 gone close-other
stub "close leaves up a question other than the one named" 0 gone close-named
stub "close says so when agterm refuses" 1 error close-refused
expect "close outside agterm closes nothing" 3 error -- "$PY" -I -B "$MAIN" lem-ask close
own=$("$PY" -I -B -c "$STUB" "$B" busy-own 2>/dev/null || true)  # exit 5 is the point; read what it printed
other=$("$PY" -I -B -c "$STUB" "$B" busy-other 2>/dev/null || true)
if printf '%s' "$own" | "$PY" -I -B -c 'import json,sys; sys.exit(json.load(sys.stdin).get("pageID") != "P0")' \
  && printf '%s' "$other" | "$PY" -I -B -c 'import json,sys; sys.exit("pageID" in json.load(sys.stdin))'; then
  pass "busy carries the page id only for a question page"
else
  fail "busy carries the page id only for a question page"
fi

# A card of a task's session (LEM_TASK), with agtermctl stubbed, in a throwaway repository of its own for
# each scenario that has the task's folder: the card kept there, and its one end (lem_cards.end) from the
# session or from the board, of which the first one recorded counts. The board's answer is written the way
# the board's server writes it, by lem_cards.end, while the card's own lem-ask waits.
CARDS=$(cat <<'PY'
import contextlib, glob, importlib.machinery, importlib.util, io, json, os, subprocess, sys, types
from pathlib import Path
sys.path.insert(0, sys.argv[1].rsplit("/lem/", 1)[0])  # src, the folder of Lem's package, which lem-ask imports from
loader = importlib.machinery.SourceFileLoader("lem-ask", sys.argv[1])
mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("lem-ask", loader))
loader.exec_module(mod)
scenario = sys.argv[2]
repo = Path(sys.argv[3]) / scenario
task = repo / ".lem" / "state" / "tasks" / "export-notes"
task.mkdir(parents=True)
subprocess.run(["git", "init", "-q", str(repo)], check=True)
os.chdir(repo)
os.environ.update(AGTERM_SESSION_ID="S1", AGTERM_ENABLED="1", LEM_TASK="export-notes")
os.environ.pop("AGTERM_WINDOW_ID", None)
if scenario == "no-task":
    del os.environ["LEM_TASK"]
if scenario == "other-task":
    os.environ["LEM_TASK"] = "import-notes"
mod.time.sleep = lambda s: None
mod.agtermctl = lambda: "/usr/bin/true"  # in_agterm() also wants the binary; CI runners have none
cards = mod.lem_cards()
SPEC = {"prompt": "Keep the empty cell?", "options": [{"id": "a", "label": "yes"}, {"id": "b", "label": "no, write a dash"}]}
def answer(oid, label, note=None):
    one = {"selected": [oid], "labels": [label]}
    if note:
        one["text"] = note
    return {"status": "answered", "answers": {"answer": one}}
A, B = answer("a", "yes"), answer("b", "no, write a dash", "a dash, as in the invoice export")
def board():
    return cards.end(task, "P1", "answered", "board", B, via="door", device="phone", agent="Mozilla/5.0 (iPhone)")
calls, polls, shown = [], [0], [True]
def reply(stdout, code=0):
    return types.SimpleNamespace(stdout=stdout, stderr="", returncode=code)
def outcome(o, value=None):
    found = {"pageID": "P1", "outcome": o}
    if value is not None:
        found["value"] = json.dumps(value)
    return reply(json.dumps({"ok": True, "result": {"pageOutcome": found}}))
def result(n):
    if scenario in ("ask-keeps", "no-task", "other-task"):
        return outcome("submitted", B) if n >= 3 else outcome("pending")
    if scenario == "board" and n == 2:
        board()  # the owner taps B on his phone while the card's own lem-ask waits
    if scenario == "both" and n == 2:
        board()  # the board records B first, and then the waiter reads the owner's A, picked at the Mac
        return outcome("submitted", A)
    if scenario == "dismissed":
        return outcome("dismissed")
    return outcome("pending")
def ctl(*args, check=True):
    calls.append(list(args))
    if args[:3] == ("session", "overlay", "open"):
        return reply(json.dumps({"ok": True, "result": {"pageID": "P1"}}))
    if args[0] == "tree":
        overlays = [{"file": os.path.join(mod.OUTDIR, "x.html"), "id": "P1"}] if shown[0] else []
        return reply(json.dumps({"ok": True, "result": {"tree": {"workspaces": [{"sessions": [{"id": "S1", "htmlOverlays": overlays}]}]}}}))
    if args[:3] == ("session", "overlay", "close"):
        if args[args.index("--target") + 1] != "S1":
            sys.exit(7)  # it closed an overlay of another session
        shown[0] = False
        return reply('{"ok":true}')
    if args[:3] == ("session", "overlay", "result"):
        polls[0] += 1
        return result(polls[0])
    sys.exit(6)  # a call of agtermctl no scenario expects
mod.ctl = ctl
a = types.SimpleNamespace(browser=False, no_wait=False, style=None, review=None, timeout=2, no_status=True,
                          follow=False, size=None, full=False, chromeless=False)
printed = io.StringIO()
with contextlib.redirect_stdout(printed):
    try:
        if scenario in ("wait-board", "close-wins", "close-loses"):
            cards.keep(task, "P1", b"<p>the card</p>", SPEC, "S1")
            if scenario != "close-wins":
                board()
            code = mod.close_page() if scenario.startswith("close") else mod.wait_page("P1", 2, status=False, card=mod.card_of("P1"))
        else:
            code = mod.ask(json.loads(json.dumps(SPEC)), a, str(repo))
    except SystemExit as stop:
        code = stop.code
lines = [line for line in printed.getvalue().splitlines() if line.strip()]
try:
    out = json.loads(printed.getvalue())
except ValueError:
    out = json.loads(lines[-1]) if lines else None
kept = sorted(p.name for p in (task / "cards").iterdir()) if (task / "cards").is_dir() else []
log = repo / ".lem" / "state" / "events.jsonl"
events = [json.loads(line) for line in log.read_text().splitlines()] if log.is_file() else []
pages = sorted(glob.glob(os.path.join(mod.OUTDIR, "*.html")), key=os.path.getmtime)
same = bool(pages) and (task / "cards" / "P1.html").is_file() and open(pages[-1], "rb").read() == (task / "cards" / "P1.html").read_bytes()
print(json.dumps({"code": code, "out": out, "calls": calls, "polls": polls[0], "kept": kept, "events": events, "html_same": same,
                  "card": cards.card(task, "P1") if (task / "cards").is_dir() else None,
                  "end": cards.ended(task, "P1") if (task / "cards").is_dir() else None}))
PY
)
card() {  # card NAME SCENARIO PYTHON-EXPR-ON-r
  local got
  got=$("$PY" -I -B -c "$CARDS" "$B" "$2" "$WORK/cards" 2>"$WORK/card-$2.err" | tail -1 || true)
  if printf '%s' "$got" | "$PY" -I -B -c "import json,sys; r=json.load(sys.stdin); sys.exit(not ($3))" 2>/dev/null; then pass "$1"; else fail "$1: $got $(cat "$WORK/card-$2.err")"; fi
}
mkdir -p "$WORK/cards"
card "a card of a task's session is kept in the task's folder: the page's own bytes, its questions and options, and card.asked; a pick in the session ends it from the session" ask-keeps \
  'r["code"] == 0 and r["out"]["from"] == "session" and r["html_same"] and r["card"]["page"] == "P1" and r["card"]["session"] == "S1"
   and r["card"]["chat"] is True and [q["id"] for q in r["card"]["questions"]] == ["answer"]
   and [(o["id"], o["label"]) for o in r["card"]["questions"][0]["options"]] == [("a", "yes"), ("b", "no, write a dash")]
   and r["end"]["status"] == "answered" and r["end"]["from"] == "session" and r["end"]["answer"]["answers"]["answer"]["selected"] == ["b"]
   and [(e["event"], e["page"]) for e in r["events"]] == [("card.asked", "P1"), ("card.answered", "P1")] and r["events"][0]["prompt"] == "Keep the empty cell?"'
card "a run outside a task keeps no card and ends as today" no-task \
  'r["code"] == 0 and "from" not in r["out"] and r["out"]["answers"]["answer"]["selected"] == ["b"] and r["kept"] == [] and r["events"] == []'
card "a run whose task has no folder in the repository keeps no card" other-task \
  'r["code"] == 0 and "from" not in r["out"] and r["kept"] == [] and r["events"] == []'
card "the board's answer ends the waiting card: lem-ask closes its own page and prints B and the note, from the board, via and device" board \
  'r["code"] == 0 and r["out"]["from"] == "board" and r["out"]["via"] == "door" and r["out"]["device"] == "phone"
   and r["out"]["answers"]["answer"] == {"selected": ["b"], "labels": ["no, write a dash"], "text": "a dash, as in the invoice export"}
   and ["session", "overlay", "close", "--target", "S1", "--json"] in r["calls"]
   and not any(c[:3] == ["session", "overlay", "submit"] for c in r["calls"])
   and [(e["event"], e.get("from")) for e in r["events"]] == [("card.asked", None), ("card.answered", "board")]'
card "two answers before the session reads either: the board's, recorded first, counts, and said names both" both \
  'r["code"] == 0 and r["out"]["from"] == "board" and r["out"]["answers"]["answer"]["selected"] == ["b"]
   and "on the board" in r["out"]["said"] and "yes on the card in the session was not taken" in r["out"]["said"]
   and r["end"]["from"] == "board" and [e["event"] for e in r["events"]].count("card.answered") == 1'
card "a wait after an exit 4 finds the board's answer at its first poll" wait-board \
  'r["code"] == 0 and r["out"]["from"] == "board" and r["out"]["answers"]["answer"]["selected"] == ["b"] and r["polls"] == 1'
card "a dismissal in the session ends the card as dismissed, and logs card.closed" dismissed \
  'r["code"] == 2 and r["out"]["status"] == "dismissed" and r["end"]["status"] == "dismissed" and r["end"]["from"] == "session"
   and r["events"][-1]["event"] == "card.closed" and r["events"][-1]["status"] == "dismissed"'
card "lem-ask close ends the card as closed before it closes the page" close-wins \
  'r["code"] == 0 and r["out"]["status"] == "closed" and r["end"]["status"] == "closed" and r["end"]["from"] == "session"
   and r["events"][-1]["event"] == "card.closed" and ["session", "overlay", "close", "--target", "S1", "--json"] in r["calls"]'
card "lem-ask close after the board's answer is not taken: the page closes, and the output is the board's answer" close-loses \
  'r["code"] == 0 and r["out"]["status"] == "answered" and r["out"]["from"] == "board" and "close in the session came after it" in r["out"]["said"]
   and r["end"]["from"] == "board" and ["session", "overlay", "close", "--target", "S1", "--json"] in r["calls"]'

# The asking glyph against status hooks. The plugin's async Stop hook acts only when a question page is open,
# re-posts the asking status (with --auto-reset) whenever another hook posted over it, and stops once the
# page is gone. Its hooks.json guard keeps Python out of sessions outside agterm and machines without it.
# A timed-out wait leaves a glyph that a visit clears.
GLYPH=$(cat <<'PY'
import importlib.machinery, importlib.util, json, os, sys, types
sys.path.insert(0, sys.argv[1].rsplit("/lem/", 1)[0])  # src, the folder of Lem's package, which lem-ask imports from
loader = importlib.machinery.SourceFileLoader("lem-ask", sys.argv[1])
mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("lem-ask", loader))
loader.exec_module(mod)
scenario = sys.argv[2]
os.environ.update(AGTERM_SESSION_ID="S1", AGTERM_ENABLED="1")
for k in ("AGTERM_WINDOW_ID", "AGTERM_PANE_ID", "CLAUDE_CODE_SESSION_ATTENDED"):
    os.environ.pop(k, None)
now = [1000.0]
mod.time.time = lambda: now[0]
mod.time.sleep = lambda s: now.__setitem__(0, now[0] + s)
glyph = {"status": "blocked" if scenario == "already" else "active", "changed": now[0]}
page = {"open": scenario != "nopage"}
posts, looks = [], []
def reply(stdout, code=0):
    return types.SimpleNamespace(stdout=stdout, stderr="", returncode=code)
def ctl(*args, check=True):
    if args[:2] == ("session", "status"):
        posts.append(list(args[2:]))
        glyph.update(status=args[2], changed=now[0])
        return reply("ok")
    if args[0] == "tree":
        looks.append(now[0])
        if scenario == "race" and now[0] >= 1001 and not glyph.get("raced"):  # a slower Stop hook posts at t=1001
            glyph.update(status="active", changed=1001.0, raced=True)
        if scenario == "answered" and now[0] >= 1000.4:
            page["open"] = False
        overlays = [{"file": os.path.join(mod.OUTDIR, "x.html"), "id": "P1"}] if page["open"] else []
        return reply(json.dumps({"ok": True, "result": {"tree": {"workspaces": [{"sessions": [
            {"id": "S1", "status": glyph["status"], "statusChangedAt": glyph["changed"], "htmlOverlays": overlays}]}]}}}))
    return reply(json.dumps({"ok": True, "result": {"pageOutcome": {"pageID": "P1", "outcome": "pending"}}}))
mod.ctl = ctl
mod.agtermctl = lambda: "/usr/bin/true"  # in_agterm() also wants the binary; CI runners have none
mod.defaults = lambda: {}
mod.sys.stdin = types.SimpleNamespace(isatty=lambda: False, read=lambda: "{}")
if scenario == "timeout":
    code = mod.wait_page("P1", 60, status=True)
else:
    code = mod.hook_stop()
print(json.dumps({"code": code, "posts": posts, "looks": len(looks)}))
PY
)
glyph() { "$PY" -I -B -c "$GLYPH" "$B" "$1" 2>/dev/null | tail -1 || true; }
check() {  # check NAME SCENARIO PYTHON-EXPR-ON-r
  local got
  got=$(glyph "$2")
  if printf '%s' "$got" | "$PY" -I -B -c "import json,sys; r=json.load(sys.stdin); sys.exit(not ($3))"; then pass "$1"; else fail "$1: $got"; fi
}
check "Stop hook re-posts the question after a slower hook paints over it" race \
  '[p[:2] for p in r["posts"]] == [["blocked", "--auto-reset"], ["blocked", "--auto-reset"]]'
check "Stop hook stops once the page is answered" answered 'r["posts"] == [] and r["looks"] == 2'
check "Stop hook leaves an asking glyph alone" already 'r["posts"] == [] and r["looks"] == 5'
check "Stop hook does nothing without a question page" nopage 'r["posts"] == [] and r["looks"] == 1'
check "a timed-out question leaves a glyph that a visit clears" timeout \
  'r["code"] == 4 and r["posts"][-1][:2] == ["blocked", "--auto-reset"]'
nohook=$(env -u AGTERM_ENABLED "$PY" -I -B "$MAIN" lem-ask hook-stop < /dev/null; echo "rc=$?")
if [ "$nohook" = "rc=0" ]; then pass "Stop hook is silent and exits 0 outside agterm"; else fail "Stop hook outside agterm: $nohook"; fi
# The hooks.json command itself, run the way Claude Code runs a command with no args: through a shell.
HOOKCMD=$("$PY" -I -B -c 'import json,sys; print(json.load(open(sys.argv[1]))["hooks"]["Stop"][0]["hooks"][0]["command"])' skills/lem-ask/hooks/hooks.json)
# A stand-in for bin/lem-ask that leaves a mark and exits 9: lem-ask itself is silent outside agterm, so only
# the guard keeps the stand-in from running, and a run with a session and a python3 shows that it can run.
FAKE=$WORK/fake-plugin
mkdir -p "$FAKE/bin" && printf '#!/bin/sh\n: > "%s/ran"\nexit 9\n' "$FAKE" > "$FAKE/bin/lem-ask" && chmod +x "$FAKE/bin/lem-ask"
guard1=$(env -u AGTERM_SESSION_ID CLAUDE_PLUGIN_ROOT="$FAKE" sh -c "$HOOKCMD" < /dev/null 2>&1; echo "rc=$?")
guard2=$(env AGTERM_SESSION_ID=S1 PATH=/nonexistent CLAUDE_PLUGIN_ROOT="$FAKE" /bin/sh -c "$HOOKCMD" < /dev/null 2>&1; echo "rc=$?")
ran_before=$([ -e "$FAKE/ran" ] && echo yes || echo no)
guard3=$(env AGTERM_SESSION_ID=S1 CLAUDE_PLUGIN_ROOT="$FAKE" sh -c "$HOOKCMD" < /dev/null 2>&1; echo "rc=$?")
if [ "$guard1" = "rc=0" ] && [ "$guard2" = "rc=0" ] && [ "$ran_before" = no ] && [ "$guard3" = "rc=9" ] && [ -e "$FAKE/ran" ]; then
  pass "hooks.json guard: silent exit 0 with no agterm session, and with no python3"
else
  fail "hooks.json guard: no session [$guard1], no python3 [$guard2], ran before a session [$ran_before], with a session [$guard3]"
fi

# A whole file in a code block is capped; past the cap the spec has to name its lines.
"$PY" -I -B -c 'print("\n".join(f"x = {i}" for i in range(400)))' > "$WORK/long.py"
bad "a whole long file as code" "{\"prompt\": \"p\", \"context\": {\"code\": {\"file\": \"$WORK/long.py\"}}}"

# The runtime parses, and every rendered page loads with no error node and every diagram drawn.
if command -v node >/dev/null; then
  if node --check "$SKILL/runtime/ask.js"; then pass "ask.js parses"; else fail "ask.js parses"; fi
else
  skip "ask.js parses: node is not installed"
fi
DOMCHECK=$(cat <<'PY'
import sys
from html.parser import HTMLParser
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.script = 0; self.app = False; self.errors = 0; self.mermaid = 0; self.failed = 0; self.drawn = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); cls = (a.get("class") or "").split()
        self.script += tag == "script"
        if self.script:
            return
        self.app |= "hd" in cls
        self.errors += "hd-err" in cls
        self.mermaid += "hd-mermaid" in cls
        self.failed += "hd-mermaid" in cls and "err" in cls
        self.drawn += tag == "svg" and (a.get("id") or "").startswith("hd-mm-")
    def handle_endtag(self, tag):
        self.script -= tag == "script"
p = P(); p.feed(open(sys.argv[1], encoding="utf-8").read())
problems = []
if not p.app: problems.append("no app root")
if p.errors: problems.append(f"{p.errors} .hd-err node(s)")
if sys.argv[2] == "required" and (p.failed or p.drawn != p.mermaid):
    problems.append(f"{p.drawn} of {p.mermaid} diagram(s) drawn")
print("; ".join(problems))
sys.exit(bool(problems))
PY
)
# PROBE PAGE COPY: COPY is PAGE with a script that measures, at each of its two questions, the
# page's width against its window and each preview of the current question against its card.
PROBE=$(cat <<'PY'
import sys
page = open(sys.argv[1], encoding="utf-8").read()
probe = """<script>setTimeout(() => {
  const d = document.documentElement, out = {};
  const look = () => ({page: [d.scrollWidth, d.clientWidth], prev: [...document.querySelectorAll(".hd-q.cur .hd-prev")].map(n => [n.scrollWidth, n.clientWidth])});
  out.tables = look();
  [...document.querySelectorAll(".hd-q")].forEach((q, i) => q.classList.toggle("cur", i === 1));
  setTimeout(() => { out.grid = look(); d.setAttribute("data-measure", JSON.stringify(out)); }, 300);
}, 1500);</script>"""
open(sys.argv[2], "w", encoding="utf-8").write(page.replace("</body>", probe + "</body>", 1))
PY
)
MEASURED=$(cat <<'PY'
import html, json, re, sys
found = re.search(r'data-measure="([^"]*)"', open(sys.argv[1], encoding="utf-8").read())
if not found:
    sys.exit("the probe wrote nothing")
m = json.loads(html.unescape(found.group(1)))
wrong = [f"the page of the {k} is {m[k]['page'][0]} px wide in a window of {m[k]['page'][1]}" for k in ("tables", "grid") if m[k]["page"][0] > m[k]["page"][1]]
wrong += [f"a preview of the grid is {w} px wide in a card of {c}" for w, c in m["grid"]["prev"] if w > c]
wrong += [] if len(m["grid"]["prev"]) == 3 else [f"the grid has {len(m['grid']['prev'])} previews, not 3"]
print("; ".join(wrong))
sys.exit(bool(wrong))
PY
)
chrome=""
for c in google-chrome chromium chromium-browser "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
  if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then chrome=$c; break; fi
done
pages=()
for f in "$WORK"/*.html; do
  case $(basename "$f" .html) in bad) ;; *) pages+=("$f") ;; esac
done
read -ra mdnames <<<"$MDNAMES"
collected "$((${#pages[@]} + ${#mdnames[@]}))"
if [ -n "$chrome" ]; then
  for f in "${pages[@]}"; do
    n=$(basename "$f" .html)
    # No network means no mermaid bundle, and diagrams show as source by design: say so, don't pass it.
    diagrams=required
    if grep -q 'mermaid unavailable' "$WORK/$n.err" 2>/dev/null; then
      diagrams=skip
      skipped=$((skipped + 1))
    fi
    "$chrome" --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" \
      --virtual-time-budget=4000 --dump-dom "file://$f" > "$WORK/$n.dom" 2>/dev/null || true
    if ! why=$("$PY" -I -B -c "$DOMCHECK" "$WORK/$n.dom" "$diagrams"); then
      fail "page loads: $n ($why)"
    elif [ "$diagrams" = skip ]; then
      skip "page loads: $n: the mermaid bundle could not be downloaded, so its diagrams were not checked"
    else
      pass "page loads: $n"
    fi
  done
  if "$PY" -I -B - "$WORK/qctx.dom" <<'PY'
import sys
from html.parser import HTMLParser
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.script = 0; self.text = []
    def handle_starttag(self, tag, attrs):
        self.script += tag == "script"
    def handle_endtag(self, tag):
        self.script -= tag == "script"
    def handle_data(self, data):
        if not self.script:
            self.text.append(data)
p = P(); p.feed(open(sys.argv[1], encoding="utf-8").read())
shown = " ".join(p.text)
sys.exit(not ("QCTX-MARKER-ONE" in shown and "QCTX-MARKER-TWO" in shown))
PY
  then pass "a question's own context and body are shown"; else fail "a question's own context and body are shown"; fi
  # VISIBLE DOM MARKER=COUNT...: each marker stands that many times in the page's visible text.
  VISIBLE=$(cat <<'PY'
import sys
from html.parser import HTMLParser
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.script = 0; self.text = []
    def handle_starttag(self, tag, attrs):
        self.script += tag == "script"
    def handle_endtag(self, tag):
        self.script -= tag == "script"
    def handle_data(self, data):
        if not self.script:
            self.text.append(data)
p = P(); p.feed(open(sys.argv[1], encoding="utf-8").read())
shown = " ".join(p.text)
wrong = [f"{m} stands {shown.count(m)} times, not {n}" for m, _, n in (w.partition("=") for w in sys.argv[2:]) if shown.count(m) != int(n)]
print("; ".join(wrong))
sys.exit(bool(wrong))
PY
)
  if why=$("$PY" -I -B -c "$VISIBLE" "$WORK/qctx-one.dom" "QCTX-MARKER-SOLO=1") \
    && why=$("$PY" -I -B -c "$VISIBLE" "$WORK/qctx-flat.dom" "QCTX-MARKER-TOP=1" "QCTX-MARKER-BODY=1"); then
    pass "a page of one question shows that question's context: in a questions list of one, and once in a spec that is the question"
  else
    fail "the context of a page of one question: $why"
  fi
  MDCHECK=$(cat <<'PY'
import sys
from html.parser import HTMLParser
VOID = {"br", "hr", "img", "input", "meta", "link", "col", "area", "base", "embed", "source", "track", "wbr"}
class Node:
    def __init__(self, tag, attrs):
        self.tag, self.attrs, self.kids = tag, dict(attrs), []
    def text(self):
        return "".join(k if isinstance(k, str) else k.text() for k in self.kids)
    def find(self, tag):
        out = []
        for k in self.kids:
            if not isinstance(k, str):
                out += [k] if k.tag == tag else []
                out += k.find(tag)
        return out
    def els(self):
        return [k for k in self.kids if not isinstance(k, str)]
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.root = Node("root", []); self.stack = [self.root]
    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs); self.stack[-1].kids.append(n)
        if tag not in VOID:
            self.stack.append(n)
    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]; break
    def handle_data(self, data):
        if self.stack[-1].tag not in ("script", "style"):
            self.stack[-1].kids.append(data)
p = P(); p.feed(open(sys.argv[1], encoding="utf-8").read())
page, case = p.root, sys.argv[2]
texts = lambda nodes: [n.text().strip() for n in nodes]
tables = page.find("table")
bad = []
def want(cond, why):
    if not cond:
        bad.append(why)
if case == "md-owner":
    want(len(tables) == 1, f"{len(tables)} tables")
    if tables:
        t = tables[0]
        want(t.find("th") == [], "a header row of empty cells")
        rows = t.find("tr")
        want([texts(r.find("td"))[0] for r in rows] == ["Outcome", "Careful paths"], f"rows {[texts(r.find('td')) for r in rows]}")
        want(texts(t.find("code")) == ["land.py", "criteria.py"], f"code {texts(t.find('code'))}")
    shown = page.text()
    want("|---" not in shown and "| |" not in shown and "| Outcome" not in shown, "raw table text on the page")
elif case == "md-header":
    want(len(tables) == 1, f"{len(tables)} tables")
    if tables:
        t = tables[0]
        want(texts(t.find("th")) == ["Name", "Value"], f"header {texts(t.find('th'))}")
        want(texts(t.find("td")) == ["a", "b"] and texts(t.find("b")) == ["b"], f"cells {texts(t.find('td'))}")
        want("right" in t.find("td")[1].attrs.get("style", "") if len(t.find("td")) > 1 else False, "the ---: column is not right-aligned")
elif case == "md-pipe-code":
    tds = tables[0].find("tr")[-1].find("td") if tables else []
    want(len(tds) == 2, f"{len(tds)} cells in the row")
    if len(tds) == 2:
        want(texts(tds[0].find("code")) == ["a|b"], f"code {texts(tds[0].find('code'))}")
        want(tds[1].text().strip() == "x | y", f"escaped pipe cell {tds[1].text()!r}")
elif case == "md-no-delim":
    want(tables == [], "a table with no delimiter line")
    want(any("a | b | c" in t for t in texts(page.find("p"))), "the lines are not a paragraph")
elif case == "md-hr":
    want(len(page.find("hr")) == 1, f"{len(page.find('hr'))} rules")
    want("---" not in page.text(), "raw --- on the page")
elif case == "md-h4":
    want(texts(page.find("h4")) == ["Deep heading"] and texts(page.find("h5")) == ["Deeper"], "no h4 and h5")
    want("####" not in page.text(), "raw #### on the page")
elif case == "md-nested":
    top = [u for u in page.find("ul") if any(li.text().startswith("top") for li in u.els())]
    want(len(top) == 1 and len(top[0].els()) == 2, "the outer list has not two items")
    if top:
        inner = top[0].els()[0].find("ul")
        want(len(inner) == 1 and "child" in inner[0].text() and "more of the child" in inner[0].text(), "the child is not a list in the first item")
elif case == "md-tilde":
    pres = [x for x in page.find("pre") if x.text() == "code here"]
    want(len(pres) == 1, "no code block")
    want("~~~" not in page.text(), "raw ~~~ on the page")
elif case == "md-task":
    shown = page.text()
    want("[ ]" not in shown and "[x]" not in shown, "raw task boxes on the page")
    want("☐" in shown and "☑" in shown, "no box glyphs")
elif case == "md-plus":
    want(any(texts(u.els()) == ["one", "two"] for u in page.find("ul")), "no list of two items")
elif case == "md-mermaid":
    drawn = [x for x in page.find("svg") if x.attrs.get("id", "").startswith("hd-mm-")]
    want(len(drawn) == 1, f"{len(drawn)} drawn diagrams")
    if drawn:
        want("Start" in drawn[0].text() and "End" in drawn[0].text(), f"the chart's text is {drawn[0].text()!r}")
    want(not any("flowchart" in x.text() for x in page.find("pre")), "the fence's text shows as code")
    py = [x for x in page.find("pre") if x.attrs.get("data-lang") == "python"]
    want(len(py) == 1 and "py-fence" in py[0].text(), "the python fence is not code")
elif case == "md-start":
    ols = page.find("ol")
    want(len(ols) == 1 and ols[0].attrs.get("start") == "3", "the list does not start at 3")
said = {
    "md-owner": "a table with an empty header row renders its rows and code, and no raw |---|",
    "md-header": "a table with a header row renders it, with the alignment marks",
    "md-pipe-code": "a pipe in a code span, or escaped, stays in its cell",
    "md-no-delim": "lines with pipes and no delimiter line stay a paragraph",
    "md-hr": "a --- line is a rule",
    "md-h4": "a heading of level 4 or 5 is a heading",
    "md-nested": "an indented item is a list in its parent item",
    "md-tilde": "a ~~~ fence is a code block",
    "md-task": "a task item shows a box",
    "md-plus": "a + item is a list item",
    "md-start": "an ordered list keeps its first number",
    "md-mermaid": "a mermaid fence in an md block draws a chart with its labels, and a python fence beside it stays code",
}[case]
print(f"markdown {case}: " + ("; ".join(bad) if bad else said))
sys.exit(bool(bad))
PY
)
  for n in "${mdnames[@]}"; do
    if grep -q 'mermaid unavailable' "$WORK/$n.err" 2>/dev/null; then
      skipped=$((skipped + 1))
      skip "markdown $n: the mermaid bundle could not be downloaded"
    elif why=$("$PY" -I -B -c "$MDCHECK" "$WORK/$n.dom" "$n"); then pass "$why"; else fail "$why"; fi
  done
  # At 900 px a wide table scrolls inside its own box and the page stays as wide as its window; the
  # grid's previews keep their path inside the card. A script added to a copy of the page measures
  # both questions of the spec and writes the numbers into the page Chrome prints.
  mkdir -p "$WORK/measure"
  "$PY" -I -B -c "$PROBE" "$WORK/wide.html" "$WORK/measure/wide.html"
  "$chrome" --headless=new --disable-gpu --no-sandbox --no-first-run --use-mock-keychain --user-data-dir="$WORK/chrome" \
    --window-size=900,900 --virtual-time-budget=4000 --dump-dom "file://$WORK/measure/wide.html" > "$WORK/measure/wide.dom" 2>/dev/null || true
  if why=$("$PY" -I -B -c "$MEASURED" "$WORK/measure/wide.dom"); then
    pass "at 900 px a wide table scrolls inside its own box and the page is no wider than its window; a long path in a grid's preview breaks inside the card"
  else
    fail "a wide table or a long path: $why"
  fi
  # The runtime posts its answer to `answer`, a path relative to the page: a page served under
  # /tasks/export-notes/cards/P1/ posts to that card's own route. A refusal (409) shows the reply's
  # `said` and leaves the page to answer again, and a 200 shows its `said`. The spec's own script picks
  # B and submits, and submits again 800 ms later: the refused page sends twice, the taken one once.
  mkdir -p "$WORK/post"
  printf '%s' '{"prompt": "Keep the empty cell?", "options": [{"id": "a", "label": "yes"}, {"id": "b", "label": "no, write a dash"}], "script": "api.select(\"answer\", \"b\"); api.submit(); setTimeout(() => api.submit(), 800);"}' > "$WORK/post/card.json"
  "$PY" -I -B "$MAIN" lem-ask render "$WORK/post/card.json" -o "$WORK/post/card.html" >/dev/null
  POSTED=$(cat <<'PY'
import http.server, json, re, subprocess, sys, threading
chrome, page, work = sys.argv[1], open(sys.argv[2], "rb").read(), sys.argv[3]
ROUTE = "/tasks/export-notes/cards/P1/"
def run(code, said):
    posts = []
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass
        def do_GET(self):
            self.send_response(200 if self.path == ROUTE else 404)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page if self.path == ROUTE else b"")
        def do_POST(self):
            posts.append((self.path, json.loads(self.rfile.read(int(self.headers.get("content-length", 0))) or b"{}")))
            body = json.dumps({"said": said}).encode()
            self.send_response(code)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    dom = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run", "--use-mock-keychain",
                          f"--user-data-dir={work}/chrome", "--virtual-time-budget=3000", "--dump-dom",
                          f"http://127.0.0.1:{server.server_address[1]}{ROUTE}"], capture_output=True, text=True, timeout=60).stdout
    server.shutdown()
    status = re.search(r'<span class="hd-status">(.*?)</span>', dom)
    return posts, status.group(1) if status else None, 'class="hd-done"' in dom, dom
wrong = []
posts, status, done, dom = run(409, "A was taken in the session at 15:42")
# the page's pagehide beacon, when Chrome leaves the refused page open, goes to the same route
answers = [path for path, body in posts if body.get("status") == "answered"]
if answers != ["/tasks/export-notes/cards/P1/answer"] * 2 or {path for path, _ in posts} != {"/tasks/export-notes/cards/P1/answer"}:
    wrong.append(f"the refused page posted {posts}, not two answers to the card's own answer route")
if posts and posts[0][1].get("answers", {}).get("answer", {}).get("selected") != ["b"]:
    wrong.append(f"the refused page posted {posts[0][1]}")
if status != "A was taken in the session at 15:42" or done:
    wrong.append(f"the refused page shows {status!r} in its status line, and its done banner: {done}")
posts, status, done, dom = run(200, "Your answer is on record")
if [path for path, body in posts if body.get("status") == "answered"] != ["/tasks/export-notes/cards/P1/answer"]:
    wrong.append(f"the taken page posted to {[path for path, _ in posts]}, not once to the card's own answer route")
if not re.search(r'class="hd-done"[^>]*>Your answer is on record<', dom):
    wrong.append("the taken page does not show the reply's said")
print("; ".join(wrong))
sys.exit(bool(wrong))
PY
)
  if why=$("$PY" -I -B -c "$POSTED" "$chrome" "$WORK/post/card.html" "$WORK"); then
    pass "the page posts its answer to the answer route beside it, shows a refusal's said and can answer again, and shows the said of an answer taken"
  else
    fail "the page's post to the route beside it: $why"
  fi
else
  for f in "${pages[@]}"; do skip "page loads: $(basename "$f" .html): no Chrome or Chromium found"; done
  for n in "${mdnames[@]}"; do skip "markdown $n: no Chrome or Chromium found"; done
  skip "a question's own context and body are shown: no Chrome or Chromium found"
  skip "a page of one question shows that question's context: no Chrome or Chromium found"
  skip "at 900 px a wide table scrolls inside its own box: no Chrome or Chromium found"
  skip "the page posts its answer to the answer route beside it: no Chrome or Chromium found"
fi

results_add_up
finished=yes
if [ "$fails" -gt 0 ]; then
  printf '%d lem-ask check(s) failed\n' "$fails"
  exit 1
fi
if [ "$skipped" -gt 0 ]; then
  printf 'all lem-ask checks passed; the diagram checks of %d pages were skipped: the mermaid bundle could not be downloaded\n' "$skipped"
else
  printf 'all lem-ask checks passed\n'
fi
