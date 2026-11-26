"""What the board's wait list shows of an open question."""

from typing import TYPE_CHECKING

from lem.app.asking import saved
from lem.app.owner import cards, releases, sessions
from lem.board.views import gather
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.owner import looks, waiting
from lem.store import tasks

if TYPE_CHECKING:
    from lem.app.sessions.here import Here
    from lem.records.record import Record


def notice(here: Here, slug: str, key: str) -> str | None:
    """Read the current question before checking the board's view of it."""
    try:
        record = tasks.read(here.where.state, slug)
    except Refusal as refusal:
        if refusal.code != "no-task":
            raise
        return None
    question = saved.named(record, key)
    if question is None or question.answer is not None:
        return None
    return from_sessions(here, record, key)


def from_sessions(here: Here, record: Record, key: str) -> str | None:
    """Use the session facts and release rule that the board uses for this task."""
    now = clock.now()
    demo = (here.where.state / gather.DEMO).is_file()
    listed, why = sessions.sessions_of(here, now, (record,), demo=demo)
    if why is not None:
        return unknown(why)
    look = looks.Look(
        record=releases.with_stops((record,))[0],
        session=cards.in_session(
            here.folder(record.task.slug),
            record,
            sessions.for_record(here, record, listed, demo=demo),
        ),
    )
    if not has_card(waiting.rows((look,), away=False, now=now), key):
        return hidden(look.session)
    return None


def has_card(rows: looks.Rows, key: str) -> bool:
    """Whether the wait list shows this card."""
    return any(row.card == key for row in rows)


def hidden(session: looks.Session | None) -> str:
    """Explain why the card has no row when the session facts say why."""
    if session is None or not session.live:
        return "The board will not show the owner's card. The task has no live session."
    return "The board will not show the owner's card for this task."


def unknown(why: str) -> str:
    """The board's rule could not be checked."""
    return f"Lem could not check if the board will show the owner's card. {why}"
