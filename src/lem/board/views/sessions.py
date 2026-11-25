"""A task's newest session as the views read it (`board_model.live_of` and `stopped_of` on
`main`): from the terminal's list, or, on a board of example tasks, from Lem's acts alone, and
the guard's stop that stands over it.

A demo has no terminal to ask: the newest session Lem opened for a task lives until Lem closed
it. A task with no session on record has one that does not live, since it opened.
"""

from typing import TYPE_CHECKING

from lem.app.owner import sessions
from lem.app.sessions import guard_look, guard_rule, log
from lem.app.sessions.acts import Close, Open
from lem.model.owner.looks import Session, Stop

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.app.sessions.acts import Act
    from lem.app.sessions.listing import Listed
    from lem.records.record import Record

    # The terminal's list of sessions, by task.
    type Listing = Mapping[str, Listed]


def acted(acts: tuple[Act, ...]) -> Open | None:
    """The newest session Lem opened, while no close of it came after."""
    opens = [act for act in acts if isinstance(act, Open)]
    if not opens:
        return None
    newest = opens[-1]
    closes = (act for act in acts if isinstance(act, Close))
    ended = any(
        log.same(close.session, newest.session)
        for close in closes
        if close.at >= newest.at
    )
    return None if ended else newest


def from_acts(record: Record, acts: tuple[Act, ...]) -> Session:
    """The session of a demo: the newest one Lem opened lives until it closed it."""
    opened = acted(acts)
    if opened is None:
        return Session(live=False, since=record.task.opened)
    return Session(live=True, since=opened.at)


def of(
    record: Record, acts: tuple[Act, ...], listed: Listing | None, *, demo: bool
) -> Session | None:
    """The task's session: from Lem's acts alone in a demo, as the terminal's list shows it,
    or None when the list was not asked."""
    if demo:
        return from_acts(record, acts)
    if listed is None:
        return None
    entry = listed.get(record.task.slug)
    return sessions.session_of(entry, record.task.opened, known=True)


def stop_of(
    record: Record, acts: tuple[Act, ...], session: Session | None
) -> Stop | None:
    """The guard's stop that stands over a task it watches whose session lives, else None
    (`app/owner/sessions.stop_of`, read from acts already in hand)."""
    task = record.task
    watched = task.status in guard_rule.GUARDED and task.hold is None
    if not watched or session is None or not session.live:
        return None
    line = guard_look.timeline(record, acts)
    place = line.stop_stands()
    if place is None:
        return None
    event = line.events[place]
    return Stop(at=event.at, unread=event.unread, restarted=guard_rule.restarted(line))


def jump_of(acts: tuple[Act, ...], session: Session | None) -> str | None:
    """The agterm id of the task's session a button jumps to, while it lives."""
    if session is None or not session.live:
        return None
    opened = acted(acts)
    return opened.session if opened else None
