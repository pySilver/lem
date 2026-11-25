"""The exact question the board can answer for a task's hold, and the form's labels."""

from types import MappingProxyType

from lem.model.owner import hold_question
from lem.model.task import breaker_question, owner_question

OPTIONS = MappingProxyType(
    {**owner_question.OPTIONS, "breaker": breaker_question.OPTIONS}
)
standing = hold_question.standing


def label_of(option: str) -> str:
    """The label of an option, as its button says it."""
    return option.capitalize()
