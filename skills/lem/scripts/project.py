#!/usr/bin/env python3
"""Say where one repository keeps what Lem reads, and what its flow settings are.

Every project keeps its own settings in its repository: what the project is, its style guide, its
personas, its review configuration, its lessons, the checks that gate a landing, and the paths
whose change takes the careful flow. `.lem/project.toml` at the root of the checkout names
them. A project that keeps a cast or a profile where an older tool already reads them
(`.personas`), or its worktrees, may point at them there (`init --existing link`), so adopting the skill moves
nothing, or start the skill's own layout beside them (`init --existing new`). Which of the two is
the owner's choice, so `init` refuses to guess it. The rules an agent already loads by itself
(`.claude/rules`) are no choice: they are the style guide, where they are.

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
    project.py rules [FILE ...] [--range BASE..TIP]
                                    the style guide files that cover these files, as JSON
    project.py task-dir SLUG [--ask TEXT] [--ticket ID]
                                    make and print one task's state directory; keep the owner's words
                                    and the ticket the ask came from
    project.py ticket-step SLUG started|commented|landed|dropped|answered
                                    write down what Lem did to the task's ticket, once
    project.py worktree-dir SLUG    print where the task's worktree goes, inside a folder git ignores
    project.py state SLUG STATUS LINE...
                                    put a new block at the top of the task's state.md, with the time
    project.py tasks                every task's ask, status and newest state block, as JSON
    project.py log SLUG EVENT [key=value ...] [key:=json ...]
                                    append one event about a task to the log the board draws
    project.py may-start SLUG       exit 1 when as many other tasks build or land as flow.max_tasks
                                    allows; the task SLUG, whose lead starts, is not counted
    project.py state-dir            the folder that holds every task, the event log and the night reports

Task state is kept inside the git directory every worktree shares: it is never committed, a
worktree's removal does not take it, and a session that replaces another finds it.

Every state block is also an event. `events.jsonl` in the state folder is the record, one JSON
object per line: `ts` (UTC to the second), `event`, `task`, then the event's fields. The same
record goes to `events.js` as a `lemEvent({...});` line, because the board is a file:// page: it
cannot read a file with fetch, and it can load a script (measured in agterm 0.34.0 by the monitor
this one follows). `state` writes `task.state` with the status, the lines, the ask, the limit and
the branch and newest commit of the task's worktree, so the board needs no agent to remember a
second command. `log` writes any other event: `key=value` stores a string and `key:=value` parses
JSON, so a commit made only of digits stays a string and an exit code stays a number. Four events
have a fixed form. `plan.talk.start`, which the defender of a careful or large plan writes when
the reviewer's seat opens, as `reviewer=AGENT`, so that the board draws the talk from its start.
`plan.talk`, which the landing reads and the plan's defender writes after the talk, as
`reviewer=AGENT turns:=N questions:=N settled:=N open:=N repaired:=N design:=N unargued:=N
root:=N layer:=N shared:=N`: the turns, the questions of the reviewer's first list, how many of
them were settled and left open (the two add up to questions), how many the defender repaired,
how many of the open ones are a design choice, how many were raised after the list and not
argued, how many repairs changed a decision of the plan and how many put a layer over a decision
with a cite (the two add up to at most the repairs), and how many decisions two questions named.
The rules of a talk keep it within 4 × questions + 2 turns; a record over that bound is taken as
it ran, and `log` adds the bound to it as `bound`, for the landing and the board to say that the
talk went over. `tasks` gives each task
its newest `plan.talk` as `talk`, the record Lem and a builder read before the build of a
careful or large plan.
And `stories.read`, which Lem or the lead writes after the personas read the stories, as
`by=lem|lead asked:=N answered:=N families:='["FAMILY", ...]' silent:='[{"name": ..., "why":
...}]' stories:=N flagged:=N split:=true|false digest=DIGEST`: who ran the read, how many personas
were asked and how many answered, the model families that answered, each source that did not
and why (a partial read counts), how many stories were read and how many an answer flagged,
whether the families split, and the digest `stories.py digest` gives for the stories read. A
read in which nobody answered is written too, with `answered:=0`, no family and each source that
was asked in `silent`; the landing counts two of those in a row as stories that went on unread.
`investigation`, which Lem writes after it reads the investigator's report of a bug or a
question, as `kind=bug|investigation call=CALL line=TEXT [where=PATH:SYMBOL]
[reproduced:=true|false]`: a bug's call is correction, usual, not-a-bug or not-reproduced, and it
says whether the bug was reproduced; a plain cause names its place; an investigation's call is
answer. `tasks` gives each task its newest as `investigation`, and `state SLUG answered` refuses
a task with no `investigation.md` and no record whose call is not-a-bug or answer.

A state line that starts with `kind:` names the kind of the request with its reason, as `kind:
bug, because the total is wrong today`, one of bug, feature, correction, investigation, chore and
docs; `state` refuses any other, and `tasks` gives the newest as `kind`.

`.lem/project.local.toml` is one person's or one day's choice on one machine: who sits in the
reviewer's pane (the usual reviewer is down, or out of tokens) and on which model the defender of
a plan talk runs, which tool marks up a plan and which one puts a question to the owner, and a no to the correction queue for that one person. It
is not committed (`init` writes `.lem/.gitignore` for it), and it is read from the main checkout,
because a task's worktree has no copy of a file git does not track. It may hold `[seats]` and
`[tools]`, and `[corrections]` with `collect = false`, and nothing else: the gate, the careful
paths, the protected branches and who lands are the project's rules, and a file nobody reviews
must not open them. For the same reason it can switch the correction queue off for its person
and never on: nobody's messages are sent because of a file that git does not show. `show` names each setting that
came from it.

The style guide is a folder of markdown files, in an adopted project the one an agent already
loads by itself (`.claude/rules`), which Lem reads and never moves; when `.lem/styleguide` holds
rules beside it, `rules` reads both folders, and `folders` in its answer names them. A file scopes itself to paths
in its frontmatter, in Claude Code's form (`paths:` with a list of globs), and a file without
that covers every path. `rules` is the one place that matches a change against those scopes: a
builder's brief, the message to the reviewer and a review round all get its answer, so an agent
that does not load the folder by itself reads the same rules as one that does.

A settings file with an unknown key, a wrong type or a path outside the repository is an error:
a stage that read half of it would run on defaults nobody chose. Needs Python 3.11 for tomllib.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"project.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; put a newer one first on PATH, or run this file with it")

import argparse
import difflib
import fnmatch
import json
import os
import re
import subprocess
import tomllib
from datetime import datetime, timezone
from pathlib import Path

# A role a developer may give to a tool of their own -> the tool Lem uses for it unless the
# settings say otherwise. The one place that names each. `lem-ask` comes with Lem; `webrev` is a
# recommended tool the developer installs (the machine check has its row and its guide).
TOOLS = {"annotate": "webrev", "ask": "lem-ask"}
SETTINGS = Path(".lem") / "project.toml"
LOCAL = Path(".lem") / "project.local.toml"
# the tables one machine may set for itself
LOCAL_TABLES = ("seats", "tools", "corrections")
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
# How a task that has a forge ends: a pull request there, or a merge into the base branch with
# none, for a developer who wants no pull requests. With no forge it is always the merge.
PROPOSE = ("pull-request", "merge")
# the agents that can sit in the reviewer's pane
REVIEWERS = ("claude", "codex")
# The reviewer's seat: the agent, and what its pane is started with. A model and an effort are
# not checked against a list: their names change with each release of an agent's command, and
# that command refuses a wrong one loudly when the pane starts.
SEAT = ("agent", "model", "effort", "plan_effort")
# The defender's seat: the agent Lem starts in the companion of a plan talk, which defends the
# plan against the reviewer. Only Claude Code, because the harness was checked in no other agent.
PLANNERS = ("claude",)
PLANNER_SEAT = ("agent", "model", "effort")
# seat -> (the keys it takes, the agents that may sit in it, why only those)
SEATS = {
    "reviewer": (SEAT, REVIEWERS, "the agents that can sit in the reviewer's pane"),
    "planner": (PLANNER_SEAT, PLANNERS, "the harness was checked in Claude Code only"),
}
# a task's slug: plain words joined by hyphens, e.g. report-dates-stay-whole
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
# What a task's newest state block may say, and who acts next:
#   queued    the ask is written and no lead runs yet: the limit was reached
#   building  a lead plans or builds
#   planned   the plan is committed and nothing builds it: it needs its talk, or a builder after the talk, or the owner reads it
#   held      it waits for the owner on what is no decision with options: the stories, one more fact, a
#             step of his, or an irreversible choice every task left needs; a decision of his is a choice
#   blocked   the lead stopped on something the coordinator has to settle
#   ready     the report is written and the branch waits for its checks
#   landing   the checks and the read run on it, or a builder repairs what they or the base showed
#   open      it is proposed: a pull request is open, or the branch is ready to land, and it waits for the merge
#   landed    it is on the base branch
#   drafted   a plan written at night that waits for the owner's word
#   dropped   nobody will build it
#   answered  it ended with a report and nothing to merge: a question answered, or a bug that is none
STATES = ("queued", "building", "planned", "held", "blocked", "ready", "landing", "open", "landed", "drafted", "dropped", "answered")
# The states a task does not leave: its files stay under its slug, and nothing of it waits.
ENDED = ("landed", "dropped", "answered")
# The kind of a request, which Lem takes from the ask's words alone (`stages/new.md`, "Open the task").
# A state line `kind: KIND, because WHY` says it; no code matches an ask's words against them.
KINDS = ("bug", "feature", "correction", "investigation", "chore", "docs")
KIND_LINE = re.compile(r"kind:\s*(?P<kind>[^,\s]+)\s*(?:,\s*because\s+(?P<why>.+))?")
# What the investigation of a bug or of a question found, as `log investigation` takes it: the call
# that sets the task's next path (`stages/new.md`, "A bug and an investigation"). Two of them end the
# task with its report, as `answered`.
CALLS = {"bug": ("correction", "usual", "not-a-bug", "not-reproduced"), "investigation": ("answer",)}
ANSWERING = ("not-a-bug", "answer")
# The states in which the task loads the machine: a lead builds, or the gate runs and a builder may
# repair a conflict or a red gate.
RUNNING = ("building", "landing")
# The first line of a state block: the time in UTC, the status, one line of text.
STATE_LINE = re.compile(r"(?P<since>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z) (?P<status>[a-z]+): (?P<text>.+)")
# How many tasks build or land at one time when the settings do not say. Four to five ran well on one Mac;
# six gave a load average of 12 to 16 and unstable browser tests (convertiser-server, as its owner
# reported it on 2026-11-14). The right number depends on the machine and on the project's tests.
MAX_TASKS = 4
# How many minutes a choice of the build waits for the owner before the recommended action is
# taken. The owner's own number: "if there is decision taken in 15 min" (2026-11-16).
DECISION_WAIT = 15
TABLES: dict[str, tuple[str, ...]] = {
    "paths": tuple(PATHS),
    "branch": ("base", "land", "history", "propose", "protected"),
    "gate": ("commands", "ignores", "setup", "bar"),
    "flow": ("careful", "topics", "max_tasks", "decision_wait"),
    "seats": ("reviewer", "planner"),
    "tools": tuple(TOOLS),
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
#   answered   the ticket got the comment with its task's answer: not a bug, or the answer to a question
TICKET_STEPS = ("started", "commented", "landed", "dropped", "answered")
# The ended states that give a task's ticket back: a new task may take it. A landed task keeps it.
RETURNED = ("dropped", "answered")

TEMPLATE = """\
# What Lem reads in this repository. `project.py show` prints it resolved.

