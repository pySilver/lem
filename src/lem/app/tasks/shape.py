"""`lem task read`: the read of a request, its type, track, careful topics and what comes
next, on the record of a task that is `shaping`. A queue by his order or behind a task, and the
wait for his answer, are the step `task`'s."""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record
    from lem.records.task import Shape


def with_shape(record: Record, *, shape: Shape) -> Record:
    """The record with the shape."""
    return replace(record, task=replace(record.task, shape=shape))


def shaped(folder: Path, slug: str, shape: Shape) -> Shape:
    """Record the shape of the task `slug`."""
    state = places.workspace(folder).state
    record = tasks.read(state, slug)
    status = record.task.status
    if status != "shaping":
        raise Refusal(
            "status",
            f"{slug} is {status}: its read is recorded while it is shaping",
            f"lem task move {slug} shaping first, when its read changes",
        )
    tasks.update(state, slug, partial(with_shape, shape=shape), record.revision)
    return shape
