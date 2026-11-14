#!/usr/bin/env python3
"""Say where one repository keeps what the task skill reads, and what its flow settings are.

Every project keeps its own settings in its repository: what the project is, its style guide, its
personas, its review configuration, its lessons, the checks that gate a landing, and the paths
whose change takes the careful flow. `.agents/project.toml` at the root of the checkout names
them. A project that keeps some of these where an older tool already reads them (`.claude/rules`,
`.revmux`, `.personas`) may point at them there (`init --existing link`), so adopting the skill
moves nothing, or start the skill's own layout beside them (`init --existing new`). Which of the
two is the owner's choice, so `init` refuses to guess it.

    project.py show                 everything, resolved, as JSON
    project.py path NAME            one path, absolute
    project.py careful FILE...      which of the files take the careful flow
    project.py may-land BRANCH      exit 1 unless tasks of this project may land on BRANCH
    project.py existing             the folders an older tool already reads here, as JSON
    project.py init [--base NAME] [--existing link|new] [--reviewer claude|codex]
                                    write .agents/project.toml
    project.py task-dir SLUG        make and print one task's state directory
    project.py tasks                every task's ask and newest state block, as JSON
    project.py state-dir            the folder that holds every task, the review queue and the night reports

Task state is kept inside the git directory every worktree shares: it is never committed, a
worktree's removal does not take it, and a session that replaces another finds it.

A settings file with an unknown key, a wrong type or a path outside the repository is an error:
a stage that read half of it would run on defaults nobody chose. Needs Python 3.11 for tomllib.
"""

import argparse
import difflib
import fnmatch
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

SETTINGS = Path(".agents") / "project.toml"
# name -> (where the skill's own layout keeps it, where an older tool keeps it)
PATHS: dict[str, tuple[str, str | None]] = {
    "profile": (".agents/profile.md", ".personas/profile.md"),
    "styleguide": (".agents/styleguide", ".claude/rules"),
    "personas": (".agents/personas", ".personas/cast"),
    "review": (".agents/review", ".revmux"),
    "lessons": (".agents/lessons.md", None),
    "rulings": ("docs/rulings", None),
    "backlog": ("docs/backlog", None),
    "plans": ("docs/plans", None),
}
LAND = ("owner", "agent")
# the agents that can sit in the reviewer's pane
REVIEWERS = ("claude", "codex")
# a task's slug: plain words joined by hyphens, e.g. report-dates-stay-whole
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
TABLES: dict[str, tuple[str, ...]] = {
    "paths": tuple(PATHS),
    "branch": ("base", "land", "protected"),
    "gate": ("commands",),
    "flow": ("careful",),
    "seats": ("reviewer",),
    "tools": ("annotate",),
}

TEMPLATE = """\
# What the task skill reads in this repository. `project.py show` prints it resolved.

[paths]
# Where each kind of setting lives, relative to the root of the checkout.
{paths}

[branch]
# The branch a task starts from and lands on.
base = "{base}"
# Who lands a finished task: "owner", or "agent" once the gate is green.
land = "owner"
# Branches nothing lands on and nothing is pushed to through this skill, whoever asks.
protected = []

[gate]
# The machine checks that gate a landing, each run at the root of the checkout.
commands = []

[flow]
# Paths whose change takes the careful flow: the plan is read by the reviewer and each task
# is reviewed before the next starts. A `*` crosses directories.
careful = []

[seats]
# The agent in the reviewer's pane: "claude" or "codex". The agent that runs /task builds; this one
# reads its plans and diffs. The same family twice is allowed.
{reviewer}

[tools]
# The skill or command the owner marks up a plan or a draft with. "webrev" comes with the skill;
# name your own instead.
annotate = "webrev"
"""


class SettingsError(Exception):
    pass


def repo_root(start: Path) -> Path:
    found = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False,
    )
    if found.returncode != 0:
        raise SettingsError(f"{start} is not inside a git checkout")
    return Path(found.stdout.strip())


def nearest(key: str, valid: tuple[str, ...]) -> str:
    close = difflib.get_close_matches(key, valid, n=1)
    return f"; did you mean {close[0]!r}?" if close else f"; valid: {', '.join(valid)}"


