"""The merge brief's time against earlier tasks of the workspace, read from every task's record:
a record of another task that does not read leaves the comparison short by it and named, and the
brief whole (`main:land.events_all` passed over an event that did not read)."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.landing import merge_time
from lem.store import survey

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


def left_out(unread: tuple[str, ...]) -> str:
    """What the source of the time adds for the tasks whose record does not read."""
    if not unread:
        return ""
    if len(unread) == 1:
        return f"; the record of {unread[0]} does not read, so the comparison leaves it out"
    names = ", ".join(unread)
    return f"; the records of {names} do not read, so the comparison leaves them out"


def compared(record: Record, state: Path) -> merge_time.Time:
    """The task's time from its opening to its first proposal, against the median of the
    earlier tasks of its track whose record reads."""
    records, unread = survey.records(state)
    measured = merge_time.measured(record, records)
    return replace(measured, source=measured.source + left_out(unread))
