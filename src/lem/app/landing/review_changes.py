"""The pure changes `read` writes through `store.tasks.update` (`land.cmd_read` on `main`): the
review's span starts with its brief; its record ends the span, adds the attempt with its round
in the journal, writes the review's word on each lowered bar, marks a resolution read, and notes
once that a review called careful a request whose plan did not.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import changes
from lem.model.landing import review_due
from lem.records.journal.landing import CarefulMissed, ReviewRound
from lem.records.journal.task import SpanMark
from lem.records.landing.record import Landing
from lem.records.work import Span

if TYPE_CHECKING:
    from lem.model.landing.review_said import Said
    from lem.records.base import Moment
    from lem.records.landing.review import Reviewed
    from lem.records.record import Record

SPAN = "review"


def job_of(attempt: int) -> str:
    """The job of a review's span: its attempt."""
    return f"attempt {attempt}"


def started(record: Record, *, attempt: int, now: Moment) -> Record:
    """The record with the review's span started, once for its attempt."""
    job, spans = job_of(attempt), record.task.spans
    if (SPAN, job) in {(span.name, span.job) for span in spans}:
        return record
    span = Span(name=SPAN, job=job, start=now)
    task = replace(record.task, spans=(*spans, span))
    mark = SpanMark(at=now, name=SPAN, edge="start", job=job)
    return changes.noted(replace(record, task=task), mark)


def closed(span: Span, job: str, now: Moment) -> Span:
    """The span ended at `now` when it is the open span of the review's `job`."""
    if (span.name, span.job, span.end) != (SPAN, job, None):
        return span
    return replace(span, end=now)


def ended(record: Record, *, attempt: int, now: Moment) -> Record:
    """The record with the review's open span of its attempt ended."""
    job = job_of(attempt)
    spans = tuple(closed(span, job, now) for span in record.task.spans)
    task = replace(record.task, spans=spans)
    mark = SpanMark(at=now, name=SPAN, edge="end", job=job)
    return changes.noted(replace(record, task=task), mark)


def lowered(record: Record, said: Said) -> Record:
    """The record with the review's word on each file whose bar the change lowers."""
    checked = (record.landing or Landing()).checked
    if checked is None or not said.answered:
        return record
    words = {named.name: named.why for named in said.lowered}
    kept = tuple(
        replace(one, reviewer=words.get(one.path, one.reviewer))
        for one in checked.lowered
    )
    return changes.landing(record, checked=replace(checked, lowered=kept))


def missed(record: Record, review: Reviewed) -> Record:
    """The record with one note, the first time, that the review called careful a request
    whose plan did not: a lesson for the retro about the plan's call."""
    plan = record.task.plan
    called = plan is not None and bool(plan.careful)
    noted = any(isinstance(entry, CarefulMissed) for entry in record.journal)
    if not (review.answered and review.careful) or called or noted:
        return record
    rounds = len(review_due.rounds(record.landing or Landing()))
    entry = CarefulMissed(at=review.at, round=rounds, why=review.careful_why or "")
    return changes.noted(record, entry)


def recorded(record: Record, *, review: Reviewed, said: Said) -> Record:
    """The record with the review attempt and everything it says."""
    landing = record.landing or Landing()
    resolution = landing.resolution
    if review.of == "resolution" and resolution is not None and review.answered:
        resolution = replace(resolution, read=review.attempt)
    added = changes.landing(
        record, reviews=(*landing.reviews, review), resolution=resolution
    )
    added = changes.noted(added, ReviewRound(at=review.at, review=review))
    added = ended(lowered(added, said), attempt=review.attempt, now=review.at)
    return missed(added, review)
