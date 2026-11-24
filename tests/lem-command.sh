#!/usr/bin/env bash
# The command `lem` (bin/lem): each name runs its script with the arguments, stdin, stdout, stderr
# and exit status as they came, `lem` alone and `lem help` list the names, an unknown name is
# refused, nothing writes bytecode, `lem version` names the plugin's version and commit, `lem` in
# Lem's marketplace clone runs the newest installed release, and no text of Lem tells anyone to run a
# script of Lem's by its path.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

LEM=$PWD/bin/lem
# the names, as `lem help` lists them: each line after the first that opens with two spaces
listed=$("$LEM" help | "$PY" -c 'import sys; print(" ".join(line.split()[0] for line in sys.stdin.read().splitlines()[1:] if line.startswith("  ")))')
names=${listed% version help}

# The table of names, src/lem/names.py, which bin/lem and the entry read.
NAMES=$PWD/src/lem/names.py
# A copy of the plugin's folder with bin/lem, the entry and the table of names, whose every module of
# a name is a stand-in that says what it got: its arguments, its stdin, whether Python writes
# bytecode, and a line on stderr; it exits 7.
FAKE=$WORK/plugin
mkdir -p "$FAKE/bin" "$FAKE/src/lem" && cp "$LEM" "$FAKE/bin/lem"
cp "$PWD/src/lem/__init__.py" "$PWD/src/lem/__main__.py" "$NAMES" "$FAKE/src/lem/"
"$PY" -I - "$NAMES" "$FAKE" <<'PY'
import runpy, sys
from pathlib import Path
commands = runpy.run_path(sys.argv[1])["COMMANDS"]
for name, (module, _) in commands.items():
    target = Path(sys.argv[2]) / "src" / "lem" / f"{module}.py"
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
    *"--repo|a b|x\"y| stdin=in put bytecode=1 $name") ;;
    *) routed="no: $name gave $out" ;;
  esac
  [ "$code" = 7 ] && [ "$err" = "err $name" ] || routed="no: $name exited $code with $err"
  [ "$routed" = yes ] || break
done
# every name of the table, so that a help that lists fewer does not pass on the names it kept
count=$("$PY" -I -c 'import runpy, sys; print(len(runpy.run_path(sys.argv[1])["COMMANDS"]))' "$NAMES")
if [ "$routed" = yes ] && [ -n "$names" ] && [ "$(wc -w <<<"$names" | tr -d ' ')" = "$count" ]; then
  pass "each name of lem ($(wc -w <<<"$names" | tr -d ' ')) runs its own script with the arguments as they came, a space and a quote in them, its stdin, its stdout and stderr apart, and its exit status, and Python with -B"
else
  fail "lem's names and what each passes through: $routed ($names)"
fi

# each name of the real plugin names a script that is there, and the real script answers through
# lem; cast takes no --help (it reads this checkout's settings first)
real=yes
for name in $names; do
  file=src/lem/$("$PY" -I -c 'import runpy, sys; print(runpy.run_path(sys.argv[1])["COMMANDS"][sys.argv[2]][0])' "$NAMES" "$name").py
  [ -f "$PWD/$file" ] || { real="no: $name names $file"; break; }
  case "$name" in
    cast) ;;
    *) said=$("$LEM" "$name" --help 2>&1 || true)
       grep -qF "usage: lem $name" <<<"$said" || { real="no: lem $name --help shows no usage of lem $name: $(head -n 1 <<<"$said")"; break; } ;;
  esac
done
# a usage error speaks the name the developer types, and so does the usage in the script's own text
wrong=$("$LEM" land start 2>&1 || true)
own=$("$LEM" land --help 2>&1 || true)
if ! grep -qF "lem land start: error: the following arguments are required: slug" <<<"$wrong" || ! grep -qxF "    lem land start SLUG [--conflicting]" <<<"$own"; then
  real="no: a usage error or the usage text of lem land names another command: $wrong"
fi
if [ "$real" = yes ]; then
  pass "each name of lem names a script of this checkout, and each one with an --help answers with its own usage in the name the developer types, as does a usage error"
else
  fail "lem's scripts: $real"
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
unknown_out=$("$LEM" tickets approve x 2>"$WORK/unknown")
unknown_code=$?
set -e
if [ "$unknown_code" = 1 ] && [ -z "$unknown_out" ] && grep -qF "lem: 'tickets' is no command of Lem's" "$WORK/unknown" && grep -qE '^  project +' "$WORK/unknown"; then
  pass "an unknown name exits 1, and says so on stderr with the names"
else
  fail "an unknown name: $unknown_code / $unknown_out / $(cat "$WORK/unknown")"
fi

