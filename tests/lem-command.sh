#!/usr/bin/env bash
# The command `lem`, the package's console script (`lem.__main__.cli`): each name runs its script with the arguments,
# stdin, stdout, stderr and exit status as they came, `lem` alone and `lem help` list the names, an unknown name is
# refused, nothing writes bytecode into a checkout, `lem version` names Lem's version, the folder of its files and its
# commit, the wheel holds what the app reads, and no text of Lem tells anyone to run a script of Lem's by its path.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

LEM=$LEM_UNDER_TEST
# the names, as `lem help` lists them: each line after the first that opens with two spaces
listed=$("$LEM" help | "$PY" -c 'import sys; print(" ".join(line.split()[0] for line in sys.stdin.read().splitlines()[1:] if line.startswith("  ")))')
names=${listed% version help}

# The table of names, src/lem/names.py, which the entry reads.
NAMES=$PWD/src/lem/names.py
# A checkout of its own with the entry, the table of names and lem.paths, whose every module of a name is a stand-in that
# says what it got: its arguments, its stdin, whether Python writes bytecode, and a line on stderr; it exits 7. Its
# command is a console script as an install writes one.
FAKE=$WORK/plugin
mkdir -p "$FAKE/bin" "$FAKE/src/lem" "$FAKE/skills/lem" && touch "$FAKE/skills/lem/SKILL.md"
cp "$PWD/src/lem/__init__.py" "$PWD/src/lem/__main__.py" "$PWD/src/lem/paths.py" "$NAMES" "$FAKE/src/lem/"
printf '%s\n' "#!$PY -B" 'import sys' "sys.path.insert(0, '$FAKE/src')" 'from lem.__main__ import cli' 'sys.exit(cli())' > "$FAKE/bin/lem"
chmod +x "$FAKE/bin/lem"
"$PY" -I - "$NAMES" "$FAKE" <<'PY'
import runpy, sys
from pathlib import Path
commands = runpy.run_path(sys.argv[1])["COMMANDS"]
for name, (module, _) in commands.items():
    target = Path(sys.argv[2]) / "src" / "lem" / f"{module}.py"
    target.write_text("import sys\nprint('|'.join(sys.argv[1:]) + '|', 'stdin=' + sys.stdin.read().strip(), 'bytecode=' + str(sys.dont_write_bytecode), '" + name + "')\n"
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
    *"--repo|a b|x\"y| stdin=in put bytecode=True $name") ;;
    *) routed="no: $name gave $out" ;;
  esac
  [ "$code" = 7 ] && [ "$err" = "err $name" ] || routed="no: $name exited $code with $err"
  [ "$routed" = yes ] || break
done
# every name of the table, so that a help that lists fewer does not pass on the names it kept
count=$("$PY" -I -c 'import runpy, sys; print(len(runpy.run_path(sys.argv[1])["COMMANDS"]))' "$NAMES")
if [ "$routed" = yes ] && [ -n "$names" ] && [ "$(wc -w <<<"$names" | tr -d ' ')" = "$count" ]; then
  pass "each name of lem ($(wc -w <<<"$names" | tr -d ' ')) runs its own script with the arguments as they came, a space and a quote in them, its stdin, its stdout and stderr apart, and its exit status, and with no bytecode written"
else
  fail "lem's names and what each passes through: $routed ($names)"
fi

# each name of the real package names a script that is there, and the real script answers through
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
lines=$(grep -cE '^  [a-z-]+ +[A-Za-z(]' <<<"$bare" || true)
if [ "$bare" = "$helped" ] && [ "$bare" = "$dashed" ] && [ "$(tail -n 1 <<<"$bare")" = "exit 0" ] && [ "$lines" = "$(wc -w <<<"$listed" | tr -d ' ')" ]; then
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

# version: Lem's version from its manifest, the folder of its files as root, and the commit: the file build-commit of the
# package when a build wrote one, else git's HEAD when the root is a checkout, else none
mkdir -p "$FAKE/.claude-plugin" && printf '{"name": "lem", "version": "1.4.0"}\n' > "$FAKE/.claude-plugin/plugin.json"
fake_version=$("$FAKE/bin/lem" version | field '(d["root"], d["version"], d["commit"])')
printf 'abc1234\n' > "$FAKE/src/lem/build-commit"
stamped=$("$FAKE/bin/lem" version | field 'd["commit"]')
own_version=$("$LEM" version | field '(d["commit"], d["root"])')
commit=$(git rev-parse --short HEAD)
if [ "$fake_version" = "('$FAKE', '1.4.0', None)" ] && [ "$stamped" = abc1234 ] && [ "$own_version" = "('$commit', '$PWD')" ]; then
  pass "lem version gives the manifest's version, the folder of Lem's files as root, and the commit a build wrote, else the checkout's, else none"
