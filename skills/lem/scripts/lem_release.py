"""The release a task began on, and the rule that stops a command for a task two releases back.

Each task keeps the release it began on: `release.txt` in its task directory, one line, which
`lem project task-dir` writes when it opens the task (`mark`). It is the release that the project's
sessions load, from Claude Code's list of installs (`chosen`): the install for the project's main
checkout, else the install for the user, else this Lem's own, and never newer than this Lem's own.
The board server runs the newest Lem of the Mac for every project, while each project's sessions
load the release installed for it, so a mark of the board's own release would stop a task it opens
for a project one release behind at its session's first step. A task with no mark began on
`UNMARKED`, the release before marks were written.

A release reads the records of its own release and of the release just before it (`BEFORE`), and no
older ones. `BEFORE` is one constant, which each release moves: the installed folder has no git, and
a number does not say which release came before it (0.1.6, then 0.2.0). `tests/lem-machine.sh`
checks it against the history of `plugin.json`.

Each command of Lem that acts on one named task runs `check` first (`stop` is the rule):

- a mark of this release, of `BEFORE`, or between the two: the command goes on;
- a mark newer than this release: the command stops with exit 1 and names the update, and it writes
  nothing, since its caller is the older Lem;
- a mark older than `BEFORE`: the command logs `release.stop` once and stops with exit 1. The event
  holds the release the task began on (`began`), this one (`running`), the task's branch as git
  names it (`branch`) and the message (`say`); the board shows the task blocked from it, and the
  task's state stays the one its own work wrote, which every script that ends a task reads. A
  command that ends a task (a drop, the end of a merge) passes: it logs the same event once, so that
  a drop that is the task's first command on this release leaves the event that `resume` reads, and
  goes on.

A command that passed opens the way for the commands it runs in this process for the same task
(`lem_sibling`): `lem land merged` writes `landed` through `lem project state` and logs through `lem
project log`. Each script's `main` runs under `one_command`, which keeps that within the one command:
the board server runs many commands in its one process, and a pass of one is no pass of the next.
"""

import contextlib
import contextvars
import functools
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import lem_state

# The release just before the version of plugin.json. A release moves it (AGENTS.md, "A release").
BEFORE = "0.3.0"
# The release of a task whose directory holds no mark: the tasks that ran when marks came.
UNMARKED = "0.3.1"
# The mark, in the task directory.
MARK = "release.txt"
# The event an old task's stop logs.
STOP = "release.stop"
# The three ends of a task, whose state a passing command writes after the stop (project.py ENDED).
ENDS = ("landed", "dropped", "answered")
# The plugin's folder, three above this file's (skills/lem/scripts/), and its manifest.
ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
# The names of Claude Code's install scopes: one for a project's checkout, one for every project.
PROJECT_SCOPES = ("project", "local")
USER_SCOPES = ("user", "managed")
UPDATE = "/plugin marketplace update lem"

# The task directories a command of this process has passed already, while one runs (`one_command`).
CLEARED: contextvars.ContextVar[frozenset | None] = contextvars.ContextVar(
    "lem_release_cleared", default=None
)


def numbers(version: object) -> tuple[int, ...] | None:
    """`0.3.0` as (0, 3, 0); None for anything that is not numbers joined by dots."""
    parts = str(version).strip().split(".") if isinstance(version, str) else []
    return (
        tuple(int(part) for part in parts)
        if parts and all(part.isdigit() for part in parts)
        else None
    )


def stop(slug: str, began: str, version: str, before: str) -> dict | None:
    """The rule: None when a command of Lem VERSION goes on with the task SLUG begun on BEGAN, else
    the stop, `{"kind": "old"|"new", "say": MESSAGE}`. BEFORE is the release just before VERSION."""
    mark, now, prior = numbers(began), numbers(version), numbers(before)
    if mark is None or now is None or prior is None:
        raise ValueError(
            f"a release is numbers joined by dots, as 0.3.0: {began!r}, {version!r}, {before!r}"
        )
    if mark > now:
        return {
            "kind": "new",
            "say": f"{slug} began on Lem {began}, which is newer than this Lem, {version}, so this Lem does nothing with it. "
            f"{UPDATE} in Claude Code brings the newer release, and a new session of the project loads it",
        }
    if mark < prior:
        return {
            "kind": "old",
            "say": f"{slug} began on Lem {began}, and Lem {version} reads only tasks begun on {before} or {version}. "
            f"Your branch and its commits stay. /lem drop {slug}, then /lem resume {slug}, starts a new task on {version} "
            "from that branch and from the notes the task left.",
        }
    return None