[paths]
# Where each kind of setting lives, relative to the root of the checkout.
{paths}

[branch]
# The branch a task starts from and lands on.
base = "{base}"
# Who lands a finished task: "owner", or "agent", which lands only a request that is green and
# not careful; the owner lands every other one.
land = "owner"
# What lands: "keep" lands the branch's own commits, "squash" lands one commit for the whole task.
history = "keep"
# How a task ends where the remote is GitHub: "pull-request" opens one there, "merge" lands the
# branch on the remote's base branch with none. With any other remote, or none, it is the merge.
propose = "pull-request"
# Branches nothing lands on and nothing is pushed to through this skill, whoever asks.
protected = []

[gate]
# The machine checks that gate a landing, each run at the root of the task's worktree.
commands = []
# Paths the gate does not read. When the base branch moves after a green gate by these files
# only, the result stands; any other file means the gate runs again. A `*` crosses directories.
ignores = []
# What a fresh worktree of this project needs before its tests can start: install the packages,
# copy an environment file. The check that each story's tests fail on the base commit runs in a
# worktree of its own and runs these there first. Leave it empty when the tests start as they are.
setup = []

[flow]
# Paths whose change takes the careful flow: its plan is talked through with the reviewer before
# any code, in a companion session of its own, and the landing gives it the project's full
# review set. A `*` crosses directories.
careful = []
# What must not go wrong in this project, each as one sentence in the owner's words: "a price a
# customer pays", "data that cannot be rebuilt", "who may sign in". No code matches these: the
# lead of a task reads its plan against each, and a plan that touches one takes the careful flow
# whatever its paths.
topics = []
# How many tasks build or land at one time. Four to five ran well on one Mac; six gave a load
# average of 12 to 16 and unstable browser tests (convertiser-server, 2026-11-14). Lower it when
# the tests share one database or drive a browser.
max_tasks = {max_tasks}
# How many minutes a choice of the build waits for the owner before the lead takes the recommended
# option, and the pull request is not green for it. The owner's own number (2026-11-16).
decision_wait = {decision_wait}

[seats.reviewer]
# The agent in the reviewer's pane: "claude" or "codex". Lem's builders build; this one talks
# the plan of a careful or large task through with its defender, in the plan talk's companion.
# The same family twice is allowed.
{reviewer}
# What its pane starts with. Leave one out and the agent's own default holds.
# model = ""
# effort = ""        # for the review of a diff
# plan_effort = ""   # for the talk over a plan

[seats.planner]
# The agent that defends a careful or large plan in its talk with the reviewer, in a companion
# session Lem opens for the talk and closes after it. Only "claude" for now. Leave a line out and
# the agent's own default holds.
# agent = "claude"
# model = ""
# effort = ""

