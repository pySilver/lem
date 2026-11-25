"""The release stops a workspace's view shows before any command writes them."""

from typing import TYPE_CHECKING

from lem.kernel.release import running
from lem.model.task import release
from lem.model.task.table import ENDED

if TYPE_CHECKING:
    from lem.records.record import Record


def with_stops(records: tuple[Record, ...]) -> tuple[Record, ...]:
    """Show a release stop as soon as the release rule holds, without writing it."""
    version = running()
    return tuple(
        release.held(record, version, record.task.since)
        if record.task.status not in ENDED
        and release.stops(record, version, release.BEFORE)
        else record
        for record in records
    )
