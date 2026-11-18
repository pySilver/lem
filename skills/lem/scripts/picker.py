#!/usr/bin/env python3
"""Pick a task of the repository in agterm's picker, and open the board of that task.

    lem picker [--repo DIR]           open agterm's picker over the tasks; a pick opens its board
    lem picker [--repo DIR] --list    print the rows the picker shows, as JSON, and open nothing

An agterm keymap command starts it with a chord. The keymap is agterm's file and Lem never writes
it: the row `task picker` of `lem doctor` gives the line for this machine, which the owner adds.
The repository is the one the session sits in (`AGT_SESSION_PWD`), so the same chord in another
session lists that session's tasks.

The rows come in the order a developer reads them: first what waits for the owner (a choice, the
criteria for his yes, a step of his, a pull request to merge, a draft), in the order of `lem
project waiting`; then the tasks that build (ACTIVE), the newest first; then the tasks that ended in the
last ENDED_DAYS days, the newest first; and last a row for the board of all tasks. A row's label is
the task's ask in the owner's words, and its subtitle the state in the board's words, the track,
the age of the newest state, and the pull request's number with green or not green.

A pick runs `lem board --task SLUG --follow` (the board of all tasks for the last row), which is
what `/lem status SLUG` opens: a page needs no agent, and nothing is typed into a pane. Escape
opens nothing. Every failure exits 1 with one line on stderr, which agterm shows when the keymap
line carries `--error-hud`: no repository of Lem in the session, no task yet, no `agtermctl`, or a
picker or a board that failed.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    # an old python3 must still load this file, so that it can say what it needs and not a traceback
    sys.exit(f"picker.py: Lem needs Python 3.11 or newer, and this python3 is {sys.version.split()[0]}; name a newer one in the keymap line")

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
import project  # noqa: E402

# The id of the row for the board of all tasks: a slug is lower-case words and hyphens, so no task has it.
ALL = ":all"
# How long an ended task keeps a row: a guess of 2026-11-18, long enough for last week's work, not measured.
ENDED_DAYS = 7
# The state of a task in the board's words (board.html STATUS); the test holds the two to one list.
WORDS = {
    "queued": "Queued", "building": "Building", "planned": "Planned", "held": "Waits for you", "blocked": "Blocked",
    "ready": "Ready for its checks", "landing": "Checks and review", "open": "Waits for the merge", "landed": "Landed",
    "dropped": "Dropped", "answered": "Answered",
}
# the board's word for a task with no state block, and for a builder that investigates before any lead
UNKNOWN = "No status"
INVESTIGATING = "Investigating"
TRACKS = {"fast": "fast track", "standard": "standard track"}
# The order of the tasks that build: an agent or the checks work on these now, and Lem acts on the rest.
ACTIVE = ("building", "landing", "ready", "planned", "blocked", "queued")
# the number of a pull request in its address: GitHub's /pull/N
NUMBER = re.compile(r"/pull/(\d+)$")


class PickerError(Exception):
    pass


def age(since: str | None, now: datetime) -> str:
    """How long ago a state was written, in the shortest words: now, 5m, 3h, 2d."""
    if not since:
        return ""
    minutes = int((now - datetime.strptime(since, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)).total_seconds() // 60)
    if minutes < 1:
        return "now"
    if minutes < 60:
        return f"{minutes}m"
    if minutes < 24 * 60:
        return f"{minutes // 60}h"
    return f"{minutes // (24 * 60)}d"


def label(task: dict) -> str:
    """The task's ask in the owner's words, on one line; its slug in words when it has none. agterm
    refuses a label with a control character, so none stays."""
    words = " ".join("".join(ch if ch.isprintable() else " " for ch in task["ask"] or "").split()) or task["slug"].replace("-", " ").capitalize()
    return words if len(words) <= 100 else words[:99].rstrip() + "…"


def state_words(task: dict, waits: str | None) -> str:
    if waits:
        return waits
    if task["status"] == "building" and any(line.startswith("investigation:") for line in (task["state"] or "").splitlines()[1:]):
        return INVESTIGATING
    return WORDS.get(task["status"], UNKNOWN)


def pull_request(task: dict) -> str:
    """The pull request's number and green or not green; only green or not green where there is no number."""
    proposal = task["proposal"]
    if not proposal:
        return ""
    number = NUMBER.search(proposal["pull_request"] or "")
    return " ".join(([f"#{number[1]}"] if number else []) + ["green" if proposal["green"] else "not green"])


def row(task: dict, now: datetime, waits: str | None = None) -> dict:
    parts = [state_words(task, waits), TRACKS.get(task["track"] or "", ""), age(task["since"], now), pull_request(task)]
    return {"id": task["slug"], "label": label(task), "subtitle": " · ".join(part for part in parts if part)}


