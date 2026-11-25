"""A task's stretches of one state each, from the moves of its journal (the segments of
`board_model.settle` on `main`): a move starts a stretch and the next move of another state ends
it; the last runs to now while the task runs, and an ended task's last state is a moment.

A summary stands for the moves it folded: its last state starts the stretch a newer move of the
same state goes on, so that the stretch still dates from the run its past began.
"""

from typing import TYPE_CHECKING, NamedTuple

from lem.board.views import rule
from lem.board.views.activity import states
from lem.records.journal.task import StateNoted, Summary

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime

    from lem.records.record import Record


class Stretch(NamedTuple):
    """A stretch: its state, when it began and ended, and whether it runs now."""

    key: str
    start: datetime
    end: datetime
    open: bool = False


class Move(NamedTuple):
    """A move of the task's state: when, and to which state."""

    at: datetime
    key: str


def stretches(record: Record, now: datetime) -> tuple[Stretch, ...]:
    """The task's stretches up to `now`."""
    moves = tuple(moves_of(record))
    if not moves:
        return ()
    ended = record.task.status in rule.ENDED
    closing = moves[-1].at if ended else now
    ends = (*(move.at for move in moves[1:]), closing)
    return joined(moves, ends, runs=not ended)


def joined(
    moves: tuple[Move, ...], ends: tuple[datetime, ...], *, runs: bool
) -> tuple[Stretch, ...]:
    """The moves with the moment each ends, a move to the state before it going on its
    stretch; the last runs when `runs`."""
    found: list[Stretch] = []
    for move, end in zip(moves, ends, strict=True):
        begun = found.pop().start if goes_on(found, move) else move.at
        found.append(Stretch(move.key, begun, end))
    if runs and found:
        tail = found.pop()
        found.append(tail._replace(open=True))
    return tuple(found)


def goes_on(found: list[Stretch], move: Move) -> bool:
    """Whether a move is to the state of the stretch before it."""
    return bool(found) and found[-1].key == move.key


def moves_of(record: Record) -> Iterator[Move]:
    """The moves of the task's journal, a summary's last state among them."""
    for entry in record.journal:
        noted = entry.last_state if isinstance(entry, Summary) else entry
        if isinstance(noted, StateNoted):
            yield Move(noted.at, states.key_of(noted.status, noted.hold))
