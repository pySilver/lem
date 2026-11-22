"""pick.py: the suites to run for the files a change touched, from one map.

    python3 tests/pick.py FILE...         the suites for these files (paths from the root)
    python3 tests/pick.py --base BASE     the suites for what `git diff --name-only BASE` names,
                                          and the files git does not track yet
    python3 tests/pick.py --check         the map's own check, a suite of tests/all.sh

It prints one command for each suite to run, `bash tests/NAME.sh` (the unit level's is
`python3 -B -m unittest discover -s tests/unit`), then `bash tests/shellcheck.sh`
with the suite files that changed, and lines that start with `#` for what it found: a file no
suite reads is named with "nothing reads it", and a file the map does not know runs the whole
suite (`bash tests/all.sh`). The Chrome suites, test-ask and test-site, run only for
their own files, not for a script they also start. The whole suite runs once before the base branch
moves: this list is for the turns before that.

The map was read from the suites' text on 2026-11-18, and the row of test-site on 2026-11-19 (the
scripts each one starts, and the files of this repository it reads), not measured by a trace. A script's change reaches every suite that runs
a script that calls it: land.py, criteria.py and decisions.py call their siblings in their own
process (`skills/lem/scripts/lem_sibling.py`).
"""

import fnmatch
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"

# The name that runs everything: a change to how the suites run is checked by a run of them all.
EVERYTHING = "all"
# The suites that are not a file tests/NAME.sh of their own: the map's check, and the unit level,
# one file for each script in tests/unit/, which tests/all.sh runs as `python3 -B tests/unit`.
COMMANDS = {"pick": "python3 tests/pick.py --check", "unit": "python3 -B -m unittest discover -s tests/unit", EVERYTHING: "bash tests/all.sh"}
CHROME = ("test-ask", "test-site")

