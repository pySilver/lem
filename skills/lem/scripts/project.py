#!/usr/bin/env python3
"""Say where one repository keeps what Lem reads, and what its flow settings are.

Every project keeps its own settings in its repository: what the project is, its style guide, its
personas, its review configuration, its lessons, the checks that gate a landing, and the paths
whose change takes the careful flow. `.lem/project.toml` at the root of the checkout names
them. A project that keeps some of these where an older tool already reads them (`.claude/rules`,
`.personas`) may point at them there (`init --existing link`), so adopting the skill
moves nothing, or start the skill's own layout beside them (`init --existing new`). Which of the
two is the owner's choice, so `init` refuses to guess it.

    project.py show                 everything, resolved, as JSON
    project.py path NAME            one path, absolute
    project.py careful FILE...      which of the files take the careful flow
    project.py may-land BRANCH      exit 1 unless tasks of this project may land on BRANCH
    project.py existing             the folders an older tool already reads here, as JSON
    project.py init [--base NAME] [--existing link|new] [--reviewer claude|codex]
                                    write .lem/project.toml
    project.py reviewer AGENT [MODEL [EFFORT [PLAN_EFFORT]]]
                                    who reviews on this machine, until `reviewer default`
    project.py reviewer default     the project's own reviewer again
    project.py migrate plan         the linked folders and the rule files, as JSON; changes nothing
    project.py migrate run [--styleguide FILE ...]
                                    move the linked folders under .lem on the current branch
    project.py task-dir SLUG [--ask TEXT] [--ticket ID]
                                    make and print one task's state directory; keep the owner's words
                                    and the ticket the ask came from
    project.py ticket-step SLUG started|commented|landed|dropped
                                    write down what Lem did to the task's ticket, once
    project.py worktree-dir SLUG    print where the task's worktree goes, inside a folder git ignores
    project.py state SLUG STATUS LINE...
                                    put a new block at the top of the task's state.md, with the time
    project.py tasks                every task's ask, status and newest state block, as JSON
    project.py log SLUG EVENT [key=value ...] [key:=json ...]
                                    append one event about a task to the log the board draws
    project.py may-start            exit 1 when as many tasks build or land as flow.max_tasks allows
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

`.lem/project.local.toml` is one person's or one day's choice on one machine: who sits in the
reviewer's pane (the usual reviewer is down, or out of tokens) and which tool marks up a plan. It
is not committed (`init` writes `.lem/.gitignore` for it), and it is read from the main checkout,
because a task's worktree has no copy of a file git does not track. It may hold `[seats]` and
`[tools]` and nothing else: the gate, the careful paths, the protected branches and who lands are
the project's rules, and a file nobody reviews must not open them. `show` names each setting that
came from it.

Linking the folders of an older tool is the first step of an adoption, not its end. `migrate run`
moves each linked folder to its place under `.lem/` with `git mv`, on a task's branch and from a
clean tree, and rewrites the paths in the settings file. An agent that loads `.claude/rules/` by
itself goes on doing so through a link per file, and that folder stays a real one, because only
the files that say how code is written here move. Which files those are is the owner's call, so
they are named with `--styleguide` and never guessed. The review tool's folder is not Lem's to
move: it is that tool's own, at the one path the tool reads, in a new project and in an adopted
one. The command ends with every tracked file that still names an old path, for a builder to
correct.

A settings file with an unknown key, a wrong type or a path outside the repository is an error:
a stage that read half of it would run on defaults nobody chose. Needs Python 3.11 for tomllib.
"""

import argparse
import difflib
import fnmatch
import json
import os
import re
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

