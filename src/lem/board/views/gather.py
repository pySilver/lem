"""A workspace read once for a page (`board_model.Reader` on `main`): every task's record and what
lies beside it, the owner's presence, the Inbox's record, and the mark of example tasks.

This module, `folder.py`, `branch.py` and the reads of the backlog and the Inbox are the views'
only reads; every other module of `views/` is a pure function of the `World` they make. The
terminal's list of sessions comes in from the server (`ask.Ask.listed`); with none, a board of
example tasks takes each session from Lem's acts alone (`sessions.from_acts`), and any other
board says that the sessions are not known.
"""

from typing import TYPE_CHECKING

from lem.app.sessions import log
from lem.board.views import branch, folder, inbox_read, sessions
from lem.board.views.backlog import read as shelf
from lem.board.views.world import Seen, World
from lem.store import owner, places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.ask import Ask
    from lem.records.record import Record

DEMO = "demo"
WORKTREES = ".lem/worktrees"
UNKNOWN = "the task sessions are not known: the server has not asked the terminal yet"


def gather(checkout: Path, ask: Ask) -> World:
    """The workspace of the main checkout `checkout` as the views read it."""
    state = places.state_of(checkout)
    demo = (state / DEMO).is_file()
    found = tuple(
        seen_of(checkout, record, ask, demo=demo) for record in tasks.every(state)
    )
    known = demo or ask.listed is not None
    return World(
        viewer=ask.viewer,
        clock=ask.clock,
        version=ask.version,
        place=ask.place,
        tasks=found,
        unknown=None if known else UNKNOWN,
        presence=owner.read(ask.home),
        backlog=shelf.read(checkout, ask.place, ask.ledger, ask.clock.now),
        inbox=inbox_read.read(state),
        demo=demo,
    )


def seen_of(checkout: Path, record: Record, ask: Ask, *, demo: bool) -> Seen:
    """One task and what lies beside its record."""
    task = record.task
    where = places.task_folder(places.state_of(checkout), task.slug)
    acts = log.read(where)
    session = sessions.of(record, acts, ask.listed, demo=demo)
    files = folder.files_of(where)
    return Seen(
        record=record,
        acts=acts,
        files=files,
        prose=folder.prose_of(where, files),
        head=branch.head_of(ask.git, checkout, task, ask.place),
        filed=branch.filed_of(ask.git, checkout, task, ask.place),
        worktree=(checkout / WORKTREES / task.slug / ".git").exists(),
        session=session,
        stop=sessions.stop_of(record, acts, session),
    )