# (the files, the suites that read them). A file pattern is fnmatch's over the path from the root,
# where `*` also crosses a `/`; a suite may be a pattern over the suites' names. A row with no suite
# names files nothing reads. A suite's own file, tests/NAME.sh, runs that suite and is in no row.
MAP: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    # Lem's scripts, and the suites that run them, directly or through a script that calls them. The
    # unit level calls their functions, and every file of it is its own.
    (("skills/lem/scripts/*", "tests/unit/*"), ("unit",)),
    # `lem project waiting` builds the board's model, and asks `lem session list` when the log has a session
    (("skills/lem/scripts/project.py", "skills/lem/scripts/lem_state.py", "skills/lem/scripts/lem_plans.py", "skills/lem/scripts/lem_board_model.py"),
     ("lem-*", "test-ask-expert", "test-gate-panel")),
    (("skills/lem/scripts/lem_sibling.py", "skills/lem/scripts/decisions.py", "skills/lem/scripts/criteria.py"),
     ("lem-land-*", "lem-decisions", "lem-serial", "lem-settings", "lem-state", "lem-machine", "lem-command", "lem-picker", "test-ask-expert", "lem-board-act")),
    (("skills/lem/scripts/land.py",), ("lem-land-*", "lem-serial", "lem-command", "lem-board-act")),
    (("skills/lem/scripts/board.py",), ("lem-serve", "lem-settings", "lem-machine", "lem-command", "lem-picker")),
    # the board server and the pages it draws, and the afternoon its block serves
    (("skills/lem/scripts/serve.py", "skills/lem/scripts/serve_hook.py", "skills/lem/scripts/lem_board_*.py", "skills/lem/scripts/lem_html.py",
      "skills/lem/scripts/lem_artifacts.py", "skills/lem/assets/*", "tests/board-showcase.py"), ("lem-serve", "lem-board-act", "lem-settings", "lem-picker", "lem-command")),
    # two machines under one address: the server that passes another's pages through, and the list of both
    (("skills/lem/scripts/serve.py", "skills/lem/scripts/lem_peers.py", "skills/lem/scripts/lem_board_pages.py"), ("lem-peers",)),
    (("skills/lem/scripts/picker.py", "skills/lem/scripts/session.py"), ("lem-picker", "lem-command")),
    (("skills/lem/scripts/session.py", "skills/lem/scripts/session_hook.py", "skills/lem/templates/handoff.md"), ("lem-session", "lem-command")),
    (("skills/lem/scripts/corrections.py", "skills/lem/scripts/jev.py", "hooks/*", "bin/lem-jev"), ("lem-machine", "lem-state", "lem-command")),
    (("skills/lem/scripts/doctor.py", "scripts/setup.py", ".claude-plugin/*", "agents/*"), ("lem-machine", "lem-command")),
    (("bin/lem", "skills/lem/scripts/lem_python.py"), ("lem-command", "lem-machine")),
    (("skills/lem-ask/*", "bin/lem-ask"), ("test-ask", "lem-machine", "lem-command")),
    (("skills/lem-ask-expert/*",), ("test-ask-expert", "lem-command")),
    (("skills/lem-gate/*", "skills/lem-panel/*"), ("test-gate-panel", "lem-state", "lem-command")),
    # the experts' brief names the personas through the panel's cast.py; the unit level calls both scripts' functions
    (("skills/lem-panel/scripts/*",), ("test-ask-expert", "unit")),
    (("skills/lem-ask-expert/scripts/*",), ("unit",)),
    # Texts a suite reads: every text under skills/ and agents/, none of which may tell anyone to run
    # a script by its path (lem-command), nor name a Lem text by a folder in a brief's first line
    # (tests/unit/test_session.py).
    (("skills/*/SKILL.md",), ("test-gate-panel",)),
    (("skills/*", "agents/*"), ("lem-command", "unit")),
    # Lem's page on GitHub Pages, and the workflow whose copy step the suite runs
    (("site/*", ".github/workflows/pages.yml"), ("test-site",)),
    (("docs/settings.md", "assets/night.py", "assets/lem.svg", "assets/lem-night.svg", "assets/lem-mark.svg", "assets/lem-mark-night.svg"), ("lem-settings",)),
    # The suites' own code.
    (("tests/lib.sh",), ("lem-*",)),
    (("tests/checks.sh",), ("lem-*", "test-ask", "test-site", "test-gate-panel", "shellcheck")),
    (("tests/suites.sh", "tests/limit.py", "tests/all.sh", "tests/test-lem.sh"), (EVERYTHING,)),
    (("tests/pick.py",), ("pick",)),
    # The short AGENTS.md, the list of rulings and its history, and the plan whose table has a row for each
    # file the list took the place of, which tests/unit/test_agents_md.py reads
    (("AGENTS.md", "docs/rulings/*", "docs/plans/2026-11-21-rulings-as-one-list.md"), ("unit",)),
    # The install guide's table of tools, whose tier words tests/unit/test_doctor.py checks against doctor.py
    (("docs/install.md",), ("unit",)),
    # What no suite reads, except docs/rulings/, the plan of the list and docs/install.md, which the rows above give the unit level;
    # tests/clock/ is a late clock that a criterion's command puts on PYTHONPATH or PATH, and tools/ is the maintainer's build of the board's kit, whose built files are under skills/lem/assets/.
    (("tools/*", "docs/*", "README.md", "CLAUDE.md", "LICENSE", "NOTICE", ".gitignore", ".lem/*", ".revmux/*", ".github/*",
      "assets/*", "tests/board-cdp.mjs", "tests/clock/*"), ()),
]
# The files the Chrome suites are run for: each row that names one of them is all of their own.
CHROME_OWN = {"test-ask": ("skills/lem-ask/*", "bin/lem-ask", "tests/checks.sh"),
              "test-site": ("site/*", ".github/workflows/pages.yml", "tests/checks.sh")}


def suites() -> list[str]:
    """Every suite there is: each tests/lem-*.sh and tests/test-*.sh but test-lem.sh, which runs the blocks; shellcheck; pick; unit."""
    found = sorted(path.stem for pattern in ("lem-*.sh", "test-*.sh") for path in TESTS.glob(pattern) if path.stem != "test-lem")
    return [*found, "shellcheck", "pick", "unit"]


def expand(names: tuple[str, ...], known: list[str]) -> set[str]:
    out = set()
    for name in names:
        matched = [EVERYTHING] if name == EVERYTHING else fnmatch.filter(known, name)
        if not matched:
            raise SystemExit(f"pick.py: the map names {name!r}, and no suite has that name; correct its row in MAP")
        out.update(matched)
    return out


def rows_of(path: str) -> list[tuple[tuple[str, ...], tuple[str, ...]]]:
    return [row for row in MAP if any(fnmatch.fnmatchcase(path, pattern) for pattern in row[0])]


def own_suite(path: str, known: list[str]) -> str | None:
    """The suite a file is the source of: tests/NAME.sh for each suite NAME."""
    match = re.fullmatch(r"tests/([^/]+)\.sh", path)
    return match.group(1) if match and match.group(1) in known else None


