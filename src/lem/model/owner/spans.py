"""The spans in which a task ran without the owner (`project.runs_without_owner` on `main`).

A span runs while he is away, and while the task's own mark holds: a night's, from the moment
the night opened it. His back ends the span his away began, and never a night's. No span starts
before the task opened, so a task opened while he is away runs without him from its open, and an
away and a back that both came before the open are no span of it. The night's mark and his words
are read in the order of their moments (`marks.py`).
"""

from functools import partial, reduce
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.model.owner.marks import Mark, marks
from lem.model.owner.presence import Without
from lem.records.base import Frozen, Moment

if TYPE_CHECKING:
    from lem.records.owner import Presence
    from lem.records.task import Task

type Spans = tuple[Without, ...]


class Fold(Frozen, frozen=True, kw_only=True):
    """The spans so far, the task's own mark once it came, and the away that holds now."""

    spans: Spans = ()
    own: Mark | None = None
    away: Mark | None = None


def spans(task: Task, presence: Presence) -> Spans:
    """The spans in which the task ran without the owner, oldest first; the newest has no end
    while it runs."""
    step = partial(folded, task.opened)
    return reduce(step, marks(task, presence), Fold()).spans


def folded(first: Moment, fold: Fold, mark: Mark) -> Fold:
    """The fold after one more mark: the night's mark holds for good, his away holds until his
    back."""
    own = fold.own
    if own is None and mark.own:
        own = mark
    away = fold.away if mark.own else held(fold.away, mark)
    after = moved(fold.spans, own or away, mark, first)
    return Fold(spans=after, own=own, away=away)


def held(away: Mark | None, mark: Mark) -> Mark | None:
    """The away that holds after one of his words: the first of a run of aways, none after a
    back."""
    if not mark.away:
        return None
    return away or mark


def moved(spans: Spans, start: Mark | None, mark: Mark, first: Moment) -> Spans:
    """The spans after one mark: a new span when one starts, the running one ended when nothing
    holds any more, and dropped when that came before the task opened."""
    newest = spans[-1] if spans else None
    running = newest is not None and newest.end is None
    if start is not None and not running:
        begins = max(start.at, first)
        return (*spans, Without(start=begins, started=start.said))
    if start is not None or not running:
        return spans
    if mark.at < first:
        return spans[:-1]
    closed = ended(spans[-1], mark)
    return (*spans[:-1], closed)


def ended(span: Without, mark: Mark) -> Without:
    """The span ended by `mark`, never before it began."""
    return replace(span, end=max(mark.at, span.start), ended=mark.said)
