"""What a part took from its feature at the split: its journal's line of the personas' read
and of the approval names the feature in `carried_from` (`part_record.py`). A part opened by
`lem task open --part-of` has lines of its own, and none carried.
"""

from typing import TYPE_CHECKING

from lem.records.journal.task import CriteriaNoted

if TYPE_CHECKING:
    from lem.records.approvals import Approval
    from lem.records.record import Record

READ = "read-done"
APPROVED = "approved"


def carried_from(record: Record, event: str) -> str | None:
    """The feature a part's line of `event` came from at the split, or None."""
    feature = record.task.part_of
    if feature is None:
        return None
    lines = (
        entry
        for entry in record.journal
        if isinstance(entry, CriteriaNoted) and entry.event == event
    )
    return feature if any(entry.carried_from == feature for entry in lines) else None


def approval(record: Record) -> Approval | None:
    """The feature's approval a part took at the split, or None."""
    approvals = record.task.criteria.approvals
    if carried_from(record, APPROVED) is None or not approvals:
        return None
    return approvals[0]
