"""The pure changes the checks and the polish pass write into a task's record: a span begun and
ended (the board's time card and `--status` read it), a run of the checks on record with its
end in the journal, the fast track turned to the standard one, and a pass given back."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import changes
from lem.records.holds import OwnerHold
from lem.records.journal.task import SpanMark
from lem.records.work import Span

type Spans = tuple[Span, ...]

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.journal.landing import CheckEnd
    from lem.records.landing.checks import Checked
    from lem.records.record import Record
    from lem.records.work import SpanName


def begun(record: Record, *, name: SpanName, at: Moment) -> Record:
    """The record with a span `name` begun at `at`."""
    spans = (*record.task.spans, Span(name=name, start=at))
    changed = replace(record, task=replace(record.task, spans=spans))
    return changes.noted(changed, SpanMark(at=at, name=name, edge="start"))


def closed(record: Record, *, name: SpanName, at: Moment) -> Record:
    """The record with the newest open span `name` ended at `at`; none open, none ends."""
    spans = record.task.spans
    place = newest_open(spans, name)
    if place is None:
        return record
    ended = with_end(spans, place, at)
    changed = replace(record, task=replace(record.task, spans=ended))
    return changes.noted(changed, SpanMark(at=at, name=name, edge="end"))


def with_end(spans: Spans, place: int, at: Moment) -> Spans:
    """The spans with the one at `place` ended at `at`."""
    ended = replace(spans[place], end=at)
    after = spans[place + 1 :]
    return (*spans[:place], ended, *after)


def newest_open(spans: Spans, name: SpanName) -> int | None:
    """The place of the newest span `name`, while it has not ended."""
    named = [place for place, span in enumerate(spans) if span.name == name]
    if not named or spans[named[-1]].end is not None:
        return None
    return named[-1]


def checked(record: Record, *, run: Checked, end: CheckEnd) -> Record:
    """The record with the run of the checks, its span ended, and its end in the journal."""
    landed = changes.landing(record, checked=run)
    return changes.noted(closed(landed, name="checks", at=end.at), end)


def reshaped(record: Record, *, line: str, at: Moment) -> Record:
    """The fast-track task whose change lowers the bar takes the standard track: back to
    `shaping`, held for the owner's interview (`landing.md` E, "Fast track lowers the bar")."""
    task = record.task
    shape = task.shape and replace(task.shape, track="full")
    hold = OwnerHold(on="interview", line=line, since=at)
    held = replace(record, task=replace(task, shape=shape, hold=hold))
    return changes.moved(held, "shaping", line, at)


def unpolished(record: Record) -> Record:
    """The record with no polish pass, so that the pass is due again: the branch was
    rewritten after it."""
    return changes.landing(record, polished=None)
