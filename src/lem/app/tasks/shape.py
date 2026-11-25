"""`lem task read`: the read of a request on the record of a task that is shaping or queued, its
queue and what waits for the owner (`model/task/read.py`), and the first line its session says.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.tasks import first_line, release
from lem.kernel import clock
from lem.model.task import read as reading
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record
    from lem.records.task import Shape


def shaped(folder: Path, slug: str, shape: Shape, queue: reading.Queue) -> Record:
    """Record the read of the task `slug`, and give its record as written."""
    where = places.workspace(folder)
    record = release.checked(where.state, slug)
    others = frozenset(one.task.slug for one in tasks.every(where.state))
    refused = reading.refusal(record, queue, others)
    if refused is not None:
        raise refused
    change = partial(reading.read, shape=shape, queue=queue, now=clock.now())
    return tasks.update(where.state, slug, change, record.revision)


def said(folder: Path, record: Record) -> str | None:
    """The first line the task's session says after its read, or None: a night task, a read
    that names no path, an order that waits for his answer."""
    return first_line.said(places.workspace(folder), record, named=False)
