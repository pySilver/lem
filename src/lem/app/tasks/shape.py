"""`lem task read`: the read of a request on the record of a task that is shaping or queued, its
queue and what waits for the owner (`model/task/read.py`), and the first line its session says.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.tasks import first_line, release
from lem.kernel import clock
from lem.model.task import first_line as opening
from lem.model.task import read as reading
from lem.store import places, task_file, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.records.task import Shape


def shaped(folder: Path, slug: str, shape: Shape, queue: reading.Queue) -> Record:
    """Record the read of the task `slug`, and give its record as written."""
    where = places.workspace(folder)
    record = release.checked(where.state, slug)
    parts = checked(where, record, queue)
    words = first_line.gathered(where, record.task)
    return tasks.update(
        where.state,
        slug,
        partial(read_with_line, shape=shape, ask=(queue, parts, clock.now(), words)),
        record.revision,
    )


def checked(
    where: places.Workspace, record: Record, queue: reading.Queue
) -> reading.Parts:
    """Refuse the read that may not be written, from the tasks its queue and the task's
    `after` name; the feature's parts among them, which the read keeps."""
    named = task_file.named(where.state, queue.after + record.task.after)
    parts = reading.parts_of(record.task, (one.task for one in named))
    statuses = {one.task.slug: one.task.status for one in named}
    refused = reading.refusal(record, queue, statuses, parts)
    if refused is not None:
        raise refused
    return parts


def read_with_line(
    record: Record,
    *,
    shape: Shape,
    ask: tuple[reading.Queue, reading.Parts, Moment, opening.Read],
) -> Record:
    """Write the shape and the first line made from the same read, the feature's parts
    kept in its `after`."""
    queue, parts, now, words = ask
    read = reading.read(record, shape=shape, queue=queue, now=now, parts=parts)
    return with_line(read, shape, words)


def with_line(read: Record, shape: Shape, words: opening.Read) -> Record:
    """Keep the line of the shape as read, before the task moves again."""
    line = opening.line_of(read.task, words)
    first = opening.composed(line, None) if line else None
    shape = replace(shape, first_line=first)
    return replace(
        read,
        task=replace(read.task, shape=shape),
        journal=first_line.with_opening(read, first),
    )
