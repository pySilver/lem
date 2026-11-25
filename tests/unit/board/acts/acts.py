"""What the cases of the owner's acts share: a task of the board's workspace, the note an act came
back with, and the task's session opened as Lem opens it."""

import dataclasses
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlsplit

from fakes.records import record
from lem.app.sessions import here, opening
from lem.board.acts.notes import NOTES
from lem.kernel import clock
from lem.store import tasks
from unit.sessions.terminal import CALLER

if TYPE_CHECKING:
    from datetime import datetime

    import httpx

    from lem.board.acts.notes import Note
    from lem.records.record import Record
    from unit.board.acts.conftest import Board

SLUG = "gift-note"


def made(board: Board, slug: str = SLUG, **fields: object) -> Record:
    """A task of the board's workspace, with `fields` over a queued one."""
    return tasks.create(board.state, record(slug, **fields))


def read(board: Board, slug: str = SLUG) -> Record:
    """The task's record now."""
    return tasks.read(board.state, slug)


def note_of(answer: httpx.Response) -> Note:
    """The note the act's 303 names."""
    assert answer.status_code == 303, answer.text
    query = parse_qs(urlsplit(answer.headers["location"]).query)
    found = NOTES.get(query["note"][0])
    assert found is not None
    return found


def opened(board: Board, slug: str = SLUG, at: datetime | None = None) -> str:
    """Open the task's session as Lem opens it, now or at `at`, and give its id."""
    mine = dataclasses.replace(here.bound(board.checkout), caller=CALLER.id)
    moment = clock.now() if at is None else at
    made_now = opening.open_session(mine, slug, "owner", None, moment)
    return made_now.session