SETTINGS = Path(".lem") / "project.toml"
LOCAL = Path(".lem") / "project.local.toml"
# the tables one machine may set for itself
LOCAL_TABLES = ("seats", "tools")
# name -> (where the skill's own layout keeps it, where an older tool keeps it)
PATHS: dict[str, tuple[str, str | None]] = {
    "profile": (".lem/profile.md", ".personas/profile.md"),
    "styleguide": (".lem/styleguide", ".claude/rules"),
    "personas": (".lem/personas", ".personas/cast"),
    # the review tool's own folder, where that tool reads it: another program's settings stay where they are
    "review": (".revmux", None),
    "lessons": (".lem/lessons.md", None),
    "rulings": ("docs/rulings", None),
    "backlog": ("docs/backlog", None),
    "plans": ("docs/plans", None),
    "worktrees": (".lem/worktrees", ".claude/worktrees"),
}
LAND = ("owner", "agent")
# How a task's branch reaches the base branch: its own commits, or one commit for the whole branch.
HISTORY = ("keep", "squash")
# the agents that can sit in the reviewer's pane
REVIEWERS = ("claude", "codex")
# The reviewer's seat: the agent, and what its pane is started with. A model and an effort are
# not checked against a list: their names change with each release of an agent's command, and
# that command refuses a wrong one loudly when the pane starts.
SEAT = ("agent", "model", "effort", "plan_effort")
# a task's slug: plain words joined by hyphens, e.g. report-dates-stay-whole
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
# What a task's newest state block may say, and who acts next:
#   queued    the ask is written and no lead runs yet: the limit was reached
#   building  a lead plans or builds
#   planned   the plan is committed and nothing builds it: it needs a session, or the owner reads it
#   held      it waits for the owner: a held decision, or a landing that is the owner's
#   blocked   the lead stopped on something the coordinator has to settle
#   ready     the report is written and the branch waits for its landing
#   landing   the gate runs on it, or a builder repairs what the gate or the base showed
#   landed    it is on the base branch and its review is queued
#   drafted   a plan written at night that waits for the owner's word
#   dropped   nobody will build it
STATES = ("queued", "building", "planned", "held", "blocked", "ready", "landing", "landed", "drafted", "dropped")
# The states in which the task loads the machine: a lead builds, or the gate runs and a builder may
# repair a conflict or a red gate.
RUNNING = ("building", "landing")
# The first line of a state block: the time in UTC, the status, one line of text.
STATE_LINE = re.compile(r"(?P<since>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z) (?P<status>[a-z]+): (?P<text>.+)")
# How many tasks build or land at one time when the settings do not say. Four to five ran well on one Mac;
# six gave a load average of 12 to 16 and unstable browser tests (convertiser-server, as its owner
# reported it on 2026-11-14). The right number depends on the machine and on the project's tests.
MAX_TASKS = 4
TABLES: dict[str, tuple[str, ...]] = {
    "paths": tuple(PATHS),
    "branch": ("base", "land", "history", "protected"),
    "gate": ("commands", "ignores"),
    "flow": ("careful", "max_tasks"),
    "seats": ("reviewer",),
    "tools": ("annotate",),
    "corrections": ("collect",),
    "tracker": ("kind", "server", "workspace", "team", "moves", "started", "landed"),
}
# The trackers Lem has a skill for, and who may move a ticket's status: Lem, or the tracker's own
# automation (a pull-request integration that moves a ticket by itself).
TRACKERS = ("linear",)
MOVES = ("lem", "tracker")
# a ticket's id as a tracker writes it, e.g. MBZ-12
TICKET = re.compile(r"[A-Za-z][A-Za-z0-9]*-[0-9]+")
# What Lem did to a task's ticket, each written down after the tracker took it, so that a step is
# never done twice and a session that was cut off can see what is still owed:
#   started    the ticket got the status for work that started
#   commented  the landing was commented on the ticket
#   landed     the ticket got the status for work that landed
#   dropped    the ticket got the comment that its task was dropped
TICKET_STEPS = ("started", "commented", "landed", "dropped")

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
# What lands: "keep" lands the branch's own commits, "squash" lands one commit for the whole task.
history = "keep"
# Branches nothing lands on and nothing is pushed to through this skill, whoever asks.
protected = []

[gate]
# The machine checks that gate a landing, each run at the root of the task's worktree.
commands = []
# Paths the gate does not read. When the base branch moves after a green gate by these files
# only, the result stands; any other file means the gate runs again. A `*` crosses directories.
ignores = []

[flow]
# Paths whose change takes the careful flow: the plan is read by the reviewer and each task
# is reviewed before the next starts. A `*` crosses directories.
careful = []
# How many tasks build or land at one time. Four to five ran well on one Mac; six gave a load
# average of 12 to 16 and unstable browser tests (convertiser-server, 2026-11-14). Lower it when
# the tests share one database or drive a browser.
max_tasks = {max_tasks}

[seats.reviewer]
# The agent in the reviewer's pane: "claude" or "codex". Lem's builders build; this one reads the
# plan and the diffs of a careful task. The same family twice is allowed.
{reviewer}
# What its pane starts with. Leave one out and the agent's own default holds.
# model = ""
# effort = ""        # for the review of a diff
# plan_effort = ""   # for the read of a careful plan

[corrections]
# Keep a queue of the owner's corrections for the retro. The hook that fills it sends each
# message the owner types, with the agent message it answers, to the Jev decision model through
# the `jev` command. That is the owner's choice, so it is false until he says yes, and he
# registers the hook himself (`/lem init` gives him the lines).
collect = false