[corrections]
# Keep a queue of the owner's corrections for the retro. The hook that fills it sends each
# message the owner types, with the agent message it answers, to the Jev decision model. That
# is the owner's choice, so it is false until he says yes. `true` here, in git, is a yes for
# everybody who works in this repository with the hook: with Lem as a plugin the hook comes with
# the install, with links the owner registers it by one command of Lem's setup. One person says
# no for themselves with `collect = false` under [corrections] in .lem/project.local.toml.
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
# The skill or command the owner marks up a plan or a draft with. "{annotate}" is the one Lem
# recommends, a recipe of the agterm cookbook that you install; name your own instead.
annotate = "{annotate}"
# How a question that asks the owner to choose or to approve reaches him. "{ask}" comes with
# Lem and shows a page with the options side by side. "terminal" asks in the conversation, as a
# numbered list. Or name a skill or a command of your own.
ask = "{ask}"
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


def commands(value: object, where: str) -> list[str]:
    """A list of shell commands. An empty one runs nothing and exits 0, so a gate of it is green."""
    found = strings(value, where)
    if any(not item.strip() for item in found):
        raise SettingsError(f"{where} holds an empty command, which passes without running anything; take it out of the list")
    return found


def patterns(value: object, where: str) -> list[str]:
    """A list of regular expressions, each one read here so that a wrong one is named where it is written."""
    for item in strings(value, where):
        try:
            re.compile(item)
        except re.error as error:
            raise SettingsError(f"{where}: {item!r} is not a regular expression ({error})") from error
    return value


def inside(root: Path, relative: str, where: str) -> Path:
    if Path(relative).is_absolute():
        raise SettingsError(f"{where} = {relative!r} must be relative to the root of the checkout")
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise SettingsError(f"{where} = {relative!r} leaves the repository")
    if resolved == root.resolve():
        # every path names a folder or a file of its own: the root would read the whole checkout as
        # backlog items or rules, and a worktrees folder there ignores every file of the project
        raise SettingsError(f"{where} = {relative!r} names the root of the checkout; name a folder or a file inside it, or leave the line out for the default")
    return resolved


def main_checkout(root: Path) -> Path:
    """The checkout every worktree hangs off: the first entry git lists. A file git does not track lives only there."""
    # -z ends each field with a NUL: a path may hold a line break, and a split on lines would cut it
    listed = subprocess.run(["git", "-C", str(root), "worktree", "list", "--porcelain", "-z"], capture_output=True, text=True, check=False)
    first = next((field.removeprefix("worktree ") for field in listed.stdout.split("\0") if field.startswith("worktree ")), None)
    return Path(first) if first else root


def text_of(file: Path) -> str:
    """A text file Lem reads, as UTF-8. A file in another encoding is refused by name: read as
    the locale's, a settings file would mean something else on another machine."""
    try:
        return file.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise SettingsError(f"{file} is not UTF-8 text (byte {error.start} does not read); save it as UTF-8") from error


def unreadable_argument(argv: list[str]) -> str | None:
    """The first argument that is not UTF-8 text, as the message that names it; None when all are.
    Such an argument would stop the write of the file it goes into half way."""
    for arg in argv:
        try:
            arg.encode("utf-8")
        except UnicodeEncodeError:
            return f"the argument {os.fsencode(arg)!r} is not UTF-8 text; give it in UTF-8"
    return None


def toml_string(value: str) -> str:
    """A string as TOML writes it. JSON's own escapes would turn a character outside the basic plane into two halves TOML refuses."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + "".join(f"\\u{ord(c):04x}" if ord(c) < 0x20 or ord(c) == 0x7F else c for c in escaped) + '"'


def read_settings(file: Path, name: Path, tables: tuple[str, ...]) -> dict:
    """One settings file as a dict, with every table and key it may not hold refused."""
    if not file.is_file():
        return {}
    try:
        raw = tomllib.loads(text_of(file))
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


def seat(raw: dict, name: Path, which: str = "reviewer") -> dict | None:
    """The seat (`SEATS`) one file names, checked; None when the file names none."""
    keys, agents, why = SEATS[which]
    given = raw.get("seats", {}).get(which)
    if given is None:
        return None
    if not isinstance(given, dict):
        raise SettingsError(f'{name}: seats.{which} is a table: write [seats.{which}] and under it agent = "{agents[-1]}"')
    for key, value in given.items():
        if key not in keys:
            raise SettingsError(f"{name}: unknown key seats.{which}.{key}{nearest(key, keys)}")
        if not isinstance(value, str) or not value.strip():
            raise SettingsError(f"{name}: seats.{which}.{key} must be a word, not {value!r}; leave the line out for the agent's own default")
    if "agent" in given and given["agent"] not in agents:
        raise SettingsError(f"{name}: seats.{which}.agent = {given['agent']!r} must be {' or '.join(agents)}: {why}")
    if "agent" not in given and given:
        raise SettingsError(f"{name}: seats.{which} names a model or an effort and no agent; a model belongs to one agent")
    return {key: given.get(key) for key in keys}


def local_off(local: dict) -> bool:
    """Whether this machine's own file says no to the correction queue. It can say nothing else about it."""
    if "collect" not in local.get("corrections", {}):
        return False
    if local["corrections"]["collect"] is not False:
        raise SettingsError(
            f"{LOCAL}: corrections.collect = {local['corrections']['collect']!r} is not for this file. It may say `collect = false`, "
            f"which keeps one person's messages out of the queue; only {SETTINGS}, which everybody reads in git, switches the queue on",
        )
    return True


