"""The spans in which a task ran without the owner (`project.runs_without_owner` on `main`).

A span runs while he is away, and while the task's own mark holds: a night's, from the moment
the night opened it. His back ends the span his away began, and never a night's. No span starts
before the task opened, so a task opened while he is away runs without him from its open, and an
away and a back that both came before the open are no span of it. The night's mark and his words
are read in the order of their moments (`marks.py`).
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.model.owner.marks import Mark, marks
from lem.model.owner.presence import Without
from lem.model.task.table import ENDED

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.owner import Presence
    from lem.records.task import Task

type Spans = tuple[Without, ...]


def spans(task: Task, presence: Presence) -> Spans:
    """The spans in which the task ran without the owner, oldest first; the newest has no end
    while it runs."""
    found: list[Without] = []
    start = None
    cutoff = task.since if task.status in ENDED else None
    for mark in marks(task, presence):
        if cutoff is not None and mark.at > cutoff:
            break
        start = held(start, mark)
        moved(found, start, mark, task.opened)
    return tuple(found)


def held(start: Mark | None, mark: Mark) -> Mark | None:
    """The night's mark holds for good, and the first of a run of aways until his back."""
    if mark.own:
        return mark
    if start is not None and start.own:
        return start
    return (start or mark) if mark.away else None


def moved(found: list[Without], start: Mark | None, mark: Mark, first: Moment) -> None:
    """Start a span or end the running one, dropping spans before the task opened."""
    running = bool(found) and found[-1].end is None
    if start is not None:
        if not running:
            begins = max(start.at, first)
            found.append(Without(start=begins, started=start.said))
    elif running:
        if mark.at < first:
            found.pop()
        else:
            found[-1] = ended(found[-1], mark)


def ended(span: Without, mark: Mark) -> Without:
    """The span ended by `mark`, never before it began."""
    return replace(span, end=max(mark.at, span.start), ended=mark.said)