def pick(paths: list[str]) -> list[str]:
    known = suites()
    run: set[str] = set()
    notes: list[str] = []
    lint = sorted({path for path in paths if re.fullmatch(r"tests/[^/]+\.sh", path) and (ROOT / path).is_file()})
    for path in sorted(set(paths)):
        suite = own_suite(path, known)
        if suite:
            if (ROOT / path).is_file():
                run.add(suite)
            continue
        rows = rows_of(path)
        if not rows:
            notes.append(f"# {path}: not in the map, so the whole suite")
            run.add(EVERYTHING)
            continue
        named = set().union(*(expand(names, known) for _, names in rows))
        if not named:
            notes.append(f"# {path}: nothing reads it")
        run |= named
    if EVERYTHING in run:
        return [*notes, COMMANDS[EVERYTHING]]
    lines = [COMMANDS.get(suite, f"bash tests/{suite}.sh") for suite in sorted(run - {"shellcheck"})]
    if "shellcheck" in run:
        lines.append("bash tests/shellcheck.sh")
    elif lint:
        lines.append("bash tests/shellcheck.sh " + " ".join(lint))
    if not lines:
        notes.append("# nothing to run")
    return [*notes, *lines]


def changed(base: str) -> list[str]:
    def git(*args: str) -> list[str]:
        ran = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False)
        if ran.returncode != 0:
            raise SystemExit(f"pick.py: git {' '.join(args)} failed: {ran.stderr.strip()}; name a commit or a branch git knows as BASE")
        return [line for line in ran.stdout.splitlines() if line]
    return git("diff", "--name-only", base) + git("ls-files", "--others", "--exclude-standard")


def check() -> int:
    """The map's own check, in the form of a suite: every file git tracks is in the map or is a
    suite's own file, every script and hook is read by a suite, each suite is in tests/all.sh, each
    block in tests/test-lem.sh, the map names only suites there are, and a Chrome suite only for
    its own files."""
    known = suites()
    tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=True).stdout.splitlines()
    runner = (TESTS / "all.sh").read_text(encoding="utf-8")
    blocks = (TESTS / "test-lem.sh").read_text(encoding="utf-8")
    listed = set(re.findall(r"[\w-]+", " ".join(re.findall(r"suites\+?=\(([^)]*)\)", runner))))
    listed_blocks = set(re.findall(r"[\w-]+", " ".join(re.findall(r"blocks\+?=\(([^)]*)\)", blocks))))
    # Lem's own scripts and hooks: a test helper of tests/ is in the map, and need not be read by a suite
    scripts = [path for path in tracked if re.fullmatch(r"(skills/[^/]+/(scripts|bin)/[^/]+|bin/[^/]+|hooks/[^/]+|scripts/[^/]+)", path)]
    checks: list[tuple[str, str | None]] = []
    for path in tracked:
        if own_suite(path, known) or rows_of(path):
            checks.append((f"{path} is in the map", None))
        else:
            checks.append((f"{path} is in the map", "no row of MAP names it: add it to the row of the suites that read it, or to the last row"))
    for path in scripts:
        named = set().union(*(expand(names, known) for _, names in rows_of(path))) if rows_of(path) else set()
        ok = own_suite(path, known) or named
        checks.append((f"{path} is read by a suite", None if ok else "its rows name no suite"))
    for suite in known:
        checks.append((f"tests/all.sh runs {suite}", None if suite in listed else "add it to the suites of tests/all.sh"))
        if suite.startswith("lem-"):
            checks.append((f"tests/test-lem.sh runs {suite}", None if suite in listed_blocks else "add it to the blocks of tests/test-lem.sh"))
    for files, names in MAP:
        try:
            named = expand(names, known)
        except SystemExit as error:
            checks.append((f"the row of {files[0]} names suites there are", str(error)))
            continue
        for suite in CHROME:
            if suite in named:
                strange = [pattern for pattern in files if pattern not in CHROME_OWN[suite]]
                checks.append((f"the row of {files[0]} names {suite} only for its own files", None if not strange else f"{', '.join(strange)} is no file of {suite}'s; CHROME_OWN lists them"))
    print(f"collected {len(checks)}")
    for text, problem in checks:
        print(f"ok   {text}" if problem is None else f"FAIL {text}: {problem}")
    return 1 if any(problem for _, problem in checks) else 0


def main(argv: list[str]) -> int:
    if argv == ["--check"]:
        return check()
    if len(argv) == 2 and argv[0] == "--base":
        paths = changed(argv[1])
    elif argv and not any(arg.startswith("-") for arg in argv):
        paths = [arg.removeprefix("./") for arg in argv]
    else:
        sys.exit("pick.py: name the changed files, or --base BASE, or --check")
    print("\n".join(pick(paths)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
