"""Whose turn a task held for the owner is: his, or Lem's while it settles the wait itself
(`board_model.turn_of` and `goes_on_of` on `main`).

Under the interview's hold he answers its questions until the interview ends; then Lem writes
the criteria, the personas read them, and his yes is what is missing once the read is in or he
skipped it. Under the criteria's hold only a read that runs is not his. While the task runs
without him (he is away, or the night opened it), the interview, the skip of the read and the
criteria go on without him (`stages/away.md`); an order that names no task, one more fact, a
step of his and a plan stay his.
"""

from typing import TYPE_CHECKING

from lem.records.holds import OwnerHold

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.task import Task

# The waits that go on without him while the task runs without him.
GOES_ON = frozenset(("interview", "skip-read", "criteria"))


def held(task: Task) -> OwnerHold | None:
    """The owner's hold of the task, or None."""
    hold = task.hold
    return hold if isinstance(hold, OwnerHold) else None


def his_turn(task: Task, *, alone: bool) -> bool:
    """Whether the task waits for the owner now: his hold, his turn under it, and a wait that
    does not go on without him."""
    hold = held(task)
    if hold is None or (alone and hold.on in GOES_ON):
        return False
    if hold.on == "interview":
        return interview_turn(task, hold.since)
    if hold.on == "criteria":
        return not reading(task, hold.since)
    return True


def interview_turn(task: Task, since: Moment) -> bool:
    """His turn under the interview's hold: its questions until it ended, then his yes once
    the read is in or he skipped it."""
    ended = asked(task)
    if ended is None:
        return True
    if reading(task, max(since, ended)):
        return False
    if task.criteria.skip == "yes":
        return True
    ends = (read.ended for read in task.criteria.reads if read.ended is not None)
    return any(end >= ended for end in ends)


def asked(task: Task) -> Moment | None:
    """When the interview's questions ended: the end of its newest span, or None while they
    run or before they began."""
    interviews = [span for span in task.spans if span.name == "interview"]
    return interviews[-1].end if interviews else None


def reading(task: Task, since: Moment) -> bool:
    """Whether the personas' read of the criteria runs now: begun since `since`, not ended."""
    return any(
        read.ended is None and read.started >= since for read in task.criteria.reads
    )
