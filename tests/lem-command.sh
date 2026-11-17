#!/usr/bin/env bash
# The command `lem` (bin/lem): each name runs its script with the arguments, stdin, stdout, stderr
# and exit status as they came, `lem` alone and `lem help` list the names, an unknown name is
# refused, nothing writes bytecode, `lem version` names the plugin's version and commit, and no
# text of Lem tells anyone to run a script of Lem's by its path.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

LEM=$PWD/bin/lem
# the names, as `lem help` lists them: each line after the first that opens with two spaces
listed=$("$LEM" help | "$PY" -c 'import sys; print(" ".join(line.split()[0] for line in sys.stdin.read().splitlines()[1:] if line.startswith("  ")))')
names=${listed% version help}

# A copy of the plugin's folder whose every script is a stand-in that says what it got: its
# arguments, its stdin, whether Python writes bytecode, and a line on stderr; it exits 7.
FAKE=$WORK/plugin
mkdir -p "$FAKE/bin" && cp "$LEM" "$FAKE/bin/lem"
"$PY" -I - "$LEM" "$FAKE" <<'PY'
import runpy, sys
from pathlib import Path
commands = runpy.run_path(sys.argv[1])["COMMANDS"]
for name, (path, _) in commands.items():
    target = Path(sys.argv[2]) / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if path.endswith(".sh"):
        target.write_text('printf "%s|" "$@"; printf " stdin=%s bytecode=- ' + name + '\\n" "$(cat)"; echo "err ' + name + '" >&2; exit 7\n')
    else:
        target.write_text("import sys\nprint('|'.join(sys.argv[1:]) + '|', 'stdin=' + sys.stdin.read().strip(), 'bytecode=' + str(sys.flags.dont_write_bytecode), '" + name + "')\n"
                          "print('err " + name + "', file=sys.stderr)\nsys.exit(7)\n")
PY
routed=yes
for name in $names; do
  set +e
  out=$(printf 'in put\n' | "$FAKE/bin/lem" "$name" --repo "a b" 'x"y' 2>"$WORK/err")
  code=$?
  set -e
  err=$(cat "$WORK/err")
  case "$out" in
    *"--repo|a b|x\"y| stdin=in put bytecode="[1-]" $name") ;;
    *) routed="no: $name gave $out" ;;
  esac
  [ "$code" = 7 ] && [ "$err" = "err $name" ] || routed="no: $name exited $code with $err"
  [ "$routed" = yes ] || break
done
if [ "$routed" = yes ] && [ -n "$names" ] && [ "$(wc -w <<<"$names")" -ge 14 ]; then
  pass "each name of lem ($(wc -w <<<"$names" | tr -d ' ')) runs its own script with the arguments as they came, a space and a quote in them, its stdin, its stdout and stderr apart, and its exit status, and Python with -B"
else
  fail "lem's names and what each passes through: $routed ($names)"
fi

# each name of the real plugin names a script that is there, and the real script answers through
# lem; doctor and cast take no --help (the one checks the machine, the other reads this checkout's
# settings first), and the release tools no flag
real=yes
for name in $names; do
  file=$("$PY" -I -c 'import runpy, sys; print(runpy.run_path(sys.argv[1])["COMMANDS"][sys.argv[2]][0])' "$LEM" "$name")
  [ -f "$PWD/$file" ] || { real="no: $name names $file"; break; }
  case "$name" in
    doctor | cast | release-*) ;;
    *) said=$("$LEM" "$name" --help 2>&1 || true)
       grep -qF "usage: $(basename "$file")" <<<"$said" || { real="no: lem $name --help shows no usage of $file"; break; } ;;
  esac
done
set +e
"$LEM" release-version >/dev/null 2>"$WORK/release"
release_code=$?
set -e
if [ "$real" = yes ] && [ "$release_code" = 1 ] && grep -qF "release type required" "$WORK/release"; then
  pass "each name of lem names a script of this checkout, each Python one with an --help answers with its own usage, and a release tool runs with bash"
else
  fail "lem's scripts: $real / $release_code / $(cat "$WORK/release")"
fi

# help: lem alone, lem help and lem --help list every name with a line each, and exit 0
bare=$("$LEM"; echo "exit $?")
helped=$("$LEM" help; echo "exit $?")
dashed=$("$LEM" --help; echo "exit $?")
lines=$(grep -cE '^  [a-z-]+ +[a-z(]' <<<"$bare" || true)
if [ "$bare" = "$helped" ] && [ "$bare" = "$dashed" ] && [ "$(tail -n 1 <<<"$bare")" = "exit 0" ] && [ "$lines" = "$(wc -w <<<"$listed" | tr -d ' ')" ] \
  && grep -qF "lem-ask (the question page) and lem-jev (the Jev model) are commands of their own" <<<"$bare"; then
  pass "lem alone, lem help and lem --help list every name with one line each, and exit 0"
else
  fail "lem's help: $bare"
fi

# an unknown name: exit 1, the name and the list on stderr, nothing on stdout
set +e
unknown_out=$("$LEM" stories approve x 2>"$WORK/unknown")
unknown_code=$?
set -e
if [ "$unknown_code" = 1 ] && [ -z "$unknown_out" ] && grep -qF "lem: 'stories' is no command of Lem's" "$WORK/unknown" && grep -qE '^  project +' "$WORK/unknown"; then
  pass "an unknown name exits 1, and says so on stderr with the names"