def installed(listed: object, main: str) -> str | None:
    """The release of Lem that the sessions of the checkout MAIN load, from LISTED, Claude Code's
    `installed_plugins.json` as read: the newest install for MAIN (scope `project` or `local`), else
    the newest for the user; None when the list names neither. An entry of another shape is no answer."""
    plugins = listed.get("plugins") if isinstance(listed, dict) else None
    own: list[str] = []
    user: list[str] = []
    here = os.path.realpath(main)
    for key, installs in plugins.items() if isinstance(plugins, dict) else []:
        if not isinstance(key, str) or key.split("@")[0] != "lem":
            continue
        for entry in installs if isinstance(installs, list) else []:
            if not isinstance(entry, dict) or numbers(entry.get("version")) is None:
                continue
            where = entry.get("projectPath")
            if (
                entry.get("scope") in PROJECT_SCOPES
                and isinstance(where, str)
                and os.path.realpath(where) == here
            ):
                own.append(entry["version"])
            elif entry.get("scope") in USER_SCOPES:
                user.append(entry["version"])
    found = own or user
    return max(found, key=numbers) if found else None


def chosen(listed: object, main: str, version: str) -> str:
    """The mark of a task that opens now in the checkout MAIN: the release its sessions load
    (`installed`), else VERSION, this Lem's own, and never newer than VERSION."""
    found = installed(listed, main)
    return (
        found if found is not None and numbers(found) <= numbers(version) else version
    )


def running() -> str:
    """This Lem's own release, from its plugin.json. A manifest that does not read is an error: no
    command can tell which tasks it reads without it."""
    try:
        version = json.loads(MANIFEST.read_text(encoding="utf-8")).get("version")
    except (OSError, ValueError, AttributeError) as error:
        raise ValueError(
            f"Lem's manifest {MANIFEST} does not read ({error}), so this Lem cannot tell its release: install Lem again"
        ) from error
    if numbers(version) is None:
        raise ValueError(
            f'Lem\'s manifest {MANIFEST} gives the version {version!r}, which is no release: plugin.json names one, as "version": "0.3.0"'
        )
    return version


