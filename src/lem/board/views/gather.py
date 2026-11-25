"""A workspace read once for a page (`board_model.Reader` on `main`): every task's record and what
lies beside it, the owner's presence, the Inbox's record, and the mark of example tasks.

This module, `folder.py`, `branch.py` and the reads of the backlog and the Inbox are the views'
only reads; every other module of `views/` is a pure function of the `World` they make. The
terminal's list of sessions comes in from the server (`ask.Ask.listed`); with none, a board of
example tasks takes each session from Lem's acts alone (`sessions.from_acts`), and any other
board says that the sessions are not known.
"""

from dataclasses import replace
from typing import TYPE_CHECKING

from lem.app.owner import releases
from lem.app.sessions import log
from lem.board.views import branch, folder, inbox_read, looked, sessions, world
from lem.board.views.backlog import read as shelf
from lem.settings import places as settings_places
from lem.settings.load import team_of
from lem.store import owner, places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.ask import Ask
    from lem.records.record import Record

DEMO = "demo"
WORKTREES = ".lem/worktrees"
UNKNOWN = "the task sessions are not known: the server has not asked the terminal yet"


def gather(checkout: Path, ask: Ask) -> world.World:
    """The workspace of the main checkout `checkout` as the views read it."""
    state = places.state_of(checkout)
    demo = (state / DEMO).is_file()
    presence = owner.read(ask.home)
    records = releases.with_stops(tasks.every(state))
    found = tuple(seen_of(checkout, record, ask, demo=demo) for record in records)
    return world.World(
        viewer=ask.viewer,
        clock=ask.clock,
        version=ask.version,
        place=place_of(checkout, ask.place),
        tasks=tuple(looked.alone(seen, presence) for seen in found),
        unknown=None if demo or ask.listed is not None else UNKNOWN,
        presence=presence,
        backlog=shelf.read(checkout, ask.place, ask.ledger, ask.clock.now),
        inbox=inbox_read.read(state),
        forge=looked.forge_of(state, records),
        demo=demo,
    )


def place_of(checkout: Path, place: world.Place) -> world.Place:
    """The board's place with the same branch history the landing reads."""
    if not (checkout / settings_places.TEAM).is_file():
        return place
    return replace(place, history=team_of(checkout).branch.history)


def seen_of(checkout: Path, record: Record, ask: Ask, *, demo: bool) -> world.Seen:
    """One task and what lies beside its record."""
    worktree = checkout / WORKTREES / record.task.slug
    where = places.task_folder(places.state_of(checkout), record.task.slug)
    acts = log.read(where)
    session = sessions.of(record, acts, ask.listed, demo=demo)
    files = folder.files_of(where)
    return world.Seen(
        record=record,
        acts=acts,
        files=files,
        prose=folder.prose_of(where, files),
        plan_text=plan_text(worktree, record),
        stats=folder.stats_of(where, files),
        head=branch.head_of(ask.git, checkout, record.task, ask.place),
        filed=branch.filed_of(ask.git, checkout, record.task, ask.place),
        worktree=(worktree / ".git").exists(),
        session=session,
        stop=sessions.stop_of(record, acts, session),
    )


def plan_text(worktree: Path, record: Record) -> str | None:
    """The recorded plan of the task, in its own worktree."""
    plan = record.task.plan
    if plan is None or not (worktree / ".git").exists():
        return None
    return folder.text_of(worktree, plan.path)