else
  fail "lem version: $fake_version / $stamped / $own_version"
fi

# The wheel, built as an install builds it (uv build: the sdist, and the wheel from it) and installed into a virtual
# environment outside the checkout: it holds every module of the package and every file the app reads through
# lem.paths, under lem/data, byte for byte as git has them, and nothing more there; its name holds the manifest's
# version; its lem version names that folder
# as root, the manifest's version and no commit (no checkout, no build-commit); its lem help lists every name. With the
# build backend in uv's cache the build needs no network; with neither uv nor the cache and no network it cannot run.
wheel_check() {
  local built=$WORK/wheel app=$WORK/app said root data diff version
  if ! said=$(uv build --offline --out-dir "$built" 2>&1) && ! said=$(uv build --out-dir "$built" 2>&1); then
    skip "the wheel holds the package and the plugin's files the app reads, and its lem version and lem help answer from them: uv build failed, offline and online: $(tail -n 3 <<<"$said")"
    return
  fi
  uv venv -q --python "$PY" "$app" >/dev/null 2>&1
  uv pip install -q --offline --no-deps --python "$app/bin/python" "$built"/lem-*.whl >/dev/null 2>&1
  said=$(env HOME="$WORK/apphome" "$app/bin/lem" version 2>&1 || true)
  root=$(field 'd["root"]' <<<"$said" 2>/dev/null || true)
  data=$(find "$app/lib" -path '*/site-packages/lem/data' -type d)
  diff=$("$PY" -I - "$PWD" "$data" <<'PY'
import subprocess, sys
from pathlib import Path
checkout, data = Path(sys.argv[1]), Path(sys.argv[2])
tracked = subprocess.run(["git", "-C", str(checkout), "ls-files", "-z", "--", "skills", "agents", "hooks", "src/lem"], capture_output=True, text=True, check=True).stdout.split("\0")
wanted = {name: name for name in tracked if name and not name.startswith("src/")}
wanted.update({name: name for name in (".claude-plugin/plugin.json", "assets/lem-mark.svg", "assets/lem-mark-night.svg")})
modules = {name.removeprefix("src/lem/"): name for name in tracked if name.startswith("src/lem/")}
found = {str(path.relative_to(data)) for path in data.rglob("*") if path.is_file()}
wrong = [f"{name} is not the checkout's" for name, source in sorted(wanted.items()) if not (data / name).is_file() or (data / name).read_bytes() != (checkout / source).read_bytes()]
wrong += [f"{name} is no file of the plugin's" for name in sorted(found - set(wanted))]
wrong += [f"the module {name} is not the checkout's" for name, source in sorted(modules.items()) if (data.parent / name).read_bytes() != (checkout / source).read_bytes()]
print("; ".join(wrong) or f"same {len(wanted)} {len(modules)}")
PY
)
  helped=$(env HOME="$WORK/apphome" "$app/bin/lem" help 2>&1 | "$PY" -c 'import sys; print(" ".join(line.split()[0] for line in sys.stdin.read().splitlines()[1:] if line.startswith("  ")))')
  table=$("$PY" -I -c 'import runpy, sys; print(" ".join(runpy.run_path(sys.argv[1])["COMMANDS"]))' "$NAMES")
  version=$(field 'd["version"]' < .claude-plugin/plugin.json)
  if [ -n "$data" ] && [ "$root" = "$data" ] && [ "$(field '(d["version"], d["commit"])' <<<"$said")" = "('$version', None)" ] && [ -f "$built/lem-$version-py3-none-any.whl" ] \
    && [[ "$diff" == "same "* ]] && [ "$helped" = "$table version help" ]; then
    pass "the wheel, built from the sdist with the manifest's version in its name and installed outside the checkout, holds each module of the package and each file the app reads through lem.paths, byte for byte, and no other file under lem/data; its lem version names that folder as root, the manifest's version and no commit, and its lem help lists every name"
  else
    fail "the installed wheel: $said / $data / $diff / $helped"
  fi
}
# uv_tried OUT SUBCOMMAND ARGS...: `uv SUBCOMMAND --offline ARGS`, and when uv says it needed the network for what its
# cache lacks, the same online; uv's output in OUT, and its exit
uv_tried() {
  local out=$1 sub=$2
  shift 2
  uv "$sub" --offline "$@" > "$out" 2>&1 && return 0
  uv_unreachable "$out" || return 1
  uv "$sub" "$@" > "$out" 2>&1
}