def strings(value: object, where: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SettingsError(f"{where} must be a list of strings")
    return value


def inside(root: Path, relative: str, where: str) -> Path:
    if Path(relative).is_absolute():
        raise SettingsError(f"{where} = {relative!r} must be relative to the root of the checkout")
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise SettingsError(f"{where} = {relative!r} leaves the repository")
    return resolved


def load(root: Path) -> dict:
    file = root / SETTINGS
    raw: dict = {}
    if file.is_file():
        try:
            raw = tomllib.loads(file.read_text())
        except tomllib.TOMLDecodeError as error:
            raise SettingsError(f"{SETTINGS}: {error}") from error
    for table, body in raw.items():
        if table not in TABLES:
            raise SettingsError(f"{SETTINGS}: unknown table [{table}]{nearest(table, tuple(TABLES))}")
        if not isinstance(body, dict):
            raise SettingsError(f"{SETTINGS}: [{table}] must be a table")
        for key in body:
            if key not in TABLES[table]:
                raise SettingsError(f"{SETTINGS}: unknown key {table}.{key}{nearest(key, TABLES[table])}")

    paths = {}
    for name, (default, _older) in PATHS.items():
        relative = raw.get("paths", {}).get(name, default)
        if not isinstance(relative, str):
            raise SettingsError(f"{SETTINGS}: paths.{name} must be a string")
        resolved = inside(root, relative, f"paths.{name}")
        paths[name] = {"path": str(resolved), "exists": resolved.exists()}

    branch = raw.get("branch", {})
    base = branch.get("base")
    if base is not None and not isinstance(base, str):
        raise SettingsError(f"{SETTINGS}: branch.base must be a string")
    land = branch.get("land", "owner")
    if land not in LAND:
        raise SettingsError(f"{SETTINGS}: branch.land = {land!r} must be one of {', '.join(LAND)}")

    protected = strings(branch.get("protected", []), "branch.protected")
    if base in protected:
        raise SettingsError(f"{SETTINGS}: branch.base = {base!r} is in branch.protected, so no task could land")
    annotate = raw.get("tools", {}).get("annotate", "webrev")
    if not isinstance(annotate, str) or not annotate.strip():
        raise SettingsError(f"{SETTINGS}: tools.annotate must name a skill or a command")

    reviewer = raw.get("seats", {}).get("reviewer")
    if reviewer is not None and reviewer not in REVIEWERS:
        raise SettingsError(f"{SETTINGS}: seats.reviewer = {reviewer!r} must be one of {', '.join(REVIEWERS)}")

    return {
        "root": str(root),
        "settings": str(file) if file.is_file() else None,
        "paths": paths,
        "branch": {"base": base, "land": land, "protected": protected},
        "gate": {"commands": strings(raw.get("gate", {}).get("commands", []), "gate.commands")},
        "flow": {"careful": strings(raw.get("flow", {}).get("careful", []), "flow.careful")},
        "seats": {"reviewer": reviewer},
        "tools": {"annotate": annotate},
    }


def cmd_path(settings: dict, name: str) -> None:
    if name not in settings["paths"]:
        raise SettingsError(f"no path named {name!r}{nearest(name, tuple(PATHS))}")
    print(settings["paths"][name]["path"])


def cmd_careful(settings: dict, files: list[str]) -> None:
    root = Path(settings["root"]).resolve()
    careful, plain = [], []
    for file in files:
        relative = Path(file)
        if relative.is_absolute():
            relative = relative.resolve().relative_to(root)
        match = next((p for p in settings["flow"]["careful"] if fnmatch.fnmatchcase(relative.as_posix(), p)), None)
        if match:
            careful.append({"file": relative.as_posix(), "pattern": match})
        else:
            plain.append(relative.as_posix())
    print(json.dumps({"careful": careful, "plain": plain}, indent=2))


def cmd_may_land(settings: dict, target: str) -> None:
    """Exit 1 unless TARGET is the branch this project's tasks land on."""
    branch = settings["branch"]
    if target in branch["protected"]:
        raise SettingsError(f"{target!r} is protected in {SETTINGS}: nothing lands on it or is pushed to it")
    if branch["base"] is None:
        raise SettingsError(f"{SETTINGS} names no branch.base, so no branch can be landed on")
    if target != branch["base"]:
        raise SettingsError(f"tasks of this project land on {branch['base']!r}, not on {target!r}")
    print(f"{target}: tasks land here; the {branch['land']} lands")


def default_branch(root: Path) -> str | None:
    head = subprocess.run(
        ["git", "-C", str(root), "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        capture_output=True, text=True, check=False,
    )
    return head.stdout.strip().removeprefix("origin/") if head.returncode == 0 else None


def older_folders(root: Path) -> dict[str, str]:
    """The settings an older tool already keeps here, where the skill's own layout has nothing yet."""
    return {
        name: older for name, (default, older) in PATHS.items()
        if older and (root / older).exists() and not (root / default).exists()
    }


def cmd_init(root: Path, base: str | None, existing: str | None, reviewer: str | None) -> None:
    file = root / SETTINGS
    if file.exists():
        raise SettingsError(f"{SETTINGS} already exists; edit it")
    base = base or default_branch(root)
    if not base:
        raise SettingsError("cannot tell the base branch (no origin/HEAD); pass --base NAME")
    older = older_folders(root)
    if older and existing is None:
        found = ", ".join(f"{name} in {path}" for name, path in older.items())
        raise SettingsError(
            f"this repository already keeps {found}; pass --existing link to point at them, "
            "or --existing new to start the skill's own layout",
        )
    lines = []
    for name, (default, _older) in PATHS.items():
        chosen = older[name] if existing == "link" and name in older else default
        lines.append(f'{name} = "{chosen}"')
    file.parent.mkdir(exist_ok=True)
    seat = f'reviewer = "{reviewer}"' if reviewer else '# reviewer = "codex"'
    file.write_text(TEMPLATE.format(paths="\n".join(lines), base=base, reviewer=seat))
    print(file)


def state_root(root: Path) -> Path:
    """The folder task state lives in: inside the git directory every worktree shares."""
    common = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-common-dir"], capture_output=True, text=True, check=True,
    ).stdout.strip()
    return (root / common).resolve() / "task"


def cmd_task_dir(root: Path, slug: str) -> None:
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    directory = state_root(root) / "tasks" / slug
    (directory / "reports").mkdir(parents=True, exist_ok=True)
    print(directory)


def cmd_tasks(root: Path) -> None:
    tasks = []
    parent = state_root(root) / "tasks"
    for directory in sorted(d for d in (parent.iterdir() if parent.is_dir() else ()) if d.is_dir()):
        ask = directory / "task.md"
        state = directory / "state.md"
        tasks.append({
            "slug": directory.name,
            "ask": ask.read_text().strip().splitlines()[0] if ask.is_file() and ask.read_text().strip() else None,
            # state.md is newest block first; a block ends at the first blank line
            "state": state.read_text().strip().split("\n\n")[0] if state.is_file() else None,
        })
    print(json.dumps(tasks, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the checkout (default: the current one)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("show")
    commands.add_parser("path").add_argument("name")
    commands.add_parser("careful").add_argument("files", nargs="+")
    commands.add_parser("may-land").add_argument("branch")
    init = commands.add_parser("init")
    init.add_argument("--base")
    init.add_argument("--existing", choices=("link", "new"))
    init.add_argument("--reviewer", choices=REVIEWERS)
    commands.add_parser("existing")
    commands.add_parser("task-dir").add_argument("slug")
    commands.add_parser("tasks")
    commands.add_parser("state-dir")
    args = parser.parse_args()
    try:
        root = repo_root(Path(args.repo))
        if args.command == "init":
            cmd_init(root, args.base, args.existing, args.reviewer)
            return
        if args.command == "existing":
            print(json.dumps(older_folders(root), indent=2))
            return
        if args.command == "task-dir":
            cmd_task_dir(root, args.slug)
            return
        if args.command == "tasks":
            cmd_tasks(root)
            return
        if args.command == "state-dir":
            state_root(root).mkdir(exist_ok=True)
            print(state_root(root))
            return
        settings = load(root)
        if args.command == "show":
            print(json.dumps(settings, indent=2))
        elif args.command == "path":
            cmd_path(settings, args.name)
        elif args.command == "may-land":
            cmd_may_land(settings, args.branch)
        else:
            cmd_careful(settings, args.files)
    except SettingsError as error:
        sys.exit(f"project.py: {error}")


if __name__ == "__main__":
    main()
