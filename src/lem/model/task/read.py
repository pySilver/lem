"""The read of a request (`lem task read`): its shape on the record, and the queue and the wait
it asks for (the fixed lines `type:`, `then:`, `after:` and `the owner's order:` on `main`).

`--after` queues the task behind another; `--order` keeps the owner's words, and with no task
named the order waits for his answer (`owner: order`). A read again with no `--after` lifts a
queue by a need that went; a queue by his order is lifted by his word alone (`lem task start`).
"""

from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.task import holds, table
from lem.records.base import Frozen

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.records.task import Shape

type Wait = Literal["criteria", "interview"]

READABLE = frozenset(("shaping", "queued"))
ORDER_WAIT = "the order waits for the owner"
WAITS = MappingProxyType(
    {
        "criteria": "the criteria wait for the owner",
        "interview": "the interview waits for the owner",
    }
)


class Queue(Frozen, frozen=True, kw_only=True):
    """What the read asks of the queue and of the owner: the task it waits for, his order in
    his words, and what waits for his answer."""

    after: str | None = None
    order: str | None = None
    wait: Wait | None = None


def refusal(record: Record, queue: Queue, others: frozenset[str]) -> Refusal | None:
    """Why the read may not be written: the task is past its shape, its queue names itself
    or no task, or it drops the queue of his order."""
    task = record.task
    slug = task.slug
    held = table.held_refusal(task, task.status)
    if held is not None:
        return held
    if task.status not in READABLE:
        return Refusal(
            "status",
            f"{slug} is {task.status}: its read is written while it is shaping or queued",
            f"lem task move {slug} shaping first, when its read changes",
        )
    after = queue.after
    if after is not None and (after == slug or after not in others):
        return Refusal(
            "after",
            f"--after names the task {slug} waits for, and {after} is no other task "
            "here",
            "lem task list names the tasks",
        )
    dropped_order = task.order is not None and task.after is not None
    if dropped_order and queue.after is None and queue.order is None:
        return Refusal(
            "order",
            f"{slug} is queued by the owner's order, and only his word removes it",
            f'lem task start {slug} --words "HIS WORDS"',
        )
    return None


def queued(record: Record, queue: Queue, now: Moment) -> Record:
    """The record with the queue the read asks for: queued behind `after`, or shaping."""
    was = record.task.status
    task = replace(record.task, after=queue.after, order=queue.order)
    if queue.after is None:
        status, line = "shaping", "the queue is lifted"
    else:
        status, line = "queued", f"queued after {queue.after}"
    record = replace(record, task=task)
    if status == was:
        return record
    return holds.moved(record, status=status, line=line, now=now)


def read(record: Record, *, shape: Shape, queue: Queue, now: Moment) -> Record:
    """The record with its shape, its queue, and what waits for the owner now."""
    shaped = replace(record, task=replace(record.task, shape=shape))
    record = queued(shaped, queue, now)
    if queue.after is None and queue.order is not None:
        return holds.waiting(record, on="order", line=ORDER_WAIT, now=now)
    wait = queue.wait
    if wait is not None:
        return holds.waiting(record, on=wait, line=WAITS[wait], now=now)
    return replace(record, task=replace(record.task, hold=None))
