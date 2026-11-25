"""A span's marks in the journal, which the Timeline draws, and the spans a resumed task takes
with it."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.records.journal.task import SpanMark

if TYPE_CHECKING:
    from lem.model.task.span_forms import Edge
    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.records.task import Task
    from lem.records.work import Span

# The spans of the stages before the build, which a resumed task takes with it
# (`RESUMED_EVENTS` on `main`).
CARRIED = frozenset(("interview", "scout", "investigation", "plan-talk"))


def mark_of(span: Span, edge: Edge, now: Moment) -> SpanMark:
    """The journal's mark of the start or the end of `span`, at `now`."""
    return SpanMark(
        at=now,
        name=span.name,
        edge=edge,
        job=span.job,
        by=span.by,
    )


def is_open(span: Span, name: str, job: str | None, *, keyed: bool) -> bool:
    """Whether `span` is the open span `name`, of `job` too when the span is `keyed`."""
    if span.name != name or span.end is not None:
        return False
    return not keyed or span.job == job


def journaled(record: Record, task: Task, mark: SpanMark) -> Record:
    """The record with the task as it is now, and the mark in its journal."""
    return replace(record, task=task, journal=(*record.journal, mark))


def carried(spans: tuple[Span, ...]) -> tuple[Span, ...]:
    """The ended spans of the stages before the build, which a task resumed from this one
    takes with it, so that its time card keeps the interview, the scout, the investigation
    and the plan talk (`RESUMED_EVENTS` on `main`)."""
    return tuple(
        span for span in spans if span.name in CARRIED and span.end is not None
    )
