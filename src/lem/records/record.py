"""`tasks/SLUG/task.json`: one record per task, written whole (the design's part 3).

`schema` is the form of the record, `release` the release of Lem the task began on (the stop two
releases back reads it), and `revision` counts its writes: a write names the revision it read,
and a stale one is refused (`store.tasks.update`).
"""

from lem.records.base import Frozen
from lem.records.journal.entry import Entry
from lem.records.landing.record import Landing
from lem.records.task import Task

# The form of task.json that this release writes.
SCHEMA = 1


class Record(Frozen, frozen=True, kw_only=True):
    """A task's whole record: its form, its release, its revision, the task, its landing, and
    its journal."""

    schema: int = SCHEMA
    release: str
    revision: int = 0
    task: Task
    landing: Landing | None = None
    journal: tuple[Entry, ...] = ()
