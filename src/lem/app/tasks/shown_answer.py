"""The answer that the task's session can take from its current hold."""

from typing import TYPE_CHECKING

from msgspec.structs import asdict

from lem.model.criteria import waits
from lem.model.owner import hold_question
from lem.model.task.claim import ENDED
from lem.records.questions import Answer

if TYPE_CHECKING:
    from lem.records.task import Task


class BoardAnswer(Answer, frozen=True, kw_only=True):
    """The answer and the exact question the owner saw."""

    key: str
    question: str


def pending(task: Task) -> BoardAnswer | None:
    """The unconsumed answer to the current hold, if there is one."""
    if task.status in ENDED:
        return None
    question = waits.question_of(task) or hold_question.standing(task)
    if question is None or question.answer is None or question.took_effect is not None:
        return None
    return BoardAnswer(
        key=question.id, question=question.question, **asdict(question.answer)
    )