def installs(environ: dict | None = None) -> object:
    """Claude Code's list of installed plugins (`plugins/installed_plugins.json` of CLAUDE_CONFIG_DIR,
    else of `~/.claude`), as read; None when it is not there or does not read."""
    environ = os.environ if environ is None else environ
    home = Path(environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    try:
        return json.loads(
            (home / "plugins" / "installed_plugins.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return None


def mark(directory: Path, main: Path) -> None:
    """Write the mark of a task that opens now, once: a mark that is there stays."""
    with (
        contextlib.suppress(FileExistsError),
        (directory / MARK).open("x", encoding="utf-8") as out,
    ):
        out.write(chosen(installs(), str(main), running()) + "\n")


def began_on(directory: Path) -> str:
    """The release the task began on, from its mark; UNMARKED for a task with none."""
    file = directory / MARK
    if not file.is_file():
        return UNMARKED
    found = file.read_text(encoding="utf-8", errors="replace").strip()
    if numbers(found) is None:
        raise ValueError(
            f"{file} says {found!r}, which is no release: it holds one line, the release the task began on, as {UNMARKED}"
        )
    return found


def git(where: Path, *args: str) -> str | None:
    ran = subprocess.run(
        ["git", "-C", str(where), *args],
        capture_output=True,
        text=True,
        check=False,
        stdin=subprocess.DEVNULL,
    )
    return ran.stdout if ran.returncode == 0 else None


def branch_of(main: Path, slug: str) -> str | None:
    """The task's branch as git names it, from no record of Lem's: the `branch` line of the entry git
    keeps for the task's worktree path (`git worktree list --porcelain`, which keeps the entry of a
    folder removed by hand until a prune), else, on a detached head, the branch a rebase in that
    worktree runs on (`head-name` of `rebase-merge/` or `rebase-apply/` in its git folder)."""
    path = os.path.realpath(main / ".lem" / "worktrees" / slug)
    listed = git(main, "worktree", "list", "--porcelain", "-z") or ""
    entry = next(
        (
            fields
            for fields in (block.split("\0") for block in listed.split("\0\0"))
            if fields[0].startswith("worktree ")
            and os.path.realpath(fields[0].removeprefix("worktree ")) == path
        ),
        None,
    )
    if entry is None:
        return None
    named = next(
        (
            field.removeprefix("branch refs/heads/")
            for field in entry
            if field.startswith("branch refs/heads/")
        ),
        None,
    )
    if named:
        return named
    common = (
        git(main, "rev-parse", "--path-format=absolute", "--git-common-dir") or ""
    ).strip()
    for gitdir in sorted(Path(common).glob("worktrees/*/gitdir")) if common else []:
        if os.path.realpath(
            gitdir.read_text(encoding="utf-8", errors="replace").strip()
        ) != os.path.realpath(os.path.join(path, ".git")):
            continue
        for folder in ("rebase-merge", "rebase-apply"):
            head = gitdir.parent / folder / "head-name"
            if head.is_file():
                return (
                    head.read_text(encoding="utf-8", errors="replace")
                    .strip()
                    .removeprefix("refs/heads/")
                    or None
                )
    return None


def stopped_already(log: Path, slug: str, version: str) -> bool:
    """Whether the log holds a stop of the task SLUG by this release (VERSION) that still stands: no
    `task.state` after it but an end of the task. The drop that passes, then the resume of the dropped
    task, logs no second stop."""
    standing = False
    for line in (
        lem_state.jsonl_lines(log.read_text(encoding="utf-8", errors="replace"))
        if log.is_file()
        else []
    ):
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict) or record.get("task") != slug:
            continue
        if record.get("event") == STOP:
            standing = record.get("running") == version
        elif record.get("event") == "task.state" and record.get("status") not in ENDS:
            standing = False
    return standing


def log_stop(directory: Path, began: str, version: str, say: str) -> None:
    """Log the old task's stop, once (`stopped_already`)."""
    state = directory.parent.parent
    main = state.parent.parent
    slug = directory.name
    branch = branch_of(main, slug)
    with lem_state.events_lock(state):
        log = state / lem_state.EVENTS
        if stopped_already(log, slug, version):
            return
        record = {
            "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event": STOP,
            "task": slug,
            "began": began,
            "running": version,
            "branch": branch,
            "say": say,
        }
        with log.open("a", encoding="utf-8") as out:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")


def check(directory: Path, passes: bool = False) -> str | None:
    """The rule for one command on the task of DIRECTORY (`.lem/state/tasks/SLUG` of the main
    checkout): None when it goes on, else the message it stops with, for the caller to refuse with.
    PASSES for a command that ends the task. A directory that is not there is no task yet, and the
    command's own refusal or its open of the task says the rest."""
    cleared = CLEARED.get()
    key = os.path.realpath(directory)
    if (cleared is not None and key in cleared) or not directory.is_dir():
        return None
    try:
        began, version = began_on(directory), running()
    except ValueError as error:
        return str(error)
    found = stop(directory.name, began, version, BEFORE)
    if found and found["kind"] == "new":
        return found["say"]
    if found:
        log_stop(directory, began, version, found["say"])
        if not passes:
            return found["say"]
    if cleared is not None:
        CLEARED.set(cleared | {key})
    return None


def one_command(main):
    """A script's `main` as one command: what it passes (`check`) holds for the commands it runs in
    this process, and for no command after it."""

    @functools.wraps(main)
    def run(*args, **kwargs):
        token = CLEARED.set(CLEARED.get() or frozenset())
        try:
            return main(*args, **kwargs)
        finally:
            CLEARED.reset(token)

    return run
