"""How far a task got (`Task.reached` and `progress` on `main`): the status it reached, which a
drop does not undo, and the task of its plan that runs (`task 2 of 3`)."""

import re
from typing import TYPE_CHECKING, NamedTuple

from lem.records.journal.task import StateNoted, Summary

if TYPE_CHECKING:
    from lem.records.record import Record

JOB = re.compile(r"task (?P<at>\d+) of (?P<of>\d+)")
DROPPED = "dropped"


class Progress(NamedTuple):
    """The task of the plan that runs, and how many the plan has."""

    at: int
    of: int


def reached(record: Record) -> str:
    """The status the task reached: its own, or for a dropped task the one before its drop."""
    status = record.task.status
    if status != DROPPED:
        return status
    before = [
        one for entry in record.journal for one in statuses(entry) if one != DROPPED
    ]
    return before[-1] if before else "queued"


def statuses(entry: object) -> tuple[str, ...]:
    """The statuses a journal entry names: a state's, or the run a summary keeps."""
    if isinstance(entry, StateNoted):
        return (entry.status,)
    if isinstance(entry, Summary):
        return entry.statuses
    return ()


def progress(record: Record) -> Progress | None:
    """The newest task of the plan the task's spans name, or None."""
    spans = [span for span in record.task.spans if span.name == "task"]
    job = spans[-1].job if spans else None
    found = JOB.search(job or "")
    if found is None:
        return None
    at, of = found["at"], found["of"]
    return Progress(at=int(at), of=int(of))


def done(record: Record) -> bool:
    """Whether the task's build is behind it."""
    return reached(record) in {"landed", "ready", "landing", "open"}
