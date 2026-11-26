"""The tasks' sessions as the list of what waits reads them (`project.waiting_sessions` and
`board_model.stopped_of` on `main`): each task's newest session, or why the terminal could not
say; and the guard's stop that stands, only over a task the guard watches whose session still
lives, since a stopped session that is gone from the terminal is a task with no session
instead."""

from typing import TYPE_CHECKING

from lem.app.sessions import guard_look, guard_rule, listing, log
from lem.app.sessions.acts import Close, Open
from lem.kernel.errors import Refusal
from lem.model.owner.looks import Session, Stop

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.acts import Act
    from lem.app.sessions.here import Here
    from lem.records.record import Record

type Listed = dict[str, listing.Listed]


def demo_open(acts: tuple[Act, ...]) -> Open | None:
    """The newest session in demo data, while no close of it came after."""
    newest = log.newest_open(acts)
    if newest is None:
        return None
    closes = (act for act in acts if isinstance(act, Close))
    ended = any(
        log.same(close.session, newest.session)
        for close in closes
        if close.at >= newest.at
    )
    return None if ended else newest


def demo_session(record: Record, acts: tuple[Act, ...]) -> Session:
    """The demo's newest opened session lives until Lem closed it."""
    opened = demo_open(acts)
    if opened is None:
        return Session(live=False, since=record.task.opened)
    return Session(live=True, since=opened.at, id=opened.session)


def sessions_of(
    here: Here, now: datetime, records: tuple[Record, ...], *, demo: bool = False
) -> tuple[Listed, str | None]:
    """Each task's newest session by task, or none and why the terminal could not say."""
    if demo:
        return {}, None
    try:
        found = listing.list_sessions(here, now, records=records)
    except Refusal as refusal:
        return {}, f"the task sessions are not known: {refusal.why}"
    return {entry.task: entry for entry in found}, None


def for_record(
    here: Here, record: Record, shown: Listed | None, *, demo: bool
) -> Session | None:
    """The session from the terminal, or from the recorded acts for demo data."""
    slug = record.task.slug
    if demo:
        return demo_session(record, log.read(here.folder(slug)))
    return session_of(
        None if shown is None else shown.get(slug),
        record.task.opened,
        here.caller,
        known=shown is not None,
    )


def session_of(
    entry: listing.Listed | None, opened: datetime, caller: str | None, *, known: bool
) -> Session | None:
    """No facts when the terminal could not say, and no turn for the session that asks."""
    if not known:
        return None
    if entry is None:
        return Session(live=False, since=opened)
    live = agent_is_live(listed=entry.live, agent=entry.agent)
    return Session(
        live=live,
        since=entry.since,
        unanswered=live and entry.unanswered,
        working=entry.turn == "runs" and not log.same(entry.session, caller),
        id=entry.session,
    )


def agent_is_live(*, listed: bool, agent: bool | None) -> bool:
    """A live task session has a listed pane and a running agent."""
    return listed and agent is True


def stop_of(here: Here, record: Record, session: Session | None) -> Stop | None:
    """The guard's stop that stands over a task it watches whose session lives, else None: a
    stopped session that is gone from the terminal is a task with no session instead."""
    task = record.task
    watched = task.status in guard_rule.GUARDED and task.hold is None
    if not watched or session is None or not session.live:
        return None
    line = guard_look.timeline(record, log.read(here.folder(task.slug)))
    place = line.stop_stands()
    if place is None:
        return None
    event = line.events[place]
    return Stop(at=event.at, unread=event.unread, restarted=guard_rule.restarted(line))
