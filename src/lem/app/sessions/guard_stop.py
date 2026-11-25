"""The guard's stop of a task's session (`lem session stopped`), put on record and read again
(`session.cmd_stopped` on `main`)."""

from typing import TYPE_CHECKING

from lem.app.sessions import guard_look, log
from lem.app.sessions.acts import Stopped
from lem.app.sessions.guard_acts import Acted, stop_said
from lem.app.sessions.guard_rule import restarted
from lem.store import tasks

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.guard_rule import Timeline
    from lem.app.sessions.here import Here


def stopped(here: Here, slug: str, looked: guard_look.Looked, now: datetime) -> Acted:
    """Put the stop on record, then read the task again: work its session put on record in
    the moment of the stop means it stands over nothing (`session.cmd_stopped` on `main`)."""
    session = looked.session or ""
    read = looked.facts.read
    after = stopped_line(here, slug, looked, now)
    stands = after.stop_stands() is not None
    say = stop_said(slug, stands=stands, read=read, again=restarted(after))
    return Acted(
        task=slug, session=session, acted=True, stands=stands, read=read, say=say
    )


def stopped_line(
    here: Here, slug: str, looked: guard_look.Looked, now: datetime
) -> Timeline:
    """Put the stop on record, and give the task's timeline as it is after it."""
    folder = here.folder(slug)
    session = looked.session or ""
    stop = Stopped(at=now, session=session, unread=not looked.facts.read)
    log.append(folder, stop)
    record = tasks.read(here.where.state, slug)
    return guard_look.timeline(record, log.read(folder))