# A plugin's folder that is not whole: bin/lem with no package at all, or with a package that lacks the table of
# names or the entry. lem alone, lem help, a name and an unknown name each say in one line on stderr which file is not
# there and to install the plugin again, and exit 1, under this Python and an old python3; lem version still answers.
cut=yes
for gone in src src/lem/names.py src/lem/__main__.py; do
  rm -rf "$WORK/cut" && mkdir -p "$WORK/cut/bin" "$WORK/cut/src" && cp "$LEM" "$WORK/cut/bin/lem" && cp -R "$PWD/src/lem" "$WORK/cut/src/lem"
  rm -rf "${WORK:?}/cut/$gone"
  for python in "$PY" /usr/bin/python3; do
    [ -x "$python" ] || continue
    for args in "" help "project show" "tickets approve"; do
      [ "$gone" = src/lem/__main__.py ] && case "$args" in "" | help | tickets*) continue ;; esac
      set +e
      # shellcheck disable=SC2086 # each word of ARGS is one argument
      said=$("$python" -B "$WORK/cut/bin/lem" $args 2>"$WORK/cut-err")
      code=$?
      set -e
      line="lem: $WORK/cut/$([ "$gone" = src ] && echo src/lem/names.py || echo "$gone") is not there: the plugin's folder $WORK/cut is not whole; install the plugin again"
      if [ "$code" != 1 ] || [ -n "$said" ] || [ "$(cat "$WORK/cut-err")" != "$line" ]; then
        cut="no: $python lem $args without $gone: $code / $said / $(cat "$WORK/cut-err")"
        break 3
      fi
    done
  done
done
rm -rf "$WORK/cut/src"
versioned=$("$PY" -B "$WORK/cut/bin/lem" version 2>&1 | field 'd["root"]' || true)
if [ "$cut" = yes ] && [ "$versioned" = "$WORK/cut" ]; then
  pass "in a plugin's folder that is not whole, lem alone, lem help, a name and an unknown name each say in one line which file is not there and to install the plugin again, and exit 1, also under an old python3; lem version still answers"
else
  fail "lem in a folder that is not whole: $cut / $versioned"
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
for name in project land criteria decisions experts cast issue board picker session; do "$LEM" "$name" --help >/dev/null 2>&1 || true; done
caches=$(find src skills bin -name __pycache__ -type d)
if [ -z "$caches" ]; then pass "lem leaves no __pycache__, also of the scripts that import their siblings"; else fail "lem left a __pycache__: $caches"; fi

# No text of Lem tells anyone to run a script of Lem's by its path or by its file's name: each says
# `lem NAME`. Allowed by name: the harness's paragraph on the fallback, and nothing else. A comment
# of a script is for the reader of the code, and stays out of it.
"$PY" -I - "$PWD" > "$WORK/said" <<'PY'
import re, sys
from pathlib import Path
root = Path(sys.argv[1])
names = "project|land|criteria|decisions|board|picker|session|doctor|corrections|experts|cast|issues"
# `python3 SKILL_DIR/scripts/land.py`, `bash SKILL_DIR/scripts/run.sh`, also across a line break
path_form = re.compile(r"(?:python3|bash)\s+\S*scripts/[\w-]+\.(?:py|sh)")
# `land.py merged SLUG`, `project.py --repo W tasks`, also across a line break
short_form = re.compile(rf"`(?:{names})\.py\s+[-a-z\[]")
found = []
for path in sorted(root.glob("skills/**/*")) + sorted(root.glob("agents/**/*")) + sorted(root.glob("src/**/*")):
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

# land.py, criteria.py and decisions.py run a sibling's command in their own process (sibling.py): for each way
# a module can end, the result is the one a process of its own gives, and a command of APART is such a process. The
# ends are modules of a copy of the package, each a name of its table, and a process of one runs through the copy's entry.
mkdir -p "$WORK/siblings/src"
cp -R "$PWD/src/lem" "$WORK/siblings/src/lem"
"$PY" -I -B - "$WORK/siblings/src" "$WORK/siblings" > "$WORK/siblings.out" <<'PY' || true
import importlib, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
work = Path(sys.argv[2])
package = Path(sys.argv[1]) / "lem"
ends = {
    "text": 'print("out")\n    sys.exit("text.py: refused")', "number": 'print("out")\n    sys.exit(3)', "wrapped": "sys.exit(-1)",
    "none": 'print("out", argv)\n    print("said", file=sys.stderr)\n    sys.exit()', "plain": 'print("out")',
    "crash": 'print("half")\n    {}["x"]', "pid": 'import os\n    print(os.getpid())',
}
with open(package / "names.py", "a") as table:
    table.write(f"COMMANDS.update({{name: (name, 'an end of a test') for name in {[*ends, 'stand']!r}}})\n")
from lem import sibling as lem_sibling
# the copy's modules of the test's names, which `loaded` does not name
lem_sibling.loaded = lambda name: importlib.import_module(f"lem.{name}")
main = str(package / "__main__.py")
wrong = []
for name, body in ends.items():
    (package / f"{name}.py").write_text(f"import sys\ndef main(argv=None):\n    {body}\nif __name__ == '__main__':\n    main(sys.argv[1:])\n")
    got = lem_sibling.run(name, work, name, "--flag")
    real = subprocess.run([sys.executable, "-B", main, name, "--repo", str(work), name, "--flag"], capture_output=True, text=True)
    if name == "pid":
        # this process runs it, and a command of APART (as criteria.py red is) runs in another
        lem_sibling.APART[("pid", "apart")] = "a process of its own"
        got, real = got.stdout.strip(), lem_sibling.run("pid", work, "apart").stdout.strip()
        if got != str(__import__("os").getpid()) or real in ("", got):
            wrong.append(f"pid: {got} in this process, {real} for a command of APART")
        continue
    last = [(ran.returncode, ran.stdout, ran.stderr.strip().splitlines()[-1:] if name == "crash" else ran.stderr) for ran in (got, real)]
    if last[0] != last[1] or (name == "crash" and not got.stderr.startswith("Traceback")):
        wrong.append(f"{name}: {last[0]!r} in this process, {last[1]!r} as a process")
