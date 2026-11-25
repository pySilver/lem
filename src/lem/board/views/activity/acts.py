"""Lem's acts on a task's sessions as the feed reads them: the acts of its folder's log
(`Seen.acts`) and the session entries of its journal, each once, oldest first; and the guard's
timeline over them and the task's work, which says whether a stop stood.

The log is the acts' stand-in until the journal holds them (`app/sessions/acts.py`); a record
that holds both is read as one.
"""

from typing import TYPE_CHECKING

from lem.app.sessions import guard_look
from lem.app.sessions.acts import Act, Close, Open, Stopped, Wake, Worked
from lem.app.sessions.guard_rule import Event, Timeline
from lem.records.journal.sessions import (
    SessionClosed,
    SessionOpened,
    SessionStopped,
    SessionWoken,
    SessionWorked,
)
from lem.records.journal.task import OwnerAct

if TYPE_CHECKING:
    from datetime import datetime

    from lem.board.views.world import Seen
    from lem.records.journal.entry import Entry

type Logged = (
    SessionOpened | SessionClosed | SessionWoken | SessionStopped | SessionWorked
)
LOGGED = (SessionOpened, SessionClosed, SessionWoken, SessionStopped, SessionWorked)


def acts_of(seen: Seen) -> tuple[Act, ...]:
    """Every act on the task's sessions, each once, oldest first."""
    logged = (
        act_of(entry) for entry in seen.record.journal if isinstance(entry, LOGGED)
    )
    found: list[Act] = []
    for act in (*seen.acts, *logged):
        if act not in found:
            found.append(act)
    return tuple(sorted(found, key=moment))


def moment(done: Act) -> datetime:
    """When an act was done."""
    return done.at


def act_of(entry: Logged) -> Act:
    """A session entry of the journal in the form of the log's act."""
    match entry:
        case SessionOpened():
            return Open(
                at=entry.at,
                session=entry.session,
                name=entry.name,
                phase=entry.phase,
                why=entry.why,
                workspace=entry.workspace,
            )
        case SessionClosed():
            return Close(at=entry.at, session=entry.session, why=entry.why)
        case SessionWoken():
            return Wake(
                at=entry.at,
                session=entry.session,
                why=entry.why,
                head=entry.head,
                unread=entry.unread,
            )
        case SessionStopped():
            return Stopped(at=entry.at, session=entry.session, unread=entry.unread)
        case SessionWorked():
            return Worked(at=entry.at, session=entry.session, turn=entry.turn)


def line_of(seen: Seen, acts: tuple[Act, ...]) -> Timeline:
    """The guard's timeline: the acts and the task's work (every entry of its journal but the
    owner's acts and the sessions' own), in one second the acts first."""
    work = (
        Event(kind="work", at=entry.at) for entry in seen.record.journal if works(entry)
    )
    events = [*filter(None, map(guard_look.event_of, acts)), *work]
    return Timeline(events=tuple(sorted(events, key=guard_look.order)))


def works(entry: Entry) -> bool:
    """Whether a journal entry is work of the task."""
    return not isinstance(entry, (OwnerAct, *LOGGED))