# A second install of a copy of this checkout, after its manifest, its build-commit and a file of the plugin changed,
# holds each change: uv's cache knows each input of the build (`[tool.uv] cache-keys`), so a sync builds again and
# never keeps the build before. The install is the one a formula makes: no editable install, no tools.
resync_check() {
  local copy=$WORK/resync first again data version
  mkdir -p "$copy"
  git ls-files -z | tar --null -T - -cf - | tar -xf - -C "$copy"
  if ! (cd "$copy" && uv_tried "$WORK/resync.out" sync --locked --no-editable --no-dev --python "$PY"); then
    if uv_unreachable "$WORK/resync.out"; then
      skip "a second sync of a copy holds its changed manifest, build-commit and plugin file: uv's cache lacks the build backend, and uv reaches no index: $(tail -n 2 "$WORK/resync.out")"
    else
      fail "a sync of a copy of this checkout: $(tail -n 5 "$WORK/resync.out")"
    fi
    return
  fi
  first=$(env HOME="$WORK/apphome" "$copy/.venv/bin/lem" version 2>&1 | field '(d["version"], d["commit"])' 2>&1 || true)
  "$PY" -I -c 'import sys; p = sys.argv[1]; s = open(p).read(); open(p, "w").write(s.replace("\"version\": \"", "\"version\": \"9.", 1))' "$copy/.claude-plugin/plugin.json"
  printf 'abc1234\n' > "$copy/src/lem/build-commit"
  printf 'one more line\n' >> "$copy/skills/lem/SKILL.md"
  (cd "$copy" && uv_tried "$WORK/resync.out" sync --locked --no-editable --no-dev --python "$PY") || true
  again=$(env HOME="$WORK/apphome" "$copy/.venv/bin/lem" version 2>&1 | field '(d["version"], d["commit"])' 2>&1 || true)
  data=$(find "$copy/.venv/lib" -path '*/site-packages/lem/data/skills/lem/SKILL.md')
  version=$(field 'd["version"]' < .claude-plugin/plugin.json)
  if [ "$first" = "('$version', None)" ] && [ "$again" = "('9.$version', 'abc1234')" ] && [ -n "$data" ] && [ "$(tail -n 1 "$data")" = "one more line" ]; then
    pass "a second sync of a copy of this checkout, with no editable install, holds its changed manifest, its new build-commit and its changed plugin file: uv builds again for each"
  else
    fail "a second sync of a copy: first $first, again $again, SKILL.md's last line there: $(tail -n 1 "$data" 2>&1) / $(tail -n 3 "$WORK/resync.out")"
  fi
}

if command -v uv >/dev/null 2>&1; then
  wheel_check
  resync_check
else
  skip_function wheel_check "no uv here to build the wheel (https://docs.astral.sh/uv/)"
  skip_function resync_check "no uv here to install the package (https://docs.astral.sh/uv/)"
fi

# no bytecode: the real scripts, through lem, the ones that import their siblings among them
for name in project land criteria decisions experts cast issue board picker session; do "$LEM" "$name" --help >/dev/null 2>&1 || true; done
caches=$(find src skills -name __pycache__ -type d)
if [ -z "$caches" ]; then pass "lem leaves no __pycache__, also of the scripts that import their siblings"; else fail "lem left a __pycache__: $caches"; fi

# No text of Lem tells anyone to run a script of Lem's by its path or by its file's name: each says
# `lem NAME`. Allowed by name: the harness's paragraph on the fallback, and nothing else. A comment
# of a script is for the reader of the code, and stays out of it.
"$PY" -I - "$PWD" > "$WORK/said" <<'PY'
import re, sys
from pathlib import Path
root = Path(sys.argv[1])
names = "project|land|criteria|decisions|board|picker|session|doctor|corrections|experts|cast|issues|ask|jev"
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
call = r"\blem\s+[a-z]"
forms = [re.compile(r"\$\(\s*lem\s"), re.compile(r"(?:\s\|\s|&&|\|\|)\s*" + call), re.compile(call + r"[^\n]*?\s(?:\|\s+[a-z]|&&|\|\|)")]
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
# The copy is a checkout's: the package beside the plugin's files, which lem.paths finds there.
mkdir -p "$WORK/siblings/src" && ln -s "$PWD/skills" "$WORK/siblings/skills"
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

finish
