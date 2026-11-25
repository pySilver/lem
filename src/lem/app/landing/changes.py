"""The pure changes a landing step writes through `store.tasks.update`: the landing's
evidence, the task's status with its journal entry, and an entry alone."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.records.journal.task import StateNoted
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.journal.entry import Entry
    from lem.records.record import Record
    from lem.records.task import Status


def landing(record: Record, **evidence: object) -> Record:
    """The record with the landing's fields `evidence` set."""
    changed = replace(record.landing or Landing(), **evidence)
    return replace(record, landing=changed)


def noted(record: Record, entry: Entry) -> Record:
    """The record with one more journal entry."""
    return replace(record, journal=(*record.journal, entry))


def moved(record: Record, status: Status, line: str, now: Moment) -> Record:
    """The record with the task in `status` since `now`, and the move in its journal; a
    move to the status it is in changes nothing."""
    if record.task.status == status:
        return record
    task = replace(record.task, status=status, since=now)
    entry = StateNoted(at=now, status=status, line=line)
    return noted(replace(record, task=task), entry)
