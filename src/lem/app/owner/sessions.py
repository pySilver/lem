"""The tasks' sessions as the list of what waits reads them (`project.waiting_sessions` and
`board_model.stopped_of` on `main`): each task's newest session, or why the terminal could not
say; and the guard's stop that stands, only over a task the guard watches whose session still
lives, since a stopped session that is gone from the terminal is a task with no session
instead."""

from typing import TYPE_CHECKING

from lem.app.sessions import guard_look, guard_rule, listing, log
from lem.kernel.errors import Refusal
from lem.model.owner.looks import Session, Stop

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.here import Here
    from lem.records.record import Record

type Listed = dict[str, listing.Listed]


def sessions_of(
    here: Here, now: datetime, records: tuple[Record, ...]
) -> tuple[Listed, str | None]:
    """Each task's newest session by task, or none and why the terminal could not say."""
    try:
        found = listing.list_sessions(here, now, records=records)
    except Refusal as refusal:
        return {}, f"the task sessions are not known: {refusal.why}"
    return {entry.task: entry for entry in found}, None


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