# The tracker a task's ask may come from. Leave it out when the project has none. Lem reads a
# ticket into a task, and comments it when the task lands. `moves` says who moves the ticket's
# status: "lem", with the two status names as the team spells them, or "tracker" when the
# tracker's own automation moves it (a pull-request integration).
# [tracker]
# kind = "linear"
# server = "linear"      # the name of the tracker's MCP server in the agent
# workspace = "acme"     # the workspace, as in its address linear.app/acme: nothing is read or written in another
# team = "ABC"           # the key of the one team whose tickets this project takes
# moves = "lem"
# started = "In Progress"
# landed = "Done"

[tools]
# The skill or command the owner marks up a plan or a draft with. "lem-webrev" comes with Lem;
# name your own instead.
annotate = "lem-webrev"
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


def main_checkout(root: Path) -> Path:
    """The checkout every worktree hangs off: the first entry git lists. A file git does not track lives only there."""
    # -z ends each field with a NUL: a path may hold a line break, and a split on lines would cut it
    listed = subprocess.run(["git", "-C", str(root), "worktree", "list", "--porcelain", "-z"], capture_output=True, text=True, check=False)
    first = next((field.removeprefix("worktree ") for field in listed.stdout.split("\0") if field.startswith("worktree ")), None)
    return Path(first) if first else root


def toml_string(value: str) -> str:
    """A string as TOML writes it. JSON's own escapes would turn a character outside the basic plane into two halves TOML refuses."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + "".join(f"\\u{ord(c):04x}" if ord(c) < 0x20 or ord(c) == 0x7F else c for c in escaped) + '"'


def read_settings(file: Path, name: Path, tables: tuple[str, ...]) -> dict:
    """One settings file as a dict, with every table and key it may not hold refused."""
    if not file.is_file():
        return {}
    try:
        raw = tomllib.loads(file.read_text())
    except tomllib.TOMLDecodeError as error:
        raise SettingsError(f"{name}: {error}") from error
    for table, body in raw.items():
        if table not in TABLES:
            raise SettingsError(f"{name}: unknown table [{table}]{nearest(table, tuple(TABLES))}")
        if table not in tables:
            raise SettingsError(
                f"{name}: [{table}] is the project's rule and belongs in {SETTINGS}; "
                f"this file may hold only {', '.join(f'[{t}]' for t in tables)}",
            )
        if not isinstance(body, dict):
            raise SettingsError(f"{name}: [{table}] must be a table")
        for key in body:
            if key not in TABLES[table]:
                raise SettingsError(f"{name}: unknown key {table}.{key}{nearest(key, TABLES[table])}")
    return raw


def seat(raw: dict, name: Path) -> dict | None:
    """The reviewer's seat one file names, checked; None when the file names none."""
    given = raw.get("seats", {}).get("reviewer")
    if given is None:
        return None
    if not isinstance(given, dict):
        raise SettingsError(f'{name}: seats.reviewer is a table: write [seats.reviewer] and under it agent = "codex"')
    for key, value in given.items():
        if key not in SEAT:
            raise SettingsError(f"{name}: unknown key seats.reviewer.{key}{nearest(key, SEAT)}")
        if not isinstance(value, str) or not value.strip():
            raise SettingsError(f"{name}: seats.reviewer.{key} must be a word, not {value!r}; leave the line out for the agent's own default")
    if "agent" in given and given["agent"] not in REVIEWERS:
        raise SettingsError(f"{name}: seats.reviewer.agent = {given['agent']!r} must be one of {', '.join(REVIEWERS)}")
    if "agent" not in given and given:
        raise SettingsError(f"{name}: seats.reviewer names a model or an effort and no agent; a model belongs to one agent")
    return {key: given.get(key) for key in SEAT}


def annotate_of(raw: dict, name: Path) -> str | None:
    """The tool one file names for marking up a plan, checked; None when the file names none."""
    if "annotate" not in raw.get("tools", {}):
        return None
    tool = raw["tools"]["annotate"]
    if not isinstance(tool, str) or not tool.strip():
        raise SettingsError(f'{name}: tools.annotate = {tool!r} must name a skill or a command in quotes, as in annotate = "lem-webrev"')
    return tool


