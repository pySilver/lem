"""The guard's look at a task now: its timeline, and the facts of its newest session as the
terminal and the harness give them (`session.guard_look` on `main`)."""

from typing import TYPE_CHECKING

from lem.app.sessions import agents, log, seen, signs
from lem.app.sessions.acts import Close, Open, Stopped, Wake, Worked
from lem.app.sessions.guard_rule import GUARDED, Event, Facts, Timeline
from lem.records.base import Frozen
from lem.records.journal.task import OwnerAct
from lem.store import tasks

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.acts import Act
    from lem.app.sessions.here import Here
    from lem.records.record import Record


class Looked(Frozen, frozen=True, kw_only=True):
    """The task's timeline, the facts of its newest session, and that session."""

    line: Timeline
    facts: Facts
    session: str | None


def looked(here: Here, slug: str, now: datetime) -> Looked:
    """The guard's look at the task `slug` now."""
    record = tasks.read(here.where.state, slug)
    acts = log.read(here.folder(slug))
    newest = log.newest_open(acts)
    return Looked(
        line=timeline(record, acts),
        facts=facts_of(here, record, newest, now),
        session=newest.session if newest else None,
    )


def facts_of(here: Here, record: Record, newest: Open | None, now: datetime) -> Facts:
    """The facts of the task's newest session: it lives with an agent, and its signs."""
    task = record.task
    guarded = task.status in GUARDED and task.hold is None
    shown = seen.look(here)
    pane = shown.carries(newest, now)
    if pane is None or not agents.agent_runs(shown.ground(pane.id)):
        return Facts(guarded=guarded, alive=False)
    read = signs.read_signs(here, task.slug, pane.id)
    return Facts(
        guarded=guarded, alive=True, shell=read.shell, read=read.signs, sign=read.sign
    )


def timeline(record: Record, acts: tuple[Act, ...]) -> Timeline:
    """The task's work and Lem's acts on its sessions, oldest first; in one second the acts
    come before the work."""
    entries = (entry for entry in record.journal if not isinstance(entry, OwnerAct))
    work = (Event(kind="work", at=entry.at) for entry in entries)
    events = [*filter(None, map(event_of, acts)), *work]
    return Timeline(events=tuple(sorted(events, key=order)))


def order(event: Event) -> tuple[datetime, bool]:
    """The place of an event in the timeline: its moment, and in one second the acts first."""
    return event.at, event.kind == "work"


def event_of(act: Act) -> Event | None:
    """An act on the task's sessions as an event of the timeline; a close is none."""
    if isinstance(act, Close):
        return None
    if isinstance(act, Open):
        return Event(kind="open", at=act.at, why=act.why)
    if isinstance(act, Wake):
        return Event(kind="wake", at=act.at, why=act.why, unread=act.unread)
    if isinstance(act, Stopped):
        return Event(kind="stopped", at=act.at, unread=act.unread)
    turn = act.turn if isinstance(act, Worked) else None
    return Event(kind="worked", at=act.at, turn=turn)
