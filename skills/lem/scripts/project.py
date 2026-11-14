#!/usr/bin/env python3
"""Say where one repository keeps what Lem reads, and what its flow settings are.

Every project keeps its own settings in its repository: what the project is, its style guide, its
personas, its review configuration, its lessons, the checks that gate a landing, and the paths
whose change takes the careful flow. `.lem/project.toml` at the root of the checkout names
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
                                    write .lem/project.toml
    project.py task-dir SLUG        make and print one task's state directory
    project.py worktree-dir SLUG    print where the task's worktree goes, inside a folder git ignores
    project.py state SLUG STATUS LINE...
                                    put a new block at the top of the task's state.md, with the time
    project.py tasks                every task's ask, status and newest state block, as JSON
    project.py log SLUG EVENT [key=value ...] [key:=json ...]
                                    append one event about a task to the log the board draws
    project.py may-start            exit 1 when as many tasks build as flow.max_tasks allows
    project.py state-dir            the folder that holds every task, the review queue and the night reports

Task state is kept inside the git directory every worktree shares: it is never committed, a
worktree's removal does not take it, and a session that replaces another finds it.

Every state block is also an event. `events.jsonl` in the state folder is the record, one JSON
object per line: `ts` (UTC to the second), `event`, `task`, then the event's fields. The same
record goes to `events.js` as a `lemEvent({...});` line, because the board is a file:// page: it
cannot read a file with fetch, and it can load a script (measured in agterm 0.34.0 by the monitor
this one follows). `state` writes `task.state` with the status, the lines, the ask, the limit and
the branch and newest commit of the task's worktree, so the board needs no agent to remember a
second command. `log` writes any other event: `key=value` stores a string and `key:=value` parses
JSON, so a commit made only of digits stays a string and an exit code stays a number.

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
from datetime import datetime, timezone
from pathlib import Path

SETTINGS = Path(".lem") / "project.toml"
# name -> (where the skill's own layout keeps it, where an older tool keeps it)
PATHS: dict[str, tuple[str, str | None]] = {
    "profile": (".lem/profile.md", ".personas/profile.md"),
    "styleguide": (".lem/styleguide", ".claude/rules"),
    "personas": (".lem/personas", ".personas/cast"),
    "review": (".lem/review", ".revmux"),
    "lessons": (".lem/lessons.md", None),
    "rulings": ("docs/rulings", None),
    "backlog": ("docs/backlog", None),
    "plans": ("docs/plans", None),
    "worktrees": (".lem/worktrees", ".claude/worktrees"),
}
LAND = ("owner", "agent")
# the agents that can sit in the reviewer's pane
REVIEWERS = ("claude", "codex")
# a task's slug: plain words joined by hyphens, e.g. report-dates-stay-whole
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
# What a task's newest state block may say, and who acts next:
#   queued    the ask is written and no lead runs yet: the limit was reached
#   building  a lead plans or builds
#   planned   the plan is committed and nothing builds it: it needs a session, or the owner reads it
#   held      it waits for the owner: a held decision, or a landing that is the owner's
#   blocked   the lead stopped on something the coordinator has to settle
#   ready     the report is written and the branch waits for its landing
#   landing   the gate runs on it
#   landed    it is on the base branch and its review is queued
#   drafted   a plan written at night that waits for the owner's word
#   dropped   nobody will build it
STATES = ("queued", "building", "planned", "held", "blocked", "ready", "landing", "landed", "drafted", "dropped")
# the states in which an agent works on the task and loads the machine
RUNNING = ("building",)
# The first line of a state block: the time in UTC, the status, one line of text.
STATE_LINE = re.compile(r"(?P<since>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z) (?P<status>[a-z]+): (?P<text>.+)")
# How many tasks build at one time when the settings do not say. Four to five ran well on one Mac;
# six gave a load average of 12 to 16 and unstable browser tests (convertiser-server, as its owner
# reported it on 2026-11-14). The right number depends on the machine and on the project's tests.
MAX_TASKS = 4
TABLES: dict[str, tuple[str, ...]] = {
    "paths": tuple(PATHS),
    "branch": ("base", "land", "protected"),
    "gate": ("commands",),
    "flow": ("careful", "max_tasks"),
    "seats": ("reviewer",),
    "tools": ("annotate",),
}

TEMPLATE = """\
# What Lem reads in this repository. `project.py show` prints it resolved.

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
# How many tasks build at one time. Four to five ran well on one Mac; six gave a load average of
# 12 to 16 and unstable browser tests (convertiser-server, 2026-11-14). Lower it when the tests
# share one database or drive a browser.
max_tasks = {max_tasks}

