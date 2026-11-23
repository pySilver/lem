"""Pick a task of the repository in agterm's picker, and go to that task's session, or its board.

    lem picker [--repo DIR]           open agterm's picker over the tasks; a pick selects the task's
                                      live session, else opens its board
    lem picker [--repo DIR] --list    print the rows the picker shows, as JSON, and open nothing

An agterm keymap command starts it with a chord. The keymap is agterm's file and Lem never writes
it: the row `task picker` of `lem doctor` gives the line for this machine, which the owner adds.
The repository is the one the session sits in (`AGT_SESSION_PWD`), so the same chord in another
session lists that session's tasks.

The rows come in the order a developer reads them: first what waits for the owner (a breaker's
document, the criteria for his yes, a step of his, a task queued after a dropped one, a task its
session stopped, a plan to read, a pull request to merge, a task with no session, a task whose
session the board server's guard logged as stopped), in the groups of
`lem project waiting`; then the tasks that build (ACTIVE), the newest first, with a parked one after them; then the tasks that ended last,
the newest first, as many as the board's Done column draws (lem_board_model.DONE_SHOWN), however long ago they ended;
and last a row for the board of all tasks. A row's label is the task's ask in the owner's words, and its subtitle the
state in the board's words, the track, the age of the newest state, and the pull request's number with green or not green.

A pick of a task whose newest session lives in agterm's tree with an agent in it (`lem session`'s
`live`) selects that session (`agtermctl session select`), where the task's agent is. A task with
none, and the last row, runs `lem board --task SLUG --follow` (the board of all tasks for the last
row), which is what `/lem status SLUG` opens: the board server's page of that task, which needs no
agent. Nothing is typed into a pane. Escape opens nothing. Every failure exits 1 with one line on stderr,
which agterm shows when the keymap line carries `--error-hud`: no repository of Lem in the session, no
task yet, no `agtermctl`, or a picker or a board that failed (a board server that does not run among
them).

In Lem's marketplace clone (`PLUGINS/marketplaces/NAME`), which holds the head of `main` and no
release, this file runs nothing of its own: it becomes the clone's `bin/lem picker` with the same
arguments, which runs the newest installed release. The keymap lines that the doctor printed before
it gave `bin/lem picker` name this file in that clone, and they stay on the machines that have them.
"""

import os
import sys
from pathlib import Path

if Path(os.path.realpath(__file__)).parts[-7:-5] == ("plugins", "marketplaces"):
    # this file is PLUGINS/marketplaces/NAME/skills/lem/scripts/picker.py: the clone is the folder four up
    os.execv(  # noqa: S606 - the clone's bin/lem takes this process's place, with the same arguments
        sys.executable,
        [
            sys.executable,
            str(Path(os.path.realpath(__file__)).parents[3] / "bin" / "lem"),
            "picker",
            *sys.argv[1:],
        ],
    )

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(
        f"picker.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; name a newer one in the keymap line"
    )

import argparse
import importlib
import json
import re
import shutil
import subprocess
from datetime import UTC, datetime

SCRIPTS = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
import lem_board_model  # noqa: E402
import project  # noqa: E402

# The id of the row for the board of all tasks: a slug is lower-case words and hyphens, so no task has it.
ALL = ":all"
# The state of a task in the board's words: the board's own list (lem_board_model.STATUS).
WORDS = {status: facts["label"] for status, facts in lem_board_model.STATUS.items()}
# the board's word for a task with no state block, and for a builder that investigates before any lead
UNKNOWN = lem_board_model.UNKNOWN["label"]
INVESTIGATING = "Investigating"
TRACKS = {"fast": "fast track", "standard": "standard track"}
# The order of the tasks that build: an agent or the checks work on these now, and Lem acts on the rest.
ACTIVE = ("building", "landing", "ready", "planned", "blocked", "queued")
# the number of a pull request in its address: GitHub's /pull/N
NUMBER = re.compile(r"/pull/(\d+)$")
# the minutes of an hour and of a day, the units of `age`
HOUR = 60
DAY = 24 * HOUR
# the longest label, in characters, before it ends in an ellipsis
LABEL_WIDTH = 100
# the exit status of `agtermctl pick` when the owner closes the picker
CLOSED = 2


class PickerError(Exception):
    pass


