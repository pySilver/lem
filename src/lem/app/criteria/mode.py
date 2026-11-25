"""Whether a task runs without the owner now, and whether its request is his own sentence: what
decides who may approve its criteria."""

import os
from typing import TYPE_CHECKING

from lem.kernel import paths
from lem.store import owner

if TYPE_CHECKING:
    from lem.records.record import Record


def not_his(record: Record) -> str | None:
    """Why the task's request is not the owner's own sentence, or None when it is: the night
    opened it, or someone else wrote it. Never his mark: a request he types while away is his."""
    task = record.task
    if task.night is not None:
        return f"the night of {task.night} opened it"
    if task.shape is not None and task.shape.someone_else:
        return "someone else wrote its request"
    return None


def alone(record: Record) -> bool:
    """Whether the task runs without the owner now: a night's task, or he is away."""
    if record.task.night is not None:
        return True
    return owner.read(paths.home(os.environ)).away
