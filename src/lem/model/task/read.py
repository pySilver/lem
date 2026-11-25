"""The read of a request (`lem task read`): its shape on the record, and the queue and the wait
it asks for (the fixed lines `type:`, `then:`, `after:` and `the owner's order:` on `main`).

`--after` queues the task behind others, a task each time it is given; `--order` keeps the
owner's words, and with no task named the order waits for his answer (`owner: order`). A read
again with no `--after` lifts a queue by a need that went; a queue by his order is lifted by
his word alone (`lem task start`).
"""

from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.task import holds, table
from lem.model.task.behind import after_dropped, word
from lem.records.base import Frozen

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.records.task import Shape, Status, Task

type Wait = Literal["criteria", "interview", "request"]

READABLE = frozenset(("shaping", "queued"))
ORDER_WAIT = "the order waits for the owner"
WAITS = MappingProxyType(
    {
        "criteria": "the criteria wait for the owner",
        "interview": "the interview waits for the owner",
        "request": "the request waits for the owner",
    }
)


class Queue(Frozen, frozen=True, kw_only=True):
    """What the read asks of the queue and of the owner: the tasks it waits for, his order in
    his words, and what waits for his answer."""

    after: tuple[str, ...] = ()
    order: str | None = None
    wait: Wait | None = None


def refusal(
    record: Record, queue: Queue, others: Mapping[str, Status]
) -> Refusal | None:
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
    for one in queue.after:
        if one == slug or one not in others:
            return Refusal(
                "after",
                f"--after names the task {slug} waits for, and {one} is no other task "
                "here",
                "lem task list names the tasks",
            )
    return removal_refusal(task, queue, others)


def removal_refusal(
    task: Task, queue: Queue, others: Mapping[str, Status]
) -> Refusal | None:
    """Only the owner's word removes an ordered dependency or one that was dropped."""
    removed = tuple(one for one in task.after if one not in queue.after)
    if removed and task.order is not None:
        return Refusal(
            "order",
            f"{task.slug} is queued by the owner's order, and only his word removes it",
            word(task.slug),
        )
    dropped_names = (one for one in removed if others.get(one) == "dropped")
    dropped = tuple((one, "dropped") for one in dropped_names)
    return after_dropped(task, dropped) if dropped else None


def moved_to(after: tuple[str, ...]) -> tuple[Status, str]:
    """Where the read moves the task, and the journal's line: queued behind `after`, or
    shaping."""
    if not after:
        return "shaping", "the queue is lifted"
    names = " and ".join(after)
    return "queued", f"queued after {names}"


def queued(record: Record, queue: Queue, now: Moment) -> Record:
    """The record with the queue the read asks for: queued behind `after`, or shaping."""
    task = record.task
    status, line = moved_to(queue.after)
    renewed = status == "queued" and task.after != queue.after
    task = replace(
        task,
        after=queue.after,
        order=task.order if task.after and task.order is not None else queue.order,
    )
    if renewed:
        task = replace(task, since=now)
    record = replace(record, task=task)
    if renewed or status != task.status:
        return holds.moved(record, status=status, line=line, now=now)
    return record


def read(record: Record, *, shape: Shape, queue: Queue, now: Moment) -> Record:
    """The record with its shape, its queue, and what waits for the owner now."""
    shaped = replace(record, task=replace(record.task, shape=shape))
    record = queued(shaped, queue, now)
    if not queue.after and queue.order is not None:
        return holds.waiting(record, on="order", line=ORDER_WAIT, now=now)
    wait = queue.wait
    if wait is not None:
        return holds.waiting(record, on=wait, line=WAITS[wait], now=now)
    return replace(record, task=replace(record.task, hold=None))