def load(root: Path) -> dict:
    file = root / SETTINGS
    raw = read_settings(file, SETTINGS, tuple(TABLES))
    local_file = main_checkout(root) / LOCAL
    local = read_settings(local_file, LOCAL, LOCAL_TABLES)

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

    history = branch.get("history", "keep")
    if history not in HISTORY:
        raise SettingsError(f"{SETTINGS}: branch.history = {history!r} must be one of {', '.join(HISTORY)}")
    protected = strings(branch.get("protected", []), "branch.protected")
    if base in protected:
        raise SettingsError(f"{SETTINGS}: branch.base = {base!r} is in branch.protected, so no task could land")
    overridden = []
    annotate = annotate_of(raw, SETTINGS) or "lem-webrev"
    local_annotate = annotate_of(local, LOCAL)
    if local_annotate is not None:
        annotate = local_annotate
        overridden.append("tools.annotate")

    # A local seat replaces the project's whole: its model and effort belong to the project's agent.
    reviewer = seat(raw, SETTINGS) or {key: None for key in SEAT}
    local_seat = seat(local, LOCAL)
    if local_seat is not None:
        reviewer = local_seat
        overridden.append("seats.reviewer")
    collect = raw.get("corrections", {}).get("collect", False)
    if not isinstance(collect, bool):
        raise SettingsError(f"{SETTINGS}: corrections.collect = {collect!r} must be true or false")
    tracker = None
    if "tracker" in raw:
        given = raw["tracker"]
        for key, value in given.items():
            if not isinstance(value, str) or not value.strip():
                raise SettingsError(f"{SETTINGS}: tracker.{key} must be a word in quotes, not {value!r}")
        for key in ("kind", "server", "workspace", "team", "moves"):
            if key not in given:
                raise SettingsError(f"{SETTINGS}: [tracker] needs {key}; leave the whole table out when the project has no tracker")
        if given["kind"] not in TRACKERS:
            raise SettingsError(f"{SETTINGS}: tracker.kind = {given['kind']!r} must be one of {', '.join(TRACKERS)}")
        if given["moves"] not in MOVES:
            raise SettingsError(f"{SETTINGS}: tracker.moves = {given['moves']!r} must be one of {', '.join(MOVES)}")
        named = [key for key in ("started", "landed") if key in given]
        if given["moves"] == "lem" and len(named) != 2:
            raise SettingsError(
                f'{SETTINGS}: with tracker.moves = "lem" the table names both statuses, started and landed, as the team spells them',
            )
        if given["moves"] == "lem" and given["started"].strip().lower() == given["landed"].strip().lower():
            raise SettingsError(
                f"{SETTINGS}: tracker.started and tracker.landed are both {given['started']!r}: "
                "a ticket would be marked as landed the moment its work starts",
            )
        if given["moves"] == "tracker" and named:
            raise SettingsError(f'{SETTINGS}: with tracker.moves = "tracker" Lem moves no ticket, so {" and ".join(named)} say nothing: remove them')
        tracker = {key: given.get(key) for key in TABLES["tracker"]}
    max_tasks = raw.get("flow", {}).get("max_tasks", MAX_TASKS)
    # a bool is an int in Python, and `max_tasks = true` is a mistake, not the number 1
    if isinstance(max_tasks, bool) or not isinstance(max_tasks, int) or max_tasks < 1:
        raise SettingsError(f"{SETTINGS}: flow.max_tasks = {max_tasks!r} must be a whole number, 1 or more")

    return {
        "root": str(root),
        # the checkout every worktree hangs off; it is `root` unless this ran in a task's worktree
        "main": str(main_checkout(root)),
        "settings": str(file) if file.is_file() else None,
        "paths": paths,
        "branch": {"base": base, "land": land, "history": history, "protected": protected},
        "gate": {
            "commands": strings(raw.get("gate", {}).get("commands", []), "gate.commands"),
            "ignores": strings(raw.get("gate", {}).get("ignores", []), "gate.ignores"),
        },
        "flow": {"careful": strings(raw.get("flow", {}).get("careful", []), "flow.careful"), "max_tasks": max_tasks},
        "seats": {"reviewer": reviewer},
        "tools": {"annotate": annotate},
        "corrections": {"collect": collect},
        "tracker": tracker,
        # what this machine set for itself, so a report can say that the reviewer is not the project's
        "local": {"file": str(local_file) if local_file.is_file() else None, "overrides": overridden},
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
    agent = f'agent = "{reviewer}"' if reviewer else '# agent = "codex"'
    file.write_text(TEMPLATE.format(paths="\n".join(lines), base=base, reviewer=agent, max_tasks=MAX_TASKS))
    # one machine's own settings are never committed
    ignore = file.parent / ".gitignore"
    known = ignore.read_text().splitlines() if ignore.is_file() else []
    if LOCAL.name not in known:
        ignore.write_text("\n".join([*known, LOCAL.name]) + "\n")
    print(file)


def cmd_reviewer(root: Path, words: list[str]) -> None:
    """Write, or with `default` remove, this machine's own reviewer seat."""
    file = main_checkout(root) / LOCAL
    local = read_settings(file, LOCAL, LOCAL_TABLES)
    # What the file already holds is checked before any of it is written again: a wrong value is
    # refused with its fix, and the file stays as the owner left it.
    annotate_of(local, LOCAL)
    if words == ["default"]:
        local.get("seats", {}).pop("reviewer", None)
    else:
        if len(words) > len(SEAT):
            raise SettingsError(f"reviewer takes AGENT [MODEL [EFFORT [PLAN_EFFORT]]], not {len(words)} words")
        local.setdefault("seats", {})["reviewer"] = dict(zip(SEAT, words))
        seat(local, LOCAL)
    lines = ["# This machine's own settings for Lem. Not committed; `project.py reviewer` writes the seat."]
    for table in LOCAL_TABLES:
        body = local.get(table) or {}
        plain = {key: value for key, value in body.items() if not isinstance(value, dict)}
        if plain:
            lines += ["", f"[{table}]", *(f"{key} = {toml_string(value)}" for key, value in plain.items())]
        for key, value in body.items():
            if isinstance(value, dict) and value:
                lines += ["", f"[{table}.{key}]", *(f"{k} = {toml_string(v)}" for k, v in value.items())]
    if len(lines) == 1:
        file.unlink(missing_ok=True)
    else:
        file.parent.mkdir(exist_ok=True)
        file.write_text("\n".join(lines) + "\n")
    resolved = load(root)
    print(json.dumps({"reviewer": resolved["seats"]["reviewer"], "local": resolved["local"]}, indent=2))


def linked(root: Path) -> dict[str, tuple[str, str]]:
    """The settings that still point at an older tool's folder: name -> (where it is, where Lem keeps it)."""
    raw = read_settings(root / SETTINGS, SETTINGS, tuple(TABLES)).get("paths", {})
    return {
        name: (older, default) for name, (default, older) in PATHS.items()
        # worktrees are live checkouts, not settings: git moves one only by `git worktree move`.
        # Path() makes `.personas/cast/` and `.personas/cast` the same folder, as the loader already reads them.
        if older and name != "worktrees" and isinstance(raw.get(name), str) and Path(raw[name]) == Path(older)
        and ((root / older).exists() or (root / older).is_symlink())
    }


def tracked_files(root: Path, path: str) -> list[str]:
    # --literal-pathspecs: a file may be named `rule[ab].md`, and git would read that as a pattern
    listed = subprocess.run(
        ["git", "--literal-pathspecs", "-C", str(root), "ls-files", "-z", "--", path], capture_output=True, text=True, check=True,
    )
    return sorted(field for field in listed.stdout.split("\0") if field)


def rule_files(root: Path, folder: str) -> list[dict]:
    """Each tracked file of the rules folder, with whether it scopes itself to paths: a hint for the owner's split."""
    files = []
    for path in tracked_files(root, folder):
        file = root / path
        head = file.read_text(errors="replace").split("\n---", 1)[0] if file.is_file() and not file.is_symlink() else ""
        files.append({
            "file": Path(path).relative_to(folder).as_posix(), "link": file.is_symlink(),
            "scoped_to_paths": head.startswith("---") and bool(re.search(r"(?m)^paths:", head)),
        })
    return files


def cmd_migrate_plan(root: Path) -> None:
    found = linked(root)
    plan: dict = {"linked": {name: {"from": old, "to": new} for name, (old, new) in found.items()}}
    if "styleguide" in found and not (root / found["styleguide"][0]).is_symlink():
        plan["rules"] = rule_files(root, found["styleguide"][0])
    print(json.dumps(plan, indent=2))


def cmd_migrate_run(root: Path, styleguide: list[str] | None) -> None:
    """Move the linked folders under .lem. What can be checked is checked before the first move, and a
    step that still fails puts every file back where it was."""
    def git(*args: str, check: bool = True) -> str:
        # Every path here is one file or folder by its exact name. Without --literal-pathspecs git
        # reads `[`, `*` and `?` in a name as a pattern, and `add -f` would then stage another file
        # that matches it, an ignored one too.
        ran = subprocess.run(["git", "--literal-pathspecs", "-C", str(root), *args], capture_output=True, text=True, check=False)
        if check and ran.returncode != 0:
            raise SettingsError(f"git {' '.join(args[:2])} failed: {ran.stderr.strip()}")
        return ran.stdout

    settings = load(root)
    found = linked(root)
    if not found:
        raise SettingsError(f"no path in {SETTINGS} points at an older tool's folder: there is nothing to move")
    if git("status", "--porcelain").strip():
        raise SettingsError("the tree has changes of its own; commit or remove them first, so the move is the only change")
    branch = git("branch", "--show-current").strip()
    if not branch or branch == settings["branch"]["base"] or branch in settings["branch"]["protected"]:
        raise SettingsError(
            f"the move is a change like any other and lands through the gate: run it on a task's branch, not on {branch or 'a detached commit'}",
        )
    if not tracked_files(root, str(SETTINGS)):
        raise SettingsError(f"{SETTINGS} is not tracked by git, so the new paths could not land with the move; commit it first")
    text = original = (root / SETTINGS).read_text()
    for name, (old, _new) in found.items():
        if len(re.findall(rf'(?m)^{name} = "{re.escape(old)}/?"\s*$', text)) != 1:
            raise SettingsError(f'{SETTINGS}: expected one line `{name} = "{old}"` under [paths]; write it that way first')
        if (root / old).is_symlink():
            # moving a link moves the name and breaks where it points
            raise SettingsError(
                f"{old} is a link to {os.readlink(root / old)}: point {name} in {SETTINGS} at the real folder, "
                "or put the folder in the link's place, and run this again",
            )

    def free(target: Path, what: str) -> None:
        """Refuse a place that is taken, or whose parent is a file."""
        if target.exists() or target.is_symlink():
            raise SettingsError(f"{target.relative_to(root)} already exists, so {what} cannot move there; merge the two by hand first")
        for parent in target.relative_to(root).parents:
            if (root / parent).exists() and not (root / parent).is_dir():
                raise SettingsError(f"{parent} is a file, so nothing can be put under it; {what} cannot move to {target.relative_to(root)}")

    rules: list[str] = []
    if "styleguide" in found:
        folder, home = found["styleguide"]
        if styleguide is None:
            raise SettingsError(
                f"{folder} holds the project's rules, and only the ones about how code is written move: name them with --styleguide "
                "(`migrate plan` lists them), or pass --styleguide with no file to leave them all where they are",
            )
        known = {entry["file"]: entry for entry in rule_files(root, folder)}
        for file in styleguide:
            if styleguide.count(file) > 1:
                raise SettingsError(f"{file!r} is named twice")
            if file not in known or known[file]["link"]:
                raise SettingsError(f"{file!r} is not a tracked rule file of {folder}; `migrate plan` lists them")
            free(root / home / file, f"{folder}/{file}")
        rules = styleguide
    for name, (old, new) in found.items():
        if name != "styleguide":
            free(root / new, old)

    # What git tracks now is what it tracks after the move, at the new path, and nothing else is added.
    before = {name: tracked_files(root, old) for name, (old, _new) in found.items()}
    journal: list[tuple[str, Path, Path | None]] = []
    moved, links, left = [], [], []

    def make_parents(target: Path) -> None:
        missing = [parent for parent in reversed(target.relative_to(root).parents) if str(parent) != "." and not (root / parent).exists()]
        for parent in missing:
            (root / parent).mkdir()
            journal.append(("made", root / parent, None))

    def move(source: Path, target: Path) -> None:
        make_parents(target)
        # a rename of the folder itself, so files git ignores travel with it and stay unstaged
        os.rename(source, target)
        journal.append(("moved", source, target))

    def link(at: Path, to: Path) -> None:
        at.symlink_to(os.path.relpath(to, at.parent))
        journal.append(("linked", at, None))

    try:
        stage: list[str] = []
        unstage: list[str] = []
        for name, (old, new) in found.items():
            if name == "styleguide":
                for file in rules:
                    move(root / old / file, root / new / file)
                    # a link per file, so an agent that loads the old folder by itself still loads this rule
                    link(root / old / file, root / new / file)
                    links.append({"link": f"{old}/{file}", "to": f"{new}/{file}"})
                    unstage.append(f"{old}/{file}")
                    stage += [f"{new}/{file}", f"{old}/{file}"]
                if rules:
                    moved.append({"name": name, "from": old, "to": new, "files": rules})
                else:
                    left.append({"name": name, "at": old, "why": "no rule file was named"})
                continue
            move(root / old, root / new)
            moved.append({"name": name, "from": old, "to": new})
            unstage += before[name]
            stage += [new + file[len(old):] for file in before[name]]
        for entry in moved:
            text = re.sub(rf'(?m)^{entry["name"]} = "{re.escape(entry["from"])}/?"\s*$', f'{entry["name"]} = "{entry["to"]}"', text)
        journal.append(("settings", root / SETTINGS, None))
        (root / SETTINGS).write_text(text)
        stage.append(str(SETTINGS))
        for start in range(0, len(unstage), 200):
            git("rm", "-q", "--cached", "--", *unstage[start:start + 200])
        # -f: a file that was tracked stays tracked where an ignore rule covers its new place, and
        # a link the review tool needs is committed where the old folder was ignored
        for start in range(0, len(stage), 200):
            git("add", "-f", "--", *stage[start:start + 200])
        load(root)
    except (SettingsError, OSError) as error:
        for kind, path, other in reversed(journal):
            if kind == "linked":
                path.unlink(missing_ok=True)
            elif kind == "moved" and other is not None:
                os.rename(other, path)
            elif kind == "made":
                path.rmdir()
            elif kind == "settings":
                path.write_text(original)
        subprocess.run(["git", "-C", str(root), "reset", "-q"], capture_output=True, check=False)
        raise SettingsError(f"{error}\nevery file was put back where it was, and nothing is staged") from error

    # Every tracked file that still names an old path, the moved ones and the settings too: a builder
    # corrects them, the script does not guess. A link holds only its new target and never matches.
    mentions = {}
    for entry in moved:
        named = [f for f in git("grep", "-l", "-z", "-F", "-e", entry["from"], check=False).split("\0") if f]
        if named:
            mentions[entry["from"]] = named
    print(json.dumps({"branch": branch, "moved": moved, "links": links, "left": left, "mentions": mentions}, indent=2))


def state_root(root: Path) -> Path:
    """The folder task state lives in: inside the git directory every worktree shares."""
    common = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-common-dir"], capture_output=True, text=True, check=True,
    ).stdout.strip()
    return (root / common).resolve() / "lem"