def age(since: str | None, now: datetime) -> str:
    """How long ago a state was written, in the shortest words: now, 5m, 3h, 2d."""
    if not since:
        return ""
    minutes = int(
        (
            now - datetime.strptime(since, "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)
        ).total_seconds()
        // 60
    )
    if minutes < 1:
        return "now"
    if minutes < HOUR:
        return f"{minutes}m"
    if minutes < DAY:
        return f"{minutes // HOUR}h"
    return f"{minutes // DAY}d"


def label(task: dict) -> str:
    """The task's ask in the owner's words, on one line; its slug in words when it has none. agterm
    refuses a label with a control character, so none stays."""
    words = (
        " ".join(
            "".join(ch if ch.isprintable() else " " for ch in task["ask"] or "").split()
        )
        or task["slug"].replace("-", " ").capitalize()
    )
    return (
        words if len(words) <= LABEL_WIDTH else words[: LABEL_WIDTH - 1].rstrip() + "…"
    )


def state_words(task: dict, waits: str | None) -> str:
    if waits:
        return waits
    # every line of the newest block, its first too, as `lem project state` writes it
    newest = project.blocks_of(task["state"] or "")
    if (
        task["status"] == "building"
        and newest
        and any(
            line.strip().startswith("investigation:") for line in newest[0]["lines"]
        )
    ):
        return INVESTIGATING
    return WORDS.get(task["status"], UNKNOWN)


def pull_request(task: dict) -> str:
    """The pull request's number and green or not green; only green or not green where there is no number."""
    proposal = task["proposal"]
    if not proposal:
        return ""
    number = NUMBER.search(proposal["pull_request"] or "")
    return " ".join(
        ([f"#{number[1]}"] if number else [])
        + ["green" if proposal["green"] else "not green"]
    )


def row(task: dict, now: datetime, waits: str | None = None) -> dict:
    parts = [
        state_words(task, waits),
        TRACKS.get(task["track"] or "", ""),
        age(task["since"], now),
        pull_request(task),
    ]
    return {
        "id": task["slug"],
        "label": label(task),
        "subtitle": " · ".join(part for part in parts if part),
    }


def breaker_words(number: int) -> str:
    return f"Stopped: breaker {number} waits for you"


def rows(root: Path, now: datetime) -> list[dict]:
    """The picker's rows, as `pick` reads them; a repository with no task has none."""
    tasks = {task["slug"]: task for task in project.read_tasks(root)}
    if not tasks:
        return []
    waiting = project.cmd_waiting(root)
    out: list[dict] = []
    seen: set[str] = set()

    def add(slug: str, waits: str | None = None) -> None:
        if slug in tasks and slug not in seen:
            seen.add(slug)
            out.append(row(tasks[slug], now, waits))

    for breaker in waiting["breakers"]:
        add(breaker["task"], breaker_words(breaker["id"]))
    for entry in waiting["criteria"]:
        add(entry["task"], "Waits for you: the acceptance criteria")
    for entry in waiting["held"]:
        add(entry["task"])
    for entry in waiting["after_dropped"]:
        add(entry["task"], f"Waits for you: {entry['after']} was dropped")
    for key in ("blocked", "plans", "pull_requests", "no_session", "stopped"):
        for entry in waiting[key]:
            add(entry["task"])

    def newest(task: dict) -> str:
        return task["since"] or ""

    # what an agent or the checks work on now, then what waits for Lem, the newest first in each
    building = [
        task
        for task in tasks.values()
        if task["slug"] not in seen and task["status"] not in project.ENDED
    ]
    for task in sorted(
        sorted(building, key=newest, reverse=True),
        key=lambda task: (
            ACTIVE.index(task["status"]) if task["status"] in ACTIVE else len(ACTIVE)
        ),
    ):
        add(task["slug"])
    # the ended tasks Done draws as cards, by the board's own number, so that the two lists cannot drift
    ended = [task for task in tasks.values() if task["status"] in project.ENDED]
    for task in sorted(ended, key=newest, reverse=True)[: lem_board_model.DONE_SHOWN]:
        add(task["slug"])
    count = len(tasks)
    out.append(
        {
            "id": ALL,
            "label": "All tasks",
            "subtitle": f"the board of every task · {count} task{'s' if count != 1 else ''}",
        }
    )
    return out


def lem_root(start: str) -> Path:
    """The checkout the session sits in, when it is a repository of Lem."""
    try:
        root = project.repo_root(Path(start))
    except project.SettingsError as error:
        raise PickerError(
            f"{error}: start the picker from a session in a repository of Lem"
        ) from error
    if not (root / project.SETTINGS).is_file():
        raise PickerError(
            f"{root} is no repository of Lem: it has no {project.SETTINGS}; /lem init sets it up"
        )
    return root


def pick(found: list[dict]) -> str | None:
    """Open agterm's picker over the rows; the id picked, or None when the owner closed it."""
    ctl = shutil.which("agtermctl")
    if not ctl:
        raise PickerError(
            "agtermctl is not on the PATH of this command: install agterm's command line tool (Help > Install Command Line Tool)"
        )
    socket = os.environ.get("AGT_SOCKET", "")
    if not (socket and os.environ.get("AGT_SESSION_ID")):
        raise PickerError(
            "not started from an agterm chord: AGT_SOCKET and AGT_SESSION_ID are not set; `lem picker --list` prints the rows"
        )
    window = os.environ.get("AGT_WINDOW_ID", "")
    ran = subprocess.run(
        [
            ctl,
            "pick",
            "--prompt",
            "Open the board of a task",
            *(["--window", window] if window else []),
            "--socket",
            socket,
        ],
        input=json.dumps(found),
        capture_output=True,
        text=True,
        check=False,
    )
    if ran.returncode == CLOSED:
        return None
    if ran.returncode != 0:
        raise PickerError(
            f"agtermctl pick failed: {(ran.stderr or ran.stdout).strip() or f'exit {ran.returncode}'}"
        )
    try:
        answer = json.loads(ran.stdout)
    except ValueError as error:
        raise PickerError(
            f"agtermctl pick answered no JSON: {ran.stdout.strip()[:200]}"
        ) from error
    if answer.get("result") != "picked":
        return None
    chosen = str(answer.get("id", ""))
    if chosen not in {item["id"] for item in found}:
        raise PickerError(f"agtermctl pick answered an id that no row has: {chosen!r}")
    return chosen


def live_session(root: Path, slug: str) -> str | None:
    """The id of the task's newest session when it lives in agterm's tree with an agent in it, else None.
    agterm's whole tree is read, every window's, since a task's session may sit in any of them."""
    session = importlib.import_module("session")
    newest = session.newest_opens(project.events_named(root, *session.EVENTS)).get(slug)
    if newest is None:
        return None
    try:
        node = session.node_of(session.tree(chord_place()), newest.get("session"))
    except session.SessionError as error:
        raise PickerError(str(error)) from error
    return (
        str(newest["session"])
        if session.live(node, newest, datetime.now(UTC))
        else None
    )


def chord_place() -> dict:
    """Where the chord was pressed, as `lem session` takes a place: agterm's socket, and no window, so that
    the whole tree answers."""
    return {
        "session": os.environ.get("AGT_SESSION_ID", ""),
        "socket": os.environ.get("AGT_SOCKET", ""),
        "window": "",
    }


def select_session(target: str) -> None:
    session = importlib.import_module("session")
    try:
        session.ctl(chord_place(), "session", "select", "--target", target)
    except session.SessionError as error:
        raise PickerError(str(error)) from error


def open_board(root: Path, chosen: str) -> None:
    """The board of the task picked, or of all tasks, as `lem board` opens it."""
    ran = subprocess.run(
        [
            sys.executable,
            "-B",
            str(SCRIPTS / "board.py"),
            "--repo",
            str(root),
            "--follow",
            *([] if chosen == ALL else ["--task", chosen]),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if ran.returncode != 0:
        said = (ran.stderr or ran.stdout).strip().splitlines()
        raise PickerError(
            (said[-1] if said else f"lem board exited {ran.returncode}").removeprefix(
                "board.py: "
            )
        )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="lem picker",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("AGT_SESSION_PWD") or ".",
        help="a directory inside the checkout (default: the session's, else the current one)",
    )
    parser.add_argument(
        "--list", action="store_true", help="print the rows as JSON and open nothing"
    )
    args = parser.parse_args(argv)
    try:
        root = lem_root(args.repo)
        found = rows(root, datetime.now(UTC))
        if not found:
            raise PickerError(f"no task yet in {root}: `/lem` and a request opens one")
        if args.list:
            print(json.dumps(found, indent=2, ensure_ascii=False))
            return
        chosen = pick(found)
        if chosen is None:
            return
        live = live_session(root, chosen) if chosen != ALL else None
        if live:
            select_session(live)
        else:
            open_board(root, chosen)
    except (PickerError, project.SettingsError) as error:
        sys.exit(f"lem picker: {error}")


if __name__ == "__main__":
    main()
