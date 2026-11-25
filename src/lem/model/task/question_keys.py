"""The questions issued for one hold key, in the order the task asked them."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.records.questions import Question
    from lem.records.task import Task


def base_of(key: str) -> str:
    """The hold key of an issued question; a renewed question adds a sequence number."""
    base, _, sequence = key.rpartition("-")
    return base if sequence.isdecimal() else key


def recorded(task: Task, key: str) -> Question | None:
    """The last question issued for this exact hold key."""
    return next(
        (one for one in reversed(task.questions) if base_of(one.id) == key), None
    )


def fresh(task: Task, key: str) -> str:
    """A new question id under the hold key, even when its start shares a second."""
    sequence = len(task.questions) + 1
    return f"{key}-{sequence}"