def tool_of(raw: dict, name: Path, role: str) -> str | None:
    """The tool one file names for a role, checked; None when the file names none."""
    if role not in raw.get("tools", {}):
        return None
    tool = raw["tools"][role]
    if not isinstance(tool, str) or not tool.strip():
        raise SettingsError(f'{name}: tools.{role} = {tool!r} must name a skill or a command in quotes, as in {role} = "{TOOLS[role]}"')
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
    if base is not None and not base.strip():
        raise SettingsError(f"{SETTINGS}: branch.base = {base!r} names no branch; write the branch tasks start from and land on, as base = \"main\"")
    land = branch.get("land", "owner")
    if land not in LAND:
        raise SettingsError(f"{SETTINGS}: branch.land = {land!r} must be one of {', '.join(LAND)}")

    history = branch.get("history", "keep")
    if history not in HISTORY:
        raise SettingsError(f"{SETTINGS}: branch.history = {history!r} must be one of {', '.join(HISTORY)}")
    propose = branch.get("propose", "pull-request")
    if propose not in PROPOSE:
        raise SettingsError(
            f"{SETTINGS}: branch.propose = {propose!r} must be one of {', '.join(PROPOSE)}: "
            '"pull-request" ends a task as a pull request on the forge, "merge" lands it on the base branch with none',
        )
    protected =strings(branch.get("protected", []), "branch.protected")
    if base in protected:
        raise SettingsError(f"{SETTINGS}: branch.base = {base!r} is in branch.protected, so no task could land")
    overridden = []
    tools = {}
    for role, own in TOOLS.items():
        tools[role] = tool_of(raw, SETTINGS, role) or own
        here = tool_of(local, LOCAL, role)
        if here is not None:
            tools[role] = here
            overridden.append(f"tools.{role}")

    # A local seat replaces the project's whole: its model and effort belong to the project's agent.
    seats = {}
    for which, (keys, _agents, _why) in SEATS.items():
        seats[which] = seat(raw, SETTINGS, which) or {key: None for key in keys}
        local_seat = seat(local, LOCAL, which)
        if local_seat is not None:
            seats[which] = local_seat
            overridden.append(f"seats.{which}")
    collect = raw.get("corrections", {}).get("collect", False)
    if not isinstance(collect, bool):
        raise SettingsError(f"{SETTINGS}: corrections.collect = {collect!r} must be true or false")
    if local_off(local):
        if collect:
            overridden.append("corrections.collect")
        collect = False
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
    decision_wait = raw.get("flow", {}).get("decision_wait", DECISION_WAIT)
    if isinstance(decision_wait, bool) or not isinstance(decision_wait, int) or decision_wait < 1:
        raise SettingsError(f"{SETTINGS}: flow.decision_wait = {decision_wait!r} must be a whole number of minutes, 1 or more")

    return {
        "root": str(root),
        # the checkout every worktree hangs off; it is `root` unless this ran in a task's worktree
        "main": str(main_checkout(root)),
        "settings": str(file) if file.is_file() else None,
        "paths": paths,
        "branch": {"base": base, "land": land, "history": history, "propose": propose, "protected": protected},
        "gate": {
            "commands": commands(raw.get("gate", {}).get("commands", []), "gate.commands"),
            "ignores": strings(raw.get("gate", {}).get("ignores", []), "gate.ignores"),
            "setup": commands(raw.get("gate", {}).get("setup", []), "gate.setup"),
            "bar": patterns(raw.get("gate", {}).get("bar", []), "gate.bar"),
        },
        "flow": {
            "careful": strings(raw.get("flow", {}).get("careful", []), "flow.careful"),
            "topics": strings(raw.get("flow", {}).get("topics", []), "flow.topics"),
            "max_tasks": max_tasks,
            "decision_wait": decision_wait,
        },
        "seats": seats,
        "tools": tools,
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
            if not relative.resolve().is_relative_to(root):
                raise SettingsError(f"{file} is not inside {root}; name files of this repository")
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
    found = subprocess.run(["git", "-C", settings["root"], "rev-parse", "--verify", "--quiet", f"refs/heads/{target}"], capture_output=True, text=True, check=False)
    if found.returncode != 0:
        raise SettingsError(f"branch.base = {target!r} is no branch of this repository; correct it in {SETTINGS}, or make the branch first")
    print(f"{target}: tasks land here; the {branch['land']} lands")


def default_branch(root: Path) -> str | None:
    head = subprocess.run(
        ["git", "-C", str(root), "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        capture_output=True, text=True, check=False,
    )
    return head.stdout.strip().removeprefix("origin/") if head.returncode == 0 else None


def rule_files(folder: Path) -> list[Path]:
    """Every .md below the folder, through links too, as the agent that loads such a folder by itself reads it."""
    found, seen = [], set()
    for where, folders, names in os.walk(folder, followlinks=True):
        real = os.path.realpath(where)
        if real in seen:
            folders[:] = []
            continue
        seen.add(real)
        folders.sort()
        found += [Path(where) / name for name in sorted(names) if name.endswith(".md")]
    return found


def older_folders(root: Path) -> dict[str, str]:
    """The settings an older tool already keeps here, where the skill's own layout has nothing yet."""
    found = {
        name: older for name, (default, older) in PATHS.items()
        if older and (root / older).exists() and not (root / default).exists()
    }
    # The rules an agent loads by itself are the style guide wherever they exist. An empty folder
    # of the skill's own layout beside them (a setup that stopped half way) does not hide them.
    # Files are compared by where they really are: one folder linked from the other, or rule
    # files linked between the two, is one set of rules. The settings name the agent's folder
    # unless the skill's own holds every file of it and more. Either way `rules` reads both
    # (`style_folders`), so two folders that each hold a file the other lacks are no refusal and
    # no move: "The rules of an existing project stay where they are" (the owner, 2026-11-15).
    own, rules = PATHS["styleguide"]
    found.pop("styleguide", None)
    if (root / rules).exists():
        ours = {os.path.realpath(file) for file in rule_files(root / own)}
        theirs = {os.path.realpath(file) for file in rule_files(root / rules)}
        if not theirs < ours:
            found["styleguide"] = rules
    return found


def style_folders(settings: dict) -> list[Path]:
    """The folders the style guide is read from: the one the settings name, and when that is the
    agent's rules folder or the skill's own, the other of the two where it exists too. A project
    may keep rules in both, and Lem moves no file between them."""
    # compared as the settings resolve a path, through links: a rules folder linked to the other is one folder
    root = Path(settings["root"])
    named = Path(settings["paths"]["styleguide"]["path"])
    pair = [(root / folder).resolve() for folder in PATHS["styleguide"]]
    if named not in pair:
        return [named]
    return [named, *(folder for folder in pair if folder != named and folder.is_dir())]


def cmd_init(root: Path, base: str | None, existing: str | None, reviewer: str | None) -> None:
    file = root / SETTINGS
    if file.exists():
        raise SettingsError(f"{SETTINGS} already exists; edit it")
    base = base or default_branch(root)
    if not base:
        raise SettingsError("cannot tell the base branch (no origin/HEAD); pass --base NAME")
    older = older_folders(root)
    # The rules an agent already loads by itself are never a choice: they stay, and they are the
    # style guide. Where the cast, the profile and the worktrees live is the owner's to say.
    choice = {name: path for name, path in older.items() if name != "styleguide"}
    if choice and existing is None:
        found = ", ".join(f"{name} in {path}" for name, path in choice.items())
        raise SettingsError(
            f"this repository already keeps {found}; pass --existing link to point at them, "
            "or --existing new to start the skill's own layout",
        )
    lines = []
    for name, (default, _older) in PATHS.items():
        chosen = older[name] if name in older and (name == "styleguide" or existing == "link") else default
        lines.append(f'{name} = "{chosen}"')
    file.parent.mkdir(exist_ok=True)
    agent = f'agent = "{reviewer}"' if reviewer else '# agent = "codex"'
    file.write_text(TEMPLATE.format(paths="\n".join(lines), base=base, reviewer=agent, max_tasks=MAX_TASKS, decision_wait=DECISION_WAIT, **TOOLS), encoding="utf-8")
    # one machine's own settings are never committed
    ignore = file.parent / ".gitignore"
    known = text_of(ignore).splitlines() if ignore.is_file() else []
    if LOCAL.name not in known:
        ignore.write_text("\n".join([*known, LOCAL.name]) + "\n", encoding="utf-8")
    print(file)


def cmd_reviewer(root: Path, words: list[str]) -> None:
    """Write, or with `default` remove, this machine's own reviewer seat."""
    file = main_checkout(root) / LOCAL
    local = read_settings(file, LOCAL, LOCAL_TABLES)
    # What the file already holds is checked before any of it is written again: a wrong value is
    # refused with its fix, and the file stays as the owner left it.
    for role in TOOLS:
        tool_of(local, LOCAL, role)
    local_off(local)
    seat(local, LOCAL, "planner")
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
            # a value here is a word in quotes, or the one `false` the corrections table may hold
            lines += ["", f"[{table}]", *(f"{key} = {'false' if value is False else toml_string(value)}" for key, value in plain.items())]
        for key, value in body.items():
            if isinstance(value, dict) and value:
                lines += ["", f"[{table}.{key}]", *(f"{k} = {toml_string(v)}" for k, v in value.items())]
    if len(lines) == 1:
        file.unlink(missing_ok=True)
    else:
        file.parent.mkdir(exist_ok=True)
        file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    resolved = load(root)
    print(json.dumps({"reviewer": resolved["seats"]["reviewer"], "local": resolved["local"]}, indent=2))


def braces(pattern: str) -> list[str]:
    """`*.{ts,tsx}` as `*.ts` and `*.tsx`, a group inside a group too. A brace with no comma stays as written."""
    depth, start = 0, 0
    for i, char in enumerate(pattern):
        if char == "{":
            if depth == 0:
                start = i
            depth += 1
        elif char == "}" and depth:
            depth -= 1
            if depth:
                continue
            parts, level, last = [], 0, start + 1
            for j in range(start + 1, i):
                level += (pattern[j] == "{") - (pattern[j] == "}")
                if pattern[j] == "," and level == 0:
                    parts.append(pattern[last:j])
                    last = j + 1
            parts.append(pattern[last:i])
            if len(parts) == 1:
                return [pattern[: i + 1] + rest for rest in braces(pattern[i + 1:])]
            return [done for part in parts for done in braces(pattern[:start] + part + pattern[i + 1:])]
    return [pattern]


def glob_regex(glob: str) -> re.Pattern[str]:
    """One glob of a rule file's `paths:` as a pattern over a path relative to the root.

    The forms Claude Code documents for `paths:` (its page on `.claude/rules`, read 2026-11-15):
    `**/*.ts` is every such file in any directory, `src/**/*` every file under `src/`, `*.md` the
    files of the root only, `src/components/*.tsx` the files of that one directory. So `*` and `?`
    stay inside one path segment, and `**` as a whole segment is any number of directories, none
    too. Not documented there, and matched here because a rule too many costs less than a rule
    missed: a name that starts with a dot, and a character class in brackets.
    """
    out, i = [], 0
    while i < len(glob):
        char = glob[i]
        whole = glob.startswith("**", i) and (i == 0 or glob[i - 1] == "/") and (i + 2 == len(glob) or glob[i + 2] == "/")
        if whole and i + 2 < len(glob):
            out.append("(?:.*/)?")
            i += 3
        elif whole:
            out.append(".*")
            i += 2
        elif char == "*":
            out.append("[^/]*")
            i += 1
        elif char == "?":
            out.append("[^/]")
            i += 1
        elif char == "[" and "]" in glob[i + 2:]:
            end = glob.index("]", i + 2)
            inner = glob[i + 1:end]
            inner = "^" + inner[1:] if inner[0] == "!" else inner
            out.append("[" + inner.replace("\\", "\\\\") + "]")
            i = end + 1
        else:
            out.append(re.escape(char))
            i += 1
    return re.compile("".join(out))


def rule_scope(file: Path, name: str) -> list[str] | None:
    """The globs a rule file scopes itself to, or None for one that covers every path.

    The one format read is Claude Code's: `paths:` in the file's frontmatter, as a list of globs.
    A `paths:` that names no glob is refused: whether the file then covers every path or none is
    not for a script to guess.
    """
    # utf-8-sig: a byte order mark before the first `---` must not turn a scoped rule into one for every path
    lines = file.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    def bare(text: str) -> str:
        """The text without a YAML comment: a `#` at the start or after a space, outside quotes."""
        quote = ""
        for i, char in enumerate(text):
            if quote:
                quote = "" if char == quote else quote
            elif char in "\"'":
                quote = char
            elif char == "#" and (i == 0 or text[i - 1].isspace()):
                return text[:i].strip()
        return text.strip()

    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        return None
    block = lines[1:end]
    at = next((i for i, line in enumerate(block) if re.match(r"paths\s*:", line)), None)
    if at is None:
        return None
    rest = bare(block[at].split(":", 1)[1])
    items: list[str] = []
    if rest.startswith("[") and rest.endswith("]"):
        level, last, quote = 0, 1, ""
        for j in range(1, len(rest) - 1):
            char = rest[j]
            if quote:
                quote = "" if char == quote else quote
            elif char in "\"'":
                quote = char
            elif char in "{}":
                level += 1 if char == "{" else -1
            elif char == "," and level == 0:
                items.append(rest[last:j])
                last = j + 1
        items.append(rest[last:-1])
    elif rest:
        items = [rest]
    else:
        for follow in block[at + 1:]:
            if not follow.strip() or follow.lstrip().startswith("#"):
                continue
            item = re.match(r"\s*-\s+(.*)$", follow)
            if item:
                items.append(bare(item.group(1)))
            elif follow[:1].isspace():
                raise SettingsError(f"{name}: a line under `paths:` is not a list item ({follow.strip()!r}); write each glob as `  - \"GLOB\"`")
            else:
                break
    globs = [item.strip() for item in items]
    globs = [glob[1:-1] if len(glob) > 1 and glob[0] == glob[-1] and glob[0] in "\"'" else glob for glob in globs]
    if not globs or not all(globs):
        raise SettingsError(f"{name}: its `paths:` names no glob; write each glob under it as `  - \"GLOB\"`, or take the line out so the file covers every path")
    return globs


def cmd_rules(settings: dict, files: list[str], commits: str | None) -> None:
    """The style guide files that cover the given files: one match for every reader of the rules."""
    root = Path(settings["root"]).resolve()
    changed = []
    for file in files:
        # One file has one answer, however it is named. Its folder is resolved the way the file
        # system reads it, a link first and `..` after it: `alias/../x` is beside what `alias`
        # points at. The last name is kept as written, since the file may be a link or be gone.
        full = root / file
        if full == root or full.name in ("", ".", ".."):
            raise SettingsError(f"{file} does not name a file; name the files a change touches")
        full = Path(os.path.realpath(full.parent)) / full.name
        if not full.is_relative_to(root) or full == root:
            raise SettingsError(f"{file} is not inside {root}; name files of this repository")
        changed.append(full.relative_to(root).as_posix())
    if commits:
        # --no-renames: a file that moved counts under its old path and its new one, each with its rules
        listed = subprocess.run(["git", "-C", str(root), "diff", "--name-only", "--no-renames", "-z", commits], capture_output=True, text=True, check=False)
        if listed.returncode != 0:
            raise SettingsError(f"git diff --name-only {commits} failed: {listed.stderr.strip()}")
        changed += [name for name in listed.stdout.split("\0") if name]
    changed = sorted(set(changed))
    if not files and not commits:
        raise SettingsError("rules needs the files a change touches: name them, or pass --range BASE..TIP")
    folders = style_folders(settings)
    folder = folders[0]
    # Each file once by where it really is, so a file linked into both folders is one rule. Two
    # files of one name, one in each folder, are two files: both are read, the named folder's first.
    rules, seen, files_read = [], set(), []
    for one in folders:
        for file in rule_files(one):
            if os.path.realpath(file) not in seen:
                seen.add(os.path.realpath(file))
                files_read.append(file)
    for file in files_read:
        shown = file.relative_to(root).as_posix() if file.is_relative_to(root) else str(file)
        globs = rule_scope(file, shown)
        if globs is None:
            rules.append({"file": str(file), "scope": "every path"})
            continue
        try:
            patterns = [(glob, glob_regex(one)) for glob in globs for one in braces(glob.removeprefix("./"))]
        except re.error as error:
            raise SettingsError(f"{shown}: a glob of its `paths:` does not read as a pattern ({error}); correct it, most likely a `[` with no `]` or a range that runs backwards") from error
        covers = sorted({name for name in changed for _, pattern in patterns if pattern.fullmatch(name)})
        if covers:
            rules.append({"file": str(file), "scope": sorted({glob for glob, pattern in patterns if any(pattern.fullmatch(name) for name in changed)}), "covers": covers})
    print(json.dumps({"styleguide": str(folder), "exists": folder.is_dir(), "folders": [str(one) for one in folders], "files": changed, "rules": rules}, indent=2))


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
        ended = next((task["status"] for task in read_tasks(root) if task["slug"] == slug and task["status"] in ENDED), None)
        if ended:
            raise SettingsError(f"the task {slug!r} is {ended}; a new task takes a slug of its own: add a word to this one")
    if ticket is not None:
        if not TICKET.fullmatch(ticket):
            raise SettingsError(f"--ticket {ticket!r} is not a ticket's id, such as MBZ-12")
        ticket = ticket.upper()
        # one ticket is one task: a second task for it would be a second branch for the same work
        tasks = read_tasks(root)
        taken = next((task["slug"] for task in tasks if task["ticket"] == ticket and task["slug"] != slug and task["status"] not in RETURNED), None)
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
        (directory / "ask.txt").write_text(ask.strip() + "\n", encoding="utf-8")
    if ticket is not None:
        (directory / "ticket.txt").write_text(ticket + "\n", encoding="utf-8")
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
    steps = text_of(file).split() if file.is_file() else []
    if step in steps:
        # the caller should have looked first: a step that is written down was done, and is not done again
        raise SettingsError(f"the step {step!r} is already written down for {text_of(ticket).strip()}: it was done, do not do it again")
    file.write_text("\n".join([*steps, step]) + "\n", encoding="utf-8")
    print(json.dumps({"slug": slug, "ticket": text_of(ticket).strip(), "steps": [*steps, step]}))


def ask_of(directory: Path) -> str | None:
    """What the owner asked for: the words `task-dir --ask` kept, else the first words of task.md without their markup."""
    for name in ("ask.txt", "task.md"):
        file = directory / name
        lines = [line.strip() for line in text_of(file).splitlines() if line.strip()] if file.is_file() else []
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
        ignore.write_text("*\n", encoding="utf-8")
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
    try:
        line.encode("utf-8")
    except UnicodeEncodeError as error:
        # a `key:=json` value may spell a lone surrogate, "\udcff", which no UTF-8 file can hold
        raise SettingsError(f"a field of the event is not UTF-8 text ({line[max(0, error.start - 20):error.start]!r} comes before it); give its text in UTF-8") from error
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
    for line in lines:
        kind_line(line)
    if status == "answered":
        answered_form(root, directory, slug)
    # the time is the clock's, never a writer's estimate
    since = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    block = "\n".join([f"{since} {status}: {lines[0].strip()}", *(line.strip() for line in lines[1:])])
    file = directory / "state.md"
    older = text_of(file).strip() if file.is_file() else ""
    fresh = directory / "state.md.new"
    fresh.write_text(block + ("\n\n" + older if older else "") + "\n", encoding="utf-8")
    fresh.replace(file)
    append_event(root, "task.state", slug, {
        "status": status, "text": lines[0].strip(), "lines": [line.strip() for line in lines[1:]],
        "ask": ask_of(directory),
        "limit": settings["flow"]["max_tasks"], **task_worktree(root, settings, slug),
    })
    print(json.dumps({"slug": slug, "status": status, "since": since}))


def kind_line(line: str) -> dict | None:
    """The kind of the request, when the line names one: `kind: bug, because the total is wrong
    today`. The status and the board read it, so a line that starts with `kind:` has this form."""
    if not line.strip().startswith("kind:"):
        return None
    found = KIND_LINE.fullmatch(line.strip())
    kind = found["kind"] if found else line.strip().removeprefix("kind:").strip()
    if kind not in KINDS:
        raise SettingsError(f"{kind!r} is not a kind of request{nearest(kind, KINDS)}; a kind line reads `kind: KIND, because WHY`")
    if not found or not found["why"]:
        raise SettingsError(f"the line {line.strip()!r} names the kind without its reason: write it as `kind: {kind}, because ...`")
    return {"kind": kind, "why": found["why"].strip()}


def answered_form(root: Path, directory: Path, slug: str) -> None:
    """A task is answered only when it has something to show: the investigation's report in its
    directory, and a record of it whose call ends the task (a question answered, a bug that is none)."""
    if not (directory / "investigation.md").is_file():
        raise SettingsError(
            f"the task {slug!r} has no investigation.md in its directory: an answered task ends with its report; "
            "write the investigator's report there first",
        )
    found = newest_events(root, "investigation").get(slug)
    if not found or found.get("call") not in ANSWERING:
        said = f"its newest says {found.get('call')!r}" if found else "it has none"
        raise SettingsError(
            f"the task {slug!r} is answered only after a record whose call is not-a-bug or answer (`log {slug} investigation ...`); {said}",
        )


def investigation_form(fields: dict) -> None:
    """What the investigation of a bug or of a question found, which Lem writes after it reads the
    report: the kind, the call that sets the next path, one line (the cause, the answer, or what was
    tried), the cause's place, and for a bug whether it was reproduced."""
    form = "investigation takes kind=bug|investigation call=CALL line=TEXT [where=PATH:SYMBOL] [reproduced:=true|false, for a bug]"
    allowed = {"kind", "call", "line", "where", "reproduced"}
    if not {"kind", "call", "line"} <= set(fields) <= allowed:
        raise SettingsError(f"{form}, and nothing else; this one has {', '.join(sorted(fields)) or 'no field'}")
    kind, call = fields["kind"], fields["call"]
    if kind not in CALLS:
        raise SettingsError(f"{form}: kind is bug or investigation, not {kind!r}")
    if call not in CALLS[kind]:
        raise SettingsError(f"{form}: call is correction, usual, not-a-bug or not-reproduced for a bug, and answer for an investigation; this one is {call!r} for a {kind}")
    if not isinstance(fields["line"], str) or not fields["line"].strip() or "\n" in fields["line"]:
        raise SettingsError(f"{form}: line is one line of text: the cause, the answer, or what was tried")
    if "where" in fields and (not isinstance(fields["where"], str) or not fields["where"].strip()):
        raise SettingsError(f"{form}: where is the cause's file and symbol, as path:symbol")
    if kind == "investigation" and "reproduced" in fields:
        raise SettingsError(f"{form}: reproduced is a bug's; an investigation answers a question and reproduces nothing")
    if kind == "bug":
        if not isinstance(fields.get("reproduced"), bool):
            raise SettingsError(f"{form}: a bug's record says whether it was reproduced, as reproduced:=true or reproduced:=false, written with :=")
        if call in ("correction", "usual") and not fields.get("where"):
            raise SettingsError(f"{form}: a plain cause has a place: where names the cause's file and symbol")
        if call == "not-reproduced" and fields["reproduced"]:
            raise SettingsError(f"{form}: not-reproduced is a bug that was not reproduced, and this record says it was")


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
    if event == "plan.talk.start":
        talk_start_form(fields)
    if event == "plan.talk":
        talk_form(fields)
        # the bound its rules give, beside the record, so that a reader says when the talk went over it
        fields["bound"] = TURNS_PER_QUESTION * fields["questions"] + TURNS_AROUND
    if event == "stories.read":
        read_form(fields)
    if event == "investigation":
        investigation_form(fields)
    print(json.dumps(append_event(root, event, slug, fields)))


def read_form(fields: dict) -> None:
    """The personas' read of the stories is read by the landing, so it has one form: who ran it,
    how many personas were asked and how many answered, the model families that answered, each
    source that did not answer and why, how many stories were read and flagged, whether the
    families split, and the digest of the stories it read (`stories.py digest`)."""
    form = (
        "stories.read takes by=lem|lead asked:=N answered:=N families:='[\"FAMILY\", ...]' "
        "silent:='[{\"name\": SOURCE, \"why\": WHY}, ...]' stories:=N flagged:=N split:=true|false digest=DIGEST"
    )
    counts = ("asked", "answered", "stories", "flagged")
    if set(fields) != {"by", "families", "silent", "split", "digest", *counts}:
        raise SettingsError(f"{form}, and nothing else; this one has {', '.join(sorted(fields)) or 'no field'}")
    if fields["by"] not in ("lem", "lead"):
        raise SettingsError(f"{form}: by is lem, when Lem ran the read in its session, or lead, when the task's lead ran it")
    if not all(isinstance(fields[key], int) and not isinstance(fields[key], bool) and fields[key] >= 0 for key in counts):
        raise SettingsError(f"{form}: each N is a whole number, written with := so that it stays one")
    families = fields["families"]
    if not isinstance(families, list) or not all(isinstance(name, str) and name.strip() for name in families) or len(set(families)) != len(families) \
            or (fields["answered"] and not families):
        raise SettingsError(f"{form}: families is the list of the model families that answered, each named once, as in families:='[\"opus\", \"sol\"]'")
    silent = fields["silent"]
    if not isinstance(silent, list) or not all(
        isinstance(item, dict) and set(item) == {"name", "why"} and all(isinstance(value, str) and value.strip() for value in item.values()) for item in silent
    ):
        raise SettingsError(f"{form}: silent is a list of {{\"name\": ..., \"why\": ...}}, one for each source that did not answer; [] when every one did")
    if not isinstance(fields["split"], bool):
        raise SettingsError(f"{form}: split is true when the two families answered a story differently, false otherwise, written with :=")
    if not isinstance(fields["digest"], str) or not re.fullmatch(r"[0-9a-f]{12}", fields["digest"]):
        raise SettingsError(f"{form}: digest is the twelve characters `stories.py digest` prints for the stories that were read")
    # every project's cast has two people or more
    if fields["asked"] < 2:
        raise SettingsError(f"{form}: a read asks two personas at the least")
    if fields["answered"] > fields["asked"]:
        raise SettingsError(f"{form}: answered is at most asked; 0 is a read in which nobody answered")
    # A read in which nobody answered is written down too, and started once more: the landing
    # counts two in a row as the stories going on unread, and the request as not green.
    if fields["answered"] == 0 and (families or fields["flagged"] or fields["split"] or len(silent) < fields["asked"]):
        raise SettingsError(
            f"{form}: a read in which nobody answered has families:='[]', flagged:=0 and split:=false, "
            "and silent names each source that was asked, one for each persona at the least, with why",
        )
    if fields["answered"] < fields["asked"] and not silent:
        raise SettingsError(f"{form}: when fewer answered than were asked, silent names each source that did not, with why")
    if fields["stories"] < 1 or fields["flagged"] > fields["stories"]:
        raise SettingsError(f"{form}: a read has one story at the least, and no more stories flagged than it read")
    if fields["split"] and len(families) < 2:
        raise SettingsError(f"{form}: a split is between two model families, and families names one")


def talk_start_form(fields: dict) -> None:
    """The start of a plan talk, written when the reviewer's seat opens, so that the board can draw
    the talk's minutes from two events: it names the reviewer, and nothing else."""
    if set(fields) != {"reviewer"} or not isinstance(fields["reviewer"], str) or not fields["reviewer"].strip():
        raise SettingsError(f"plan.talk.start takes reviewer=AGENT, and nothing else; this one has {', '.join(sorted(fields)) or 'no field'}")


# The most turns a talk of N questions has by its rules: the reviewer's list, two answers of the defender
# and two of the reviewer on each question (a question that holds a second time stops), and the close.
# Derived from the rules of `stages/plan.md` step 4, in a Fable second opinion (2026-11-16); no talk
# under these rules has been measured yet. It is the defender's to keep, not a check of the record: a
# talk that ran longer is written as it ran, and `log` adds the bound to it, so the pull request and
# the board can say that it went over.
TURNS_PER_QUESTION = 4
TURNS_AROUND = 2


def talk_form(fields: dict) -> None:
    """A plan talk's record is read by the landing, so it has one form: who argued the plan with its
    defender, how many turns the talk had, how many questions the reviewer's first list held, how many
    of them it settled and left open, how many the lead repaired, how many of the open ones are a
    design choice (a question that held a second time), how many questions were raised after the
    list and not argued, and three counts of Fable's check for a layer of patches (2026-11-16):
    `root`, the repairs that changed a decision of the plan; `layer`, the repairs that put a
    mechanism over a decision the plan cites (a story, a ruling, existing code) and stayed; and
    `shared`, the decisions two questions named."""
    form = "plan.talk takes reviewer=AGENT turns:=N questions:=N settled:=N open:=N repaired:=N design:=N unargued:=N root:=N layer:=N shared:=N"
    counts = ("turns", "questions", "settled", "open", "repaired", "design", "unargued", "root", "layer", "shared")
    if set(fields) != {"reviewer", *counts}:
        raise SettingsError(f"{form}, and nothing else; this one has {', '.join(sorted(fields)) or 'no field'}")
    if not isinstance(fields["reviewer"], str) or not fields["reviewer"].strip():
        raise SettingsError(f"{form}: reviewer names the agent that argued the plan with its defender")
    if not all(isinstance(fields[key], int) and not isinstance(fields[key], bool) and fields[key] >= 0 for key in counts):
        raise SettingsError(f"{form}: each N is a whole number, written with := so that it stays one")
    turns, questions = fields["turns"], fields["questions"]
    # A floor against an empty record, not a measure of a good talk. A reviewer that found nothing
    # says so in its first turn, and the defender closes: a talk of no question has those two turns.
    if turns < 2:
        raise SettingsError(f"{form}: a talk has two turns at the least: the reviewer's list, which may be empty, and the close")
    if questions == 0 and fields["unargued"] and turns <= TURNS_AROUND:
        raise SettingsError(f"{form}: a talk of no question and two turns has no turn after the list, so unargued is 0")
    if fields["settled"] + fields["open"] != questions:
        raise SettingsError(f"{form}: each question of the reviewer's first list ends settled or left open, so settled and open add up to questions")
    if fields["design"] > fields["open"]:
        raise SettingsError(f"{form}: a design choice is a question left open because it held a second time, so design is at most open")
    if fields["repaired"] > questions:
        raise SettingsError(f"{form}: repaired counts the questions whose answer changed the plan, so repaired is at most questions")
    if fields["root"] + fields["layer"] > fields["repaired"]:
        raise SettingsError(
            f"{form}: a repair either changed a decision of the plan (root) or put a mechanism over a decision with a cite (layer), "
            "or neither, so root and layer add up to at most repaired",
        )
    # No check of the rules themselves: a talk over its bound of turns, or one whose second question on
    # a decision did not close as a design choice, is a fact, and a record refused for it would leave
    # the companion open and the request unproposed for ever.


def ticket_owed(status: str | None, steps: list[str], tracker: dict | None) -> list[str]:
    """The steps a ticket still waits for, now that its task has ended. A session may be cut off
    between a task's last state and the tracker, and this is how the next one sees it."""
    if tracker is None:
        return []
    if status == "landed":
        wanted = ["commented", *(["landed"] if tracker["moves"] == "lem" else [])]
    elif status in RETURNED:
        # the comment of the tracker's "drop" or "answer", and no status: where it goes is the owner's call
        wanted = [status]
    else:
        wanted = []
    return [step for step in wanted if step not in steps]


def proposal(directory: Path) -> dict | None:
    """What `land.py propose` kept for a task: the pull request's address, when there is one, and green or the reasons it is not."""
    kept_file = directory / "landing.json"
    if not kept_file.is_file():
        return None
    try:
        kept = json.loads(text_of(kept_file))
    except ValueError as error:
        raise SettingsError(f"{kept_file} does not read as JSON ({error}); it is the landing's own record, written by land.py") from error
    if not kept.get("proposed"):
        return None
    reasons = kept.get("not_green", [])
    return {"pull_request": (kept.get("pr") or {}).get("url"), "green": not reasons, "not_green": reasons}


def newest_events(root: Path, event: str) -> dict[str, dict]:
    """Each task's newest event of one name in the event log. Lem closes a talk's companion, and a
    builder leads the build of a careful or large plan, only on the newest `plan.talk`, never on a
    line that says so; Lem takes a bug's next path on the newest `investigation`."""
    log, found = state_root(root) / "events.jsonl", {}
    if not log.is_file():
        return found
    for number, line in enumerate(text_of(log).splitlines(), 1):
        if f'"{event}"' not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError as error:
            raise SettingsError(f"{log}:{number} does not read as JSON ({error}); the log is written by project.py, never by hand") from error
        if record.get("event") == event:
            found[record.get("task")] = record
    return found


def kind_of(text: str) -> dict | None:
    """The newest kind of the request that a block of state.md names (newest block first)."""
    for line in text.splitlines():
        try:
            found = kind_line(line)
        except SettingsError:
            # state wrote every kind line in its form; a line written by hand that is not is no kind
            continue
        if found:
            return found
    return None


def read_tasks(root: Path) -> list[dict]:
    tasks = []
    talks = newest_events(root, "plan.talk")
    investigations = newest_events(root, "investigation")
    parent = state_root(root) / "tasks"
    for directory in sorted(d for d in (parent.iterdir() if parent.is_dir() else ()) if d.is_dir()):
        state = directory / "state.md"
        # state.md is newest block first; a block ends at the first blank line
        written = text_of(state) if state.is_file() else ""
        block = written.strip().split("\n\n")[0] if written.strip() else None
        first = STATE_LINE.fullmatch(block.splitlines()[0]) if block else None
        known = first is not None and first["status"] in STATES
        tasks.append({
            "slug": directory.name,
            "ask": ask_of(directory),
            # the tracker's ticket the ask came from; a dropped or answered task gives its ticket back
            "ticket": text_of(directory / "ticket.txt").strip() or None if (directory / "ticket.txt").is_file() else None,
            # what Lem did to that ticket so far (TICKET_STEPS)
            "ticket_steps": text_of(directory / "ticket-steps.txt").split() if (directory / "ticket-steps.txt").is_file() else [],
            "ticket_owed": [],
            # null when no block was written through `project.py state`: nobody can tell who acts next
            "status": first["status"] if known else None,
            "since": first["since"] if known else None,
            "state": block,
            # what the landing proposed to the owner, for the status and the board: where, and green or why not
            "proposal": proposal(directory),
            # the newest record of its plan talk, as `log plan.talk` wrote it, or null when it had none
            "talk": talks.get(directory.name),
            # the kind of the request with its reason, from the newest block that names it, or null
            "kind": kind_of(written),
            # what the investigation of a bug or a question found, as `log investigation` wrote it last, or null
            "investigation": investigations.get(directory.name),
        })
    if any(task["ticket"] for task in tasks):
        # only a project with a ticket needs its settings here; a broken settings file then stops this, loudly
        tracker = load(root)["tracker"]
        for task in tasks:
            if task["ticket"]:
                task["ticket_owed"] = ticket_owed(task["status"], task["ticket_steps"], tracker)
    return tasks


def cmd_may_start(settings: dict, root: Path, slug: str) -> None:
    """Exit 1 when as many other tasks build or land as the project allows at one time. The task
    whose lead starts is not counted: when it builds already (its investigator called the path, or
    its lead stopped and starts again), the place it holds is the one its next lead takes."""
    task_directory(root, slug)
    limit = settings["flow"]["max_tasks"]
    running = [task["slug"] for task in read_tasks(root) if task["status"] in RUNNING and task["slug"] != slug]
    if len(running) >= limit:
        raise SettingsError(
            f"{len(running)} tasks build or land ({', '.join(running)}) and flow.max_tasks is {limit}: "
            f"write the state of {slug} as `queued` and start it when one of them stops; "
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
    rules = commands.add_parser("rules")
    rules.add_argument("files", nargs="*", metavar="FILE")
    rules.add_argument("--range", dest="commits", metavar="BASE..TIP", help="also the files this range of commits changes")
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
    commands.add_parser("may-start").add_argument("slug")
    commands.add_parser("state-dir")
    args = parser.parse_args()
    if problem := unreadable_argument(sys.argv[1:]):
        sys.exit(f"project.py: {problem}")
    try:
        root = repo_root(Path(args.repo))
        if args.command == "init":
            cmd_init(root, args.base, args.existing, args.reviewer)
            return
        if args.command == "reviewer":
            cmd_reviewer(root, args.words)
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
        if args.command == "rules":
            cmd_rules(settings, args.files, args.commits)
            return
        if args.command == "show":
            print(json.dumps(settings, indent=2))
        elif args.command == "path":
            cmd_path(settings, args.name)
        elif args.command == "worktree-dir":
            cmd_worktree_dir(settings, args.slug)
        elif args.command == "may-land":
            cmd_may_land(settings, args.branch)
        elif args.command == "may-start":
            cmd_may_start(settings, root, args.slug)
        else:
            cmd_careful(settings, args.files)
    except SettingsError as error:
        sys.exit(f"project.py: {error}")


if __name__ == "__main__":
    main()