else
  fail "an unknown name: $unknown_code / $unknown_out / $(cat "$WORK/unknown")"
fi

# version: the plugin's version from its manifest when it has one, and the commit when the folder is a checkout
mkdir -p "$FAKE/.claude-plugin" && printf '{"name": "lem", "version": "1.4.0"}\n' > "$FAKE/.claude-plugin/plugin.json"
fake_version=$("$FAKE/bin/lem" version | field '(d["version"], d["commit"])')
own_version=$("$LEM" version | field '(d["commit"], d["root"])')
commit=$(git rev-parse --short HEAD)
if [ "$fake_version" = "('1.4.0', None)" ] && [ "$own_version" = "('$commit', '$PWD')" ]; then
  pass "lem version gives the manifest's version when it names one, and the commit when the plugin's folder is a git checkout"
else
  fail "lem version: $fake_version / $own_version"
fi

# no bytecode: the real scripts, through lem, the ones that import their siblings among them
for name in project land criteria decisions experts cast board; do "$LEM" "$name" --help >/dev/null 2>&1 || true; done
caches=$(find skills bin -name __pycache__ -type d)
if [ -z "$caches" ]; then pass "lem leaves no __pycache__, also of the scripts that import their siblings"; else fail "lem left a __pycache__: $caches"; fi

# No text of Lem tells anyone to run a script of Lem's by its path or by its file's name: each says
# `lem NAME`. Allowed by name: the harness's paragraph on the fallback, and nothing else. A comment
# of a script is for the reader of the code, and stays out of it.
"$PY" -I - "$PWD" > "$WORK/said" <<'PY'
import re, sys
from pathlib import Path
root = Path(sys.argv[1])
names = "project|land|criteria|decisions|board|doctor|corrections|experts|cast|gate-log|triage"
# `python3 SKILL_DIR/scripts/land.py`, `bash SKILL_DIR/scripts/get-notes.sh`, also across a line break
path_form = re.compile(r"(?:python3|bash)\s+\S*scripts/[\w-]+\.(?:py|sh)")
# `land.py merged SLUG`, `project.py --repo W tasks`, also across a line break
short_form = re.compile(rf"`(?:{names})\.py\s+[-a-z\[]")
found = []
for path in sorted(root.glob("skills/**/*")) + sorted(root.glob("agents/**/*")):
    if not path.is_file() or path.suffix not in (".md", ".html", ".json", ".py", ""):
        continue
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if path == root / "skills/lem/harness/claude-code.md":
        # the section on the command, which gives the fallback by its path
        inside = False
        for number, line in enumerate(lines):
            if line.startswith("## "):
                inside = line == "## lem"
            if inside:
                lines[number] = ""
    for number, line in enumerate(lines):
        if path.suffix in (".py", ".html") and line.lstrip().startswith(("#", "//")):
            continue
        # a form that starts on this line, whole on it or cut by the line break
        pair = line + "\n" + (lines[number + 1] if number + 1 < len(lines) else "")
        forms = [short_form] + ([path_form] if path.suffix != ".py" else [])
        if any(found_form.start() < len(line) for form in forms for found_form in form.finditer(pair)):
            found.append(f"{path.relative_to(root)}:{number + 1}: {line.strip()[:100]}")
print("\n".join(found))
PY
said=$(cat "$WORK/said")
if [ -z "$said" ]; then
  pass "no text under skills/ or agents/, and no message of a script, tells anyone to run a script of Lem's by its path or its file's name, outside the harness's fallback"
else
  fail "a text names a script of Lem's to run in the place of lem NAME:
$said"
fi

# The one rule `Bash(lem *)` covers a plain call: no text gives a `lem` call inside `$(...)`, before a pipe into another
# command or beside an `&&` or `||`, in a code span or a code block. A `|` between two options of a synopsis is no pipe.
"$PY" -I - "$PWD" > "$WORK/compound" <<'PY'
import re, sys
from pathlib import Path
root = Path(sys.argv[1])
call = r"\blem(?:-ask|-jev)?\s+[a-z]"
forms = [re.compile(r"\$\(\s*lem(?:-ask|-jev)?\s"), re.compile(r"(?:\s\|\s|&&|\|\|)\s*" + call), re.compile(call + r"[^\n]*?\s(?:\|\s+[a-z]|&&|\|\|)")]
found = []
for path in sorted(root.glob("skills/**/*.md")) + sorted(root.glob("agents/**/*.md")):
    fence = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if any(form.search(piece) for piece in ([line] if fence else re.findall(r"`([^`]+)`", line)) for form in forms):
            found.append(f"{path.relative_to(root)}:{number}: {line.strip()[:100]}")
print("\n".join(found))
PY
compound=$(cat "$WORK/compound")
if [ -z "$compound" ]; then
  pass "no text under skills/ or agents/ gives a lem call inside \$(...), before a pipe or beside && or ||: each is a plain call whose output the agent reads"
else
  fail "a text gives a lem call in a compound command, which the rule Bash(lem *) does not cover:
$compound"
fi

finish
