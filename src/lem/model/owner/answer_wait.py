"""Which questions still wait for the owner on the task's record."""

from typing import TYPE_CHECKING

from lem.model.owner.hold_question import standing
from lem.model.task.table import ENDED
from lem.records.holds import Parked, ReleaseHold

if TYPE_CHECKING:
    from lem.records.questions import Question
    from lem.records.task import Task


def why_closed(task: Task, asked: Question) -> str | None:
    """Why the question no longer waits, or None while the owner can answer it."""
    if task.status in ENDED:
        return f"{task.slug} is {task.status}: an ended task stays ended"
    if not isinstance(task.hold, (Parked, ReleaseHold)) and (
        asked.topic == "card" or standing(task) == asked
    ):
        return None
    return f"{asked.id} no longer waits for the owner"
