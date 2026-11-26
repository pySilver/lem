"""The predecessor's Activity that a resumed task shows at the time of the resume."""

from operator import attrgetter
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.model.task.span_marks import CARRIED
from lem.records.journal.task import CriteriaNoted, DecisionNoted, SpanMark

if TYPE_CHECKING:
    from collections.abc import Iterator

    from lem.records.journal.entry import Entry
    from lem.records.record import Record
    from lem.records.task import Task

type Carried = CriteriaNoted | DecisionNoted | SpanMark


def eligible(record: Record) -> Iterator[Carried]:
    """Each entry the successor carries, in the order of the predecessor's journal."""
    for entry in record.journal:
        if isinstance(entry, (CriteriaNoted, DecisionNoted)) or (
            isinstance(entry, SpanMark) and entry.name in CARRIED
        ):
            yield entry


def older_approvals(
    record: Record, named: tuple[Carried, ...]
) -> Iterator[CriteriaNoted]:
    """Approval lines for records that hold the approvals only in the criteria."""
    kept = {
        entry.number
        for entry in named
        if isinstance(entry, CriteriaNoted) and entry.event == "approved"
    }
    for approval in record.task.criteria.approvals:
        if approval.number not in kept:
            yield CriteriaNoted(
                at=approval.at,
                event="approved",
                by=approval.by,
                number=approval.number,
                size=approval.size,
            )


def copied(record: Record, task: Task) -> tuple[Entry, ...]:
    """Use one new moment for all the copied lines. The task keeps the source times."""
    named = tuple(eligible(record))
    older = tuple(older_approvals(record, named))
    if older:
        combined = (*named, *older)
        named = tuple(sorted(combined, key=attrgetter("at")))
    return tuple(
        replace(entry, at=task.opened, carried_from=record.task.slug) for entry in named
    )
