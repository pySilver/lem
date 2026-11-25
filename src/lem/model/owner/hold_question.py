"""The current question of a task's hold, for the board and the answer rules."""

from typing import TYPE_CHECKING

from lem.model.task import breaker_question, owner_question
from lem.records.holds import BreakerHold, OwnerHold

if TYPE_CHECKING:
    from lem.records.questions import Question
    from lem.records.task import Task


def standing(task: Task) -> Question | None:
    """The question from the active hold's key, when it has one."""
    hold = task.hold
    if isinstance(hold, BreakerHold):
        return breaker_question.current(task, hold)
    if isinstance(hold, OwnerHold):
        return owner_question.current(task, hold)
    return None