[seats]
# The agent in the reviewer's pane: "claude" or "codex". Lem's builders build; this one reads the
# plan and the diffs of a careful task. The same family twice is allowed.
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
    max_tasks = raw.get("flow", {}).get("max_tasks", MAX_TASKS)
    # a bool is an int in Python, and `max_tasks = true` is a mistake, not the number 1
    if isinstance(max_tasks, bool) or not isinstance(max_tasks, int) or max_tasks < 1:
        raise SettingsError(f"{SETTINGS}: flow.max_tasks = {max_tasks!r} must be a whole number, 1 or more")

    return {
        "root": str(root),
        "settings": str(file) if file.is_file() else None,
        "paths": paths,
        "branch": {"base": base, "land": land, "protected": protected},
        "gate": {"commands": strings(raw.get("gate", {}).get("commands", []), "gate.commands")},
        "flow": {"careful": strings(raw.get("flow", {}).get("careful", []), "flow.careful"), "max_tasks": max_tasks},
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
    file.write_text(TEMPLATE.format(paths="\n".join(lines), base=base, reviewer=seat, max_tasks=MAX_TASKS))
    print(file)


def state_root(root: Path) -> Path:
    """The folder task state lives in: inside the git directory every worktree shares."""
    common = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-common-dir"], capture_output=True, text=True, check=True,
    ).stdout.strip()
    return (root / common).resolve() / "lem"


def cmd_task_dir(root: Path, slug: str) -> None:
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    directory = state_root(root) / "tasks" / slug
    (directory / "reports").mkdir(parents=True, exist_ok=True)
    print(directory)


def cmd_worktree_dir(settings: dict, slug: str) -> None:
    """Print where a task's worktree goes, and keep the folder that holds worktrees out of git status."""
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    parent = Path(settings["paths"]["worktrees"]["path"])
    parent.mkdir(parents=True, exist_ok=True)
    ignore = parent / ".gitignore"
    if not ignore.is_file():
        # `*` ignores the folder's content and this file, so the project needs no ignore rule
        ignore.write_text("*\n")
    print(parent / slug)


def task_directory(root: Path, slug: str) -> Path:
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    directory = state_root(root) / "tasks" / slug
    if not directory.is_dir():
        raise SettingsError(f"no task {slug!r}; `project.py task-dir {slug}` makes its directory")
    return directory


def append_event(root: Path, event: str, slug: str, fields: dict) -> dict:
    """Append one record to the log, and to the copy of it the board can load."""
    record = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": event, "task": slug, **fields}
    line = json.dumps(record, ensure_ascii=False)
    directory = state_root(root)
    with (directory / "events.jsonl").open("a", encoding="utf-8") as log:
        log.write(line + "\n")
    with (directory / "events.js").open("a", encoding="utf-8") as feed:
        feed.write(f"lemEvent({line});\n")
    return record


def task_worktree(root: Path, settings: dict, slug: str) -> dict:
    """The branch and the newest commit of the task's worktree; nothing when it has no worktree."""
    def git(where: Path, *args: str) -> str | None:
        ran = subprocess.run(["git", "-C", str(where), *args], capture_output=True, text=True, check=False)
        return ran.stdout.strip() if ran.returncode == 0 and ran.stdout.strip() else None

    # Worktrees hang off the main checkout, and this may run in one of them: the first entry git
    # lists is the main checkout.
    listed = git(root, "worktree", "list", "--porcelain") or ""
    main = next((line.removeprefix("worktree ") for line in listed.splitlines() if line.startswith("worktree ")), None)
    if main is None:
        return {}
    path = Path(main) / Path(settings["paths"]["worktrees"]["path"]).relative_to(root.resolve()) / slug
    if not (path / ".git").exists():
        return {}
    commit = git(path, "log", "-1", "--format=%h%x00%s")
    head, _, subject = (commit or "").partition("\0")
    found = {"branch": git(path, "branch", "--show-current"), "head": head or None, "subject": subject or None}
    return {key: value for key, value in found.items() if value}


def cmd_state(root: Path, slug: str, status: str, lines: list[str]) -> None:
    """Put a new block at the top of the task's state.md, and the same as an event in the log."""
    directory = task_directory(root, slug)
    settings = load(root)
    if status not in STATES:
        raise SettingsError(f"status {status!r} is not one a task has{nearest(status, STATES)}")
    if any(not line.strip() or "\n" in line for line in lines):
        # a blank line ends a block, so one inside a block would hide the lines after it
        raise SettingsError("each LINE of a state block is one line of text, and none is empty")
    # the time is the clock's, never a writer's estimate
    since = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    block = "\n".join([f"{since} {status}: {lines[0].strip()}", *(line.strip() for line in lines[1:])])
    file = directory / "state.md"
    older = file.read_text().strip() if file.is_file() else ""
    fresh = directory / "state.md.new"
    fresh.write_text(block + ("\n\n" + older if older else "") + "\n")
    fresh.replace(file)
    ask = directory / "task.md"
    append_event(root, "task.state", slug, {
        "status": status, "text": lines[0].strip(), "lines": [line.strip() for line in lines[1:]],
        "ask": ask.read_text().strip().splitlines()[0] if ask.is_file() and ask.read_text().strip() else None,
        "limit": settings["flow"]["max_tasks"], **task_worktree(root, settings, slug),
    })
    print(json.dumps({"slug": slug, "status": status, "since": since}))