# a module in a sibling's place with no main(argv) of its own, such as a stand-in that reads sys.argv, is run as a process
(package / "stand.py").write_text('import sys\nprint(sys.argv[1:])\nsys.exit("stand.py: refused" if "landed" in sys.argv else 0)\n')
for args in (("state", "x", "landed"), ("tasks",)):
    got, real = lem_sibling.run("stand", work, *args), subprocess.run([sys.executable, "-B", main, "stand", "--repo", str(work), *args], capture_output=True, text=True)
    if (got.returncode, got.stdout, got.stderr) != (real.returncode, real.stdout, real.stderr):
        wrong.append(f"stand-in {args}: {(got.returncode, got.stdout, got.stderr)!r}, as a process {(real.returncode, real.stdout, real.stderr)!r}")
print("; ".join(wrong) or "same")
PY
if [ "$(cat "$WORK/siblings.out")" = same ]; then
  pass "a sibling's command in the caller's process ends as its own process would: sys.exit with a text, a number or none, a plain end, and a crash with its traceback and exit 1; a command of APART and a file with no main(argv) each run as a process of their own"
else
  fail "a sibling's command in the caller's process: $(cat "$WORK/siblings.out")"
fi

# In Lem's marketplace clone (PLUGINS/marketplaces/NAME), which holds the head of main, lem runs no script of the clone:
# it becomes the bin/lem of the newest release of lem@NAME in PLUGINS/installed_plugins.json, by number and not by text,
# with every argument, its output and its exit status, and lem-ask the release's lem-ask; an install of another
# marketplace is not one of them. With no release listed it exits 1 and names the install.
PLUGINS=$WORK/claude/plugins
CLONE=$PLUGINS/marketplaces/lem
mkdir -p "$CLONE/bin" && cp "$LEM" "$CLONE/bin/lem" && ln -s lem "$CLONE/bin/lem-ask"
"$PY" -I - "$PLUGINS" <<'PY'
import json, sys
from pathlib import Path
plugins = Path(sys.argv[1])
def release(name, number):
    folder = plugins / "cache" / name / "lem" / number
    (folder / "bin").mkdir(parents=True)
    (folder / "bin" / "lem").write_text(f"import os, sys\nprint({number!r}, os.path.basename(sys.argv[0]), '|'.join(sys.argv[1:]) + '|')\nsys.exit(5)\n")
    (folder / "bin" / "lem-ask").symlink_to("lem")
    return str(folder)
listed = {"lem@lem": [{"scope": "project", "projectPath": "/r/shop", "installPath": release("lem", "0.9.0"), "version": "0.9.0"},
                      {"scope": "user", "installPath": release("lem", "0.10.0"), "version": "0.10.0"},
                      {"scope": "project", "projectPath": "/r/old", "installPath": release("lem", "0.2.0"), "version": "0.2.0"},
                      {"scope": "project", "projectPath": "/r/odd", "installPath": "/nowhere", "version": "a commit"}],
          "lem@fork": [{"scope": "user", "installPath": release("fork", "9.0.0"), "version": "9.0.0"}]}
(plugins / "installed_plugins.json").write_text(json.dumps({"version": 2, "plugins": listed}))
PY
set +e
handed=$("$CLONE/bin/lem" picker --repo "a b" 'x"y' 2>&1); handed_code=$?
asked=$("$CLONE/bin/lem-ask" --help 2>&1); asked_code=$?
printf '{"version": 2, "plugins": {"lem@fork": []}}\n' > "$PLUGINS/installed_plugins.json"
none=$("$CLONE/bin/lem" version 2>"$WORK/none"); none_code=$?
set -e
if [ "$handed" = "0.10.0 lem picker|--repo|a b|x\"y|" ] && [ "$handed_code" = 5 ] && [ "$asked" = "0.10.0 lem-ask --help|" ] && [ "$asked_code" = 5 ] \
  && [ "$none_code" = 1 ] && [ -z "$none" ] && grep -qF "lem: $CLONE is the marketplace clone of lem@lem, which holds the head of main and no release" "$WORK/none" \
  && grep -qF "the owner installs one with \`claude plugin install lem@lem\`" "$WORK/none"; then
  pass "lem in Lem's marketplace clone runs the newest installed release of that marketplace's lem, 0.10.0 before 0.9.0, with its arguments, output and exit status, and lem-ask the release's lem-ask; with no release listed it exits 1 and names the install"
else
  fail "lem in the marketplace clone: $handed ($handed_code) / $asked ($asked_code) / $none_code $none $(cat "$WORK/none")"
fi

finish
