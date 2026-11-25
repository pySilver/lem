"""The exact question the board can answer for a task's hold, and the form's labels."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.model.task import breaker_question, owner_question
from lem.records.holds import BreakerHold, OwnerHold

if TYPE_CHECKING:
    from lem.records.questions import Question
    from lem.records.task import Task

OPTIONS = MappingProxyType(
    {**owner_question.OPTIONS, "breaker": breaker_question.OPTIONS}
)


def standing(task: Task) -> Question | None:
    """The question the board answers now, from the active hold's key."""
    hold = task.hold
    if isinstance(hold, BreakerHold):
        return breaker_question.current(task, hold)
    if isinstance(hold, OwnerHold):
        return owner_question.current(task, hold)
    return None


def label_of(option: str) -> str:
    """The label of an option, as its button says it."""
    return option.capitalize()