def cmd_log(root: Path, slug: str, event: str, pairs: list[str]) -> None:
    """Append one event about a task; `state` is the only writer of task.state."""
    task_directory(root, slug)
    if event == "task.state":
        raise SettingsError("task.state is written by `project.py state`, which also writes the state block")
    fields: dict[str, object] = {}
    for pair in pairs:
        key, separator, raw = pair.partition("=")
        typed = key.endswith(":")
        key = key.removesuffix(":")
        if not separator or not key:
            raise SettingsError(f"{pair!r} is neither key=value nor key:=json")
        if key in fields or key in ("ts", "event", "task"):
            raise SettingsError(f"field {key!r} is given twice or is one the log sets itself")
        try:
            fields[key] = json.loads(raw) if typed else raw
        except json.JSONDecodeError as error:
            raise SettingsError(f"{key!r} is not JSON ({error}): {raw!r}") from error
    print(json.dumps(append_event(root, event, slug, fields)))


def read_tasks(root: Path) -> list[dict]:
    tasks = []
    parent = state_root(root) / "tasks"
    for directory in sorted(d for d in (parent.iterdir() if parent.is_dir() else ()) if d.is_dir()):
        ask = directory / "task.md"
        state = directory / "state.md"
        # state.md is newest block first; a block ends at the first blank line
        block = state.read_text().strip().split("\n\n")[0] if state.is_file() and state.read_text().strip() else None
        first = STATE_LINE.fullmatch(block.splitlines()[0]) if block else None
        known = first is not None and first["status"] in STATES
        tasks.append({
            "slug": directory.name,
            "ask": ask.read_text().strip().splitlines()[0] if ask.is_file() and ask.read_text().strip() else None,
            # null when no block was written through `project.py state`: nobody can tell who acts next
            "status": first["status"] if known else None,
            "since": first["since"] if known else None,
            "state": block,
        })
    return tasks


def cmd_may_start(settings: dict, root: Path) -> None:
    """Exit 1 when as many tasks build as the project allows at one time."""
    limit = settings["flow"]["max_tasks"]
    running = [task["slug"] for task in read_tasks(root) if task["status"] in RUNNING]
    if len(running) >= limit:
        raise SettingsError(
            f"{len(running)} tasks build ({', '.join(running)}) and flow.max_tasks is {limit}: "
            f"write the new task's state as `queued` and start it when one of them stops; "
            f"only the owner raises the limit, in {SETTINGS}",
        )
    print(json.dumps({"running": running, "limit": limit}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="a directory inside the checkout (default: the current one)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("show")
    commands.add_parser("path").add_argument("name")
    commands.add_parser("careful").add_argument("files", nargs="+")
    commands.add_parser("may-land").add_argument("branch")
    commands.add_parser("worktree-dir").add_argument("slug")
    init = commands.add_parser("init")
    init.add_argument("--base")
    init.add_argument("--existing", choices=("link", "new"))
    init.add_argument("--reviewer", choices=REVIEWERS)
    commands.add_parser("existing")
    commands.add_parser("task-dir").add_argument("slug")
    state = commands.add_parser("state")
    state.add_argument("slug")
    state.add_argument("status")
    state.add_argument("lines", nargs="+", metavar="LINE")
    commands.add_parser("tasks")
    log = commands.add_parser("log")
    log.add_argument("slug")
    log.add_argument("event")
    log.add_argument("fields", nargs="*", metavar="key=value")
    commands.add_parser("may-start")
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
        if args.command == "state":
            cmd_state(root, args.slug, args.status, args.lines)
            return
        if args.command == "tasks":
            print(json.dumps(read_tasks(root), indent=2))
            return
        if args.command == "log":
            cmd_log(root, args.slug, args.event, args.fields)
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
        elif args.command == "worktree-dir":
            cmd_worktree_dir(settings, args.slug)
        elif args.command == "may-land":
            cmd_may_land(settings, args.branch)
        elif args.command == "may-start":
            cmd_may_start(settings, root)
        else:
            cmd_careful(settings, args.files)
    except SettingsError as error:
        sys.exit(f"project.py: {error}")


if __name__ == "__main__":
    main()