def choices_words(ids: list) -> str:
    if len(ids) == 1:
        return f"Choice {ids[0]} waits for you"
    return f"Choices {', '.join(map(str, ids[:-1]))} and {ids[-1]} wait for you"


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

    ids: dict[str, list] = {}
    for choice in waiting["choices"]:
        ids.setdefault(choice["task"], []).append(choice["id"])
    for slug, numbers in ids.items():
        add(slug, choices_words(numbers))
    for entry in waiting["criteria"]:
        add(entry["task"], "Waits for you: the acceptance criteria")
    for key in ("held", "pull_requests"):
        for entry in waiting[key]:
            add(entry["task"])
    def newest(task: dict) -> str:
        return task["since"] or ""

    # what an agent or the checks work on now, then what waits for Lem, the newest first in each
    building = [task for task in tasks.values() if task["slug"] not in seen and task["status"] not in project.ENDED]
    for task in sorted(sorted(building, key=newest, reverse=True), key=lambda task: ACTIVE.index(task["status"]) if task["status"] in ACTIVE else len(ACTIVE)):
        add(task["slug"])
    lately = (now - timedelta(days=ENDED_DAYS)).strftime("%Y-%m-%dT%H:%MZ")
    ended = [task for task in tasks.values() if task["status"] in project.ENDED and newest(task) >= lately]
    for task in sorted(ended, key=newest, reverse=True):
        add(task["slug"])
    count = len(tasks)
    out.append({"id": ALL, "label": "All tasks", "subtitle": f"the board of every task · {count} task{'s' if count != 1 else ''}"})
    return out


def lem_root(start: str) -> Path:
    """The checkout the session sits in, when it is a repository of Lem."""
    try:
        root = project.repo_root(Path(start))
    except project.SettingsError as error:
        raise PickerError(f"{error}: start the picker from a session in a repository of Lem") from error
    if not (root / project.SETTINGS).is_file():
        raise PickerError(f"{root} is no repository of Lem: it has no {project.SETTINGS}; /lem init sets it up")
    return root


def pick(found: list[dict]) -> str | None:
    """Open agterm's picker over the rows; the id picked, or None when the owner closed it."""
    ctl = shutil.which("agtermctl")
    if not ctl:
        raise PickerError("agtermctl is not on the PATH of this command: install agterm's command line tool (Help > Install Command Line Tool)")
    socket = os.environ.get("AGT_SOCKET", "")
    if not (socket and os.environ.get("AGT_SESSION_ID")):
        raise PickerError("not started from an agterm chord: AGT_SOCKET and AGT_SESSION_ID are not set; `lem picker --list` prints the rows")
    window = os.environ.get("AGT_WINDOW_ID", "")
    ran = subprocess.run([ctl, "pick", "--prompt", "Open the board of a task", *(["--window", window] if window else []), "--socket", socket],
                         input=json.dumps(found), capture_output=True, text=True, check=False)
    if ran.returncode == 2:
        return None
    if ran.returncode != 0:
        raise PickerError(f"agtermctl pick failed: {(ran.stderr or ran.stdout).strip() or f'exit {ran.returncode}'}")
    try:
        answer = json.loads(ran.stdout)
    except ValueError as error:
        raise PickerError(f"agtermctl pick answered no JSON: {ran.stdout.strip()[:200]}") from error
    if answer.get("result") != "picked":
        return None
    chosen = str(answer.get("id", ""))
    if chosen not in {item["id"] for item in found}:
        raise PickerError(f"agtermctl pick answered an id that no row has: {chosen!r}")
    return chosen


def open_board(root: Path, chosen: str) -> None:
    """The board of the task picked, or of all tasks, as `lem board` opens it."""
    ran = subprocess.run([sys.executable, "-B", str(SCRIPTS / "board.py"), "--repo", str(root), "--follow", *([] if chosen == ALL else ["--task", chosen])],
                         capture_output=True, text=True, check=False)
    if ran.returncode != 0:
        said = (ran.stderr or ran.stdout).strip().splitlines()
        raise PickerError((said[-1] if said else f"lem board exited {ran.returncode}").removeprefix("board.py: "))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="lem picker", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=os.environ.get("AGT_SESSION_PWD") or ".", help="a directory inside the checkout (default: the session's, else the current one)")
    parser.add_argument("--list", action="store_true", help="print the rows as JSON and open nothing")
    args = parser.parse_args(argv)
    try:
        root = lem_root(args.repo)
        found = rows(root, datetime.now(timezone.utc))
        if not found:
            raise PickerError(f"no task yet in {root}: `/lem` and a request opens one")
        if args.list:
            print(json.dumps(found, indent=2, ensure_ascii=False))
            return
        chosen = pick(found)
        if chosen is not None:
            open_board(root, chosen)
    except (PickerError, project.SettingsError) as error:
        sys.exit(f"lem picker: {error}")


if __name__ == "__main__":
    main()
