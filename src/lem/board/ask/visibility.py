"""What the board's wait list shows of an open question."""

from typing import TYPE_CHECKING

from lem.app.asking import saved
from lem.app.owner import releases, sessions
from lem.app.sessions import log
from lem.board.views import gather
from lem.kernel import clock
from lem.model.owner import looks, waiting
from lem.store import tasks

if TYPE_CHECKING:
    from lem.app.sessions.here import Here
    from lem.records.record import Record


def notice(here: Here, slug: str, key: str, session: str) -> str | None:
    """Read the current question before checking the board's view of it."""
    records = tasks.every(here.where.state)
    record = next((one for one in records if one.task.slug == slug), None)
    if record is None:
        return None
    question = saved.named(record, key)
    if question is None or question.answer is not None:
        return None
    return from_sessions(here, records, record, key, session)


def from_sessions(
    here: Here, records: tuple[Record, ...], record: Record, key: str, session: str
) -> str | None:
    """Use the session facts and release rule that the board uses for this task."""
    now = clock.now()
    demo = (here.where.state / gather.DEMO).is_file()
    listed, why = sessions.sessions_of(here, now, records, demo=demo)
    if why is not None:
        return unknown(why)
    look = looks.Look(
        record=releases.with_stops((record,))[0],
        session=sessions.for_record(here, record, listed, demo=demo),
    )
    if not has_card(waiting.rows((look,), away=False, now=now), key):
        return hidden(look.session)
    return pane_notice(listed, record.task.slug, session)


def has_card(rows: looks.Rows, key: str) -> bool:
    """Whether the wait list shows this card."""
    return any(row.card == key for row in rows)


def hidden(session: looks.Session | None) -> str:
    """Explain why the card has no row when the session facts say why."""
    if session is None or not session.live:
        return "The board will not show the owner's card. The task has no live session."
    return "The board will not show the owner's card for this task."


def pane_notice(listed: sessions.Listed, slug: str, session: str) -> str | None:
    """The board can show a card that it refuses to answer."""
    entry = listed.get(slug)
    if entry is not None and not log.same(entry.session, session):
        return (
            "The owner cannot answer this card on the board. "
            "The task has a live session in a different pane."
        )
    return None


def unknown(why: str) -> str:
    """The board's rule could not be checked."""
    return f"Lem could not check if the board will show the owner's card. {why}"
