"""`lem task may-start` and `lem task start`: whether a task gets a lead now, and the owner's
"start SLUG now" for a queued one (`project.cmd_may_start` on `main`).

His word lifts the queue whatever it was: an order of his, a need, or a task it waited for that
was dropped. Its line keeps his words as he typed them; the task goes to `shaping` when its
interview comes next, else to `building`.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.tasks import release
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.task import holds, queue, table
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.records.task import Status, Task


def may(folder: Path, slug: str) -> queue.May:
    """Whether `slug` may start now; refused with the way on when it may not."""
    state = places.workspace(folder).state
    record = release.checked(state, slug)
    every = tasks.every(state)
    refused = queue.start_refusal(record.task, every)
    if refused is not None:
        raise refused
    return queue.May(slug=slug, running=queue.running(slug, every))


def started(record: Record, *, status: Status, words: str, now: Moment) -> Record:
    """The record of a queued task his word starts: no queue, no wait for his order, and
    his words in the journal's line."""
    unqueued = replace(record, task=replace(record.task, after=(), order=None))
    line = f'the owner\'s word: "{words}"'
    return holds.moved(unqueued, status=status, line=line, now=now)


def startable(task: Task) -> None:
    """Refuse his word over a task that is not queued, or that a park or a seat's block
    holds."""
    held = table.held_refusal(task, "building")
    if held is not None:
        raise held
    if task.status != "queued":
        raise Refusal(
            "start",
            f"{task.slug} is {task.status}: the owner's word starts a queued task",
            f"lem task may-start {task.slug} says whether it may start",
        )


def start(folder: Path, slug: str, words: str) -> table.Moved:
    """His "start SLUG now": the queued task starts."""
    state = places.workspace(folder).state
    record = release.checked(state, slug)
    startable(record.task)
    status = queue.started_in(record.task)
    change = partial(started, status=status, words=words, now=clock.now())
    tasks.update(state, slug, change, record.revision)
    return table.Moved(slug=slug, was=record.task.status, status=status)