def cmd_task_dir(root: Path, slug: str, ask: str | None, ticket: str | None) -> None:
    if not SLUG.fullmatch(slug):
        raise SettingsError(f"slug {slug!r} must be lower-case words joined by hyphens")
    if ask is not None and not ask.strip():
        raise SettingsError("--ask is the owner's words for this task, and they are empty")
    if ask is not None or ticket is not None:
        # This call opens a task. A slug whose task has ended keeps that task's files, its state and
        # what was done to its ticket: a new task under it would start with another task's record.
        ended = next((task["status"] for task in read_tasks(root) if task["slug"] == slug and task["status"] in ("landed", "dropped")), None)
        if ended:
            raise SettingsError(f"the task {slug!r} is {ended}; a new task takes a slug of its own: add a word to this one")
    if ticket is not None:
        if not TICKET.fullmatch(ticket):
            raise SettingsError(f"--ticket {ticket!r} is not a ticket's id, such as MBZ-12")
        ticket = ticket.upper()
        # one ticket is one task: a second task for it would be a second branch for the same work
        tasks = read_tasks(root)
        taken = next((task["slug"] for task in tasks if task["ticket"] == ticket and task["slug"] != slug and task["status"] != "dropped"), None)
        if taken:
            raise SettingsError(f"the task {taken!r} already holds the ticket {ticket}; go on with that task, or drop it first")
        mine = next((task["ticket"] for task in tasks if task["slug"] == slug), None)
        if mine and mine != ticket:
            # two tickets with one title would give one slug: the first task keeps its ticket
            raise SettingsError(f"the task {slug!r} already holds the ticket {mine}; give the task for {ticket} another slug")
    directory = state_root(root) / "tasks" / slug
    (directory / "reports").mkdir(parents=True, exist_ok=True)
    if ask is not None:
        # The owner's words, as given. task.md is a document with headings; the board and the
        # status show these words, so they have a file of their own that nothing rewrites.
        (directory / "ask.txt").write_text(ask.strip() + "\n")
    if ticket is not None:
        (directory / "ticket.txt").write_text(ticket + "\n")
    print(directory)


