"""The holds a task's own commands set and clear: the owner's wait, his park and its resume,
and what a move or a drop leaves of a hold (the design's part 3, "The task: a status and a hold").

Only a task no agent works on is parked: one that waits (queued, planned), or one that a hold
keeps still (the owner's answer, a breaker, a block). The resume gives back the hold the park put
aside. A move clears the owner's wait, a breaker and a block, which the move answers; a drop
keeps only the release stop, which the resume of a dropped task reads.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.task import breaker_question, owner_question
from lem.records.holds import Blocked, BreakerHold, OwnerHold, Parked, ReleaseHold
from lem.records.journal.task import StateNoted

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.holds import Hold, OwnerWait
    from lem.records.record import Record
    from lem.records.task import Status, Task

STILL = frozenset(("queued", "planned"))
ENDED = frozenset(("landed", "dropped", "answered"))
DONE = frozenset(("ready", "landing", "open"))
WHY = MappingProxyType(
    {
        "building": "its lead or its investigator works now: park it once it stops, or "
        "drop it",
        "shaping": "its session shapes it now: park it once it waits for him, or drop it",
    }
)


def park_refusal(task: Task) -> Refusal | None:
    """Why `task` may not be parked now, or None; a task parked already is no refusal."""
    hold, status = task.hold, task.status
    keeps_still = isinstance(hold, (OwnerHold, BreakerHold, Blocked, Parked))
    if status not in ENDED and (status in STILL or keeps_still):
        return None
    if status in ENDED:
        why = "an ended task stays ended"
    elif status in DONE:
        why = "its build is done: its landing goes on, or the owner drops it"
    else:
        why = WHY.get(status, "nothing of it runs to put aside")
    return Refusal(
        "park",
        f"{task.slug} is {status}, and only a task that no agent works on is parked: {why}",
        f"lem task move {task.slug} dropped --line WHY drops it",
    )


def parked(record: Record, *, words: str, now: Moment) -> Record:
    """The record with the hold `parked`; a task parked already keeps its park."""
    task = record.task
    if isinstance(task.hold, Parked):
        return record
    refusal = park_refusal(task)
    if refusal is not None:
        raise refusal
    entry = StateNoted(at=now, status=task.status, hold="parked", line=words)
    saved = task.hold
    if not isinstance(saved, (OwnerHold, BreakerHold, Blocked)):
        saved = None
    hold = Parked(since=now, words=words, held=saved)
    return replace(
        record, task=replace(task, hold=hold), journal=(*record.journal, entry)
    )


def resumed(record: Record, *, before: Hold | None, now: Moment) -> Record:
    """The record of a parked task with the hold its park put aside, and its status as it
    was."""
    task = record.task
    if isinstance(before, BreakerHold):
        task = breaker_question.renewed(task, before, now)
    elif isinstance(before, OwnerHold):
        task = owner_question.renewed(task, before)
    else:
        task = replace(task, hold=before)
    hold = task.hold
    kind = None if hold is None else str(hold.__struct_config__.tag)
    entry = StateNoted(at=now, status=task.status, hold=kind, line="resumed")
    return replace(record, task=task, journal=(*record.journal, entry))


def left(hold: Hold | None, status: Status) -> Hold | None:
    """What a move to `status` leaves of a hold: the release stop on a drop, and nothing
    else."""
    if status == "dropped" and isinstance(hold, ReleaseHold):
        return hold
    return None


def moved(record: Record, *, status: Status, line: str, now: Moment) -> Record:
    """The record with the task in `status` since `now`, its hold as the move leaves it, and
    the move in its journal; a move to the status it is in writes the line alone."""
    task = record.task
    hold = left(task.hold, status)
    since = task.since if status == task.status else now
    entry = StateNoted(at=now, status=status, line=line)
    changed = replace(task, status=status, since=since, hold=hold)
    return replace(record, task=changed, journal=(*record.journal, entry))


def waiting(record: Record, *, on: OwnerWait, line: str, now: Moment) -> Record:
    """The record with the owner's wait `on`, whose line the stage says."""
    hold = OwnerHold(on=on, line=line, since=now)
    entry = StateNoted(at=now, status=record.task.status, hold="owner", line=line)
    return replace(
        record,
        task=replace(record.task, hold=hold),
        journal=(*record.journal, entry),
    )
