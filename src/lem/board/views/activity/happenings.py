"""Everything that happened to a task, as the feed tells it, oldest first: the entries of its
journal, Lem's acts on its sessions, the questions it asked the owner, and its seats' errors.

In one moment Lem's acts come first, as the guard's timeline orders them, then the journal's
entries in their order, then the questions, then the seats.
"""

from typing import TYPE_CHECKING, NamedTuple

from lem.board.views.activity import (
    acts,
    journal_told,
    tell_questions,
    tell_seats,
    tell_sessions,
)
from lem.records.journal.task import StateNoted

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime

    from lem.board.views.activity.told import Told
    from lem.board.views.world import Seen
    from lem.records.record import Record
    from lem.records.task import Task

ACT, ENTRY, ASKED, SEAT = range(4)


class Happening(NamedTuple):
    """A row of the feed: its moment, what made it (an act, an entry, a seat), its words, and
    whether it is a move of the task's state."""

    at: datetime
    source: int
    told: Told
    state: bool = False


def of(seen: Seen) -> tuple[Happening, ...]:
    """The task's rows, oldest first."""
    record = seen.record
    found = [*by_act(seen), *by_entry(record)]
    found.extend(by_question(record))
    found.extend(by_seat(record.task))
    return tuple(sorted(found, key=order))


def by_act(seen: Seen) -> Iterator[Happening]:
    """The rows of Lem's acts on the task's sessions."""
    done = acts.acts_of(seen)
    line = acts.line_of(seen, done)
    for act in done:
        yield Happening(act.at, ACT, tell_sessions.act(act, line))


def by_entry(record: Record) -> Iterator[Happening]:
    """The rows of the journal's entries."""
    for entry in record.journal:
        state = isinstance(entry, StateNoted)
        for told in journal_told.told_of(entry, record.task):
            yield Happening(entry.at, ENTRY, told, state=state)


def by_question(record: Record) -> Iterator[Happening]:
    """The rows of the questions the task asked."""
    for asked in record.task.questions:
        for at, told in tell_questions.question(asked, record.journal):
            yield Happening(at, ASKED, told)


def by_seat(task: Task) -> Iterator[Happening]:
    """The rows of the task's seats."""
    for stood in task.stand_ins:
        for at, told in tell_seats.seat(stood, task):
            yield Happening(at, SEAT, told)


def order(happening: Happening) -> tuple[datetime, int]:
    """A row's place: its moment, then what made it."""
    return happening.at, happening.source