def cmd_ticket_step(root: Path, slug: str, step: str) -> None:
    """Write down one thing Lem did to the task's ticket, after the tracker took it."""
    directory = task_directory(root, slug)
    ticket = directory / "ticket.txt"
    if not ticket.is_file():
        raise SettingsError(f"the task {slug!r} came from no ticket")
    if step not in TICKET_STEPS:
        raise SettingsError(f"{step!r} is not a step{nearest(step, TICKET_STEPS)}")
    file = directory / "ticket-steps.txt"
    steps = file.read_text().split() if file.is_file() else []
    if step in steps:
        # the caller should have looked first: a step that is written down was done, and is not done again
        raise SettingsError(f"the step {step!r} is already written down for {ticket.read_text().strip()}: it was done, do not do it again")
    file.write_text("\n".join([*steps, step]) + "\n")
    print(json.dumps({"slug": slug, "ticket": ticket.read_text().strip(), "steps": [*steps, step]}))


def ask_of(directory: Path) -> str | None:
    """What the owner asked for: the words `task-dir --ask` kept, else the first words of task.md without their markup."""
    for name in ("ask.txt", "task.md"):
        file = directory / name
        lines = [line.strip() for line in file.read_text().splitlines() if line.strip()] if file.is_file() else []
        if lines:
            return " ".join(lines) if name == "ask.txt" else lines[0].lstrip("#> ").strip() or None
    return None


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

    # Worktrees hang off the main checkout, and this may run in one of them.
    path = main_checkout(root) / Path(settings["paths"]["worktrees"]["path"]).relative_to(root.resolve()) / slug
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
    append_event(root, "task.state", slug, {
        "status": status, "text": lines[0].strip(), "lines": [line.strip() for line in lines[1:]],
        "ask": ask_of(directory),
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


def ticket_owed(status: str | None, steps: list[str], tracker: dict | None) -> list[str]:
    """The steps a ticket still waits for, now that its task has ended. A session may be cut off
    between a task's last state and the tracker, and this is how the next one sees it."""
    if tracker is None:
        return []
    if status == "landed":
        wanted = ["commented", *(["landed"] if tracker["moves"] == "lem" else [])]
    elif status == "dropped":
        wanted = ["dropped"]
    else:
        wanted = []
    return [step for step in wanted if step not in steps]


def read_tasks(root: Path) -> list[dict]:
    tasks = []
    parent = state_root(root) / "tasks"
    for directory in sorted(d for d in (parent.iterdir() if parent.is_dir() else ()) if d.is_dir()):
        state = directory / "state.md"
        # state.md is newest block first; a block ends at the first blank line
        block = state.read_text().strip().split("\n\n")[0] if state.is_file() and state.read_text().strip() else None
        first = STATE_LINE.fullmatch(block.splitlines()[0]) if block else None
        known = first is not None and first["status"] in STATES
        tasks.append({
            "slug": directory.name,
            "ask": ask_of(directory),
            # the tracker's ticket the ask came from; a dropped task gives its ticket back
            "ticket": (directory / "ticket.txt").read_text().strip() or None if (directory / "ticket.txt").is_file() else None,
            # what Lem did to that ticket so far (TICKET_STEPS)
            "ticket_steps": (directory / "ticket-steps.txt").read_text().split() if (directory / "ticket-steps.txt").is_file() else [],
            "ticket_owed": [],
            # null when no block was written through `project.py state`: nobody can tell who acts next
            "status": first["status"] if known else None,
            "since": first["since"] if known else None,
            "state": block,
            # backlog items a closing pass proposed and the owner has not answered: they wait for
            # him also after the session that offered them is gone
            "proposed": sorted(f.name for f in (directory / "proposed").iterdir() if f.is_file()) if (directory / "proposed").is_dir() else [],
        })
    if any(task["ticket"] for task in tasks):
        # only a project with a ticket needs its settings here; a broken settings file then stops this, loudly
        tracker = load(root)["tracker"]
        for task in tasks:
            if task["ticket"]:
                task["ticket_owed"] = ticket_owed(task["status"], task["ticket_steps"], tracker)
    return tasks


def cmd_may_start(settings: dict, root: Path) -> None:
    """Exit 1 when as many tasks build or land as the project allows at one time."""
    limit = settings["flow"]["max_tasks"]
    running = [task["slug"] for task in read_tasks(root) if task["status"] in RUNNING]
    if len(running) >= limit:
        raise SettingsError(
            f"{len(running)} tasks build or land ({', '.join(running)}) and flow.max_tasks is {limit}: "
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
    commands.add_parser("reviewer").add_argument("words", nargs="+", metavar="AGENT|default")
    migrate = commands.add_parser("migrate")
    migrate.add_argument("step", choices=("plan", "run"))
    migrate.add_argument("--styleguide", nargs="*", metavar="FILE", help="the rule files that say how code is written here, relative to the rules folder")
    task_dir = commands.add_parser("task-dir")
    task_dir.add_argument("slug")
    task_dir.add_argument("--ask", help="the owner's words for this task, as given")
    task_dir.add_argument("--ticket", help="the id of the tracker's ticket the ask came from, e.g. MBZ-12")
    state = commands.add_parser("state")
    state.add_argument("slug")
    state.add_argument("status")
    state.add_argument("lines", nargs="+", metavar="LINE")
    commands.add_parser("tasks")
    step = commands.add_parser("ticket-step")
    step.add_argument("slug")
    step.add_argument("step")
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
        if args.command == "reviewer":
            cmd_reviewer(root, args.words)
            return
        if args.command == "migrate":
            if args.step == "plan":
                cmd_migrate_plan(root)
            else:
                cmd_migrate_run(root, args.styleguide)
            return
        if args.command == "existing":
            print(json.dumps(older_folders(root), indent=2))
            return
        if args.command == "task-dir":
            cmd_task_dir(root, args.slug, args.ask, args.ticket)
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
        if args.command == "ticket-step":
            cmd_ticket_step(root, args.slug, args.step)
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
