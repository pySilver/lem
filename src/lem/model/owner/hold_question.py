"""The current question of a task's hold, for the board and the answer rules."""

from typing import TYPE_CHECKING

from lem.model.criteria import waits
from lem.model.task import breaker_question, owner_question
from lem.model.task.claim import ENDED
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


def active(task: Task) -> Question | None:
    """The question of the active hold, if the board can answer it."""
    if task.status in ENDED:
        return None
    if waits.hold_of(task) is not None:
        return waits.question_of(task)
    return standing(task)


def pending_answer(task: Task) -> Question | None:
    """An answer to the active hold which its session has yet to take."""
    asked = active(task)
    if asked is None or asked.answer is None or asked.took_effect is not None:
        return None
    return asked
