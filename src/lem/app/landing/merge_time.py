"""Time from a task's opening to its first proposal, and the same-track median."""

from statistics import median
from types import MappingProxyType
from typing import TYPE_CHECKING

import msgspec

from lem.records.base import Frozen
from lem.records.journal.proposal import ProposalNoted

if TYPE_CHECKING:
    from lem.records.approvals import Size
    from lem.records.base import Moment
    from lem.records.record import Record

TRACKS = MappingProxyType(
    {None: "both tracks", "small": "the fast track", "full": "the standard track"}
)


class Time(Frozen, frozen=True, kw_only=True):
    """The elapsed seconds in the merge brief and the source of the expectation."""

    seconds: int | None
    expected: int | None
    source: str = msgspec.field(name="from")


def first_proposal(record: Record) -> Moment | None:
    """The first confirmed proposal, also for a folded journal if only one round ran."""
    for entry in record.journal:
        if isinstance(entry, ProposalNoted):
            return entry.at
    landing = record.landing
    if landing is not None and landing.round == 1 and landing.proposed is not None:
        return landing.proposed.at
    return None


def track(record: Record) -> Size | None:
    """The track that built the task's criteria."""
    shape = record.task.shape
    shaped = shape.track if shape else None
    return record.task.criteria.size or shaped


def elapsed(record: Record, proposed: Moment) -> int:
    """The seconds from the task's opening to its proposal."""
    return round((proposed - record.task.opened).total_seconds())


def earlier(record: Record, mine: Size | None, before: Moment) -> int | None:
    """Its elapsed seconds when the first proposal was earlier and the track matches."""
    proposed = first_proposal(record)
    if proposed is None or proposed >= before:
        return None
    if mine is not None and track(record) != mine:
        return None
    return elapsed(record, proposed)


def elapsed_before(
    records: tuple[Record, ...], mine: Size | None, before: Moment
) -> list[int]:
    """The elapsed seconds of the tasks that the comparison can use."""
    spans = (earlier(record, mine, before) for record in records)
    return [one for one in spans if one is not None]


def measured(record: Record, records: tuple[Record, ...]) -> Time:
    """The task's own elapsed time and the median of earlier proposals of its track."""
    proposed = first_proposal(record)
    if proposed is None:
        return Time(seconds=None, expected=None, source="the task was not proposed")
    mine = track(record)
    spans = elapsed_before(records, mine, proposed)
    same = TRACKS[mine]
    if not spans:
        return Time(
            seconds=elapsed(record, proposed),
            expected=None,
            source=f"no earlier first proposal of {same} on record",
        )
    noun = "task" if len(spans) == 1 else "tasks"
    return Time(
        seconds=elapsed(record, proposed),
        expected=round(median(spans)),
        source=f"the median of {len(spans)} earlier {noun} of {same}, from opening to proposal",
    )
