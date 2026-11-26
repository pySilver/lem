"""The answer a task's session can take from its hold or its completed approval."""

from typing import TYPE_CHECKING

from msgspec.structs import asdict

from lem.model.owner import hold_question
from lem.model.task.claim import ENDED
from lem.records.journal.task import OwnerAct, StateNoted
from lem.records.questions import Answer

if TYPE_CHECKING:
    from lem.records.questions import Question
    from lem.records.record import Record


class BoardAnswer(Answer, frozen=True, kw_only=True):
    """The answer and the exact question the owner saw."""

    key: str
    question: str


def approved(record: Record) -> Question | None:
    """The board approval since the last state line, if it cleared the hold."""
    task = record.task
    if task.hold is not None or task.status in ENDED:
        return None
    for entry in reversed(record.journal):
        if isinstance(entry, StateNoted):
            break
        if isinstance(entry, OwnerAct) and entry.act == "approve":
            return next(
                (asked for asked in task.questions if asked.id == entry.question), None
            )
    return None


def pending(record: Record) -> BoardAnswer | None:
    """The answer to the current hold or the board approval that ended it."""
    question = hold_question.pending_answer(record.task) or approved(record)
    if question is None or question.answer is None:
        return None
    return BoardAnswer(
        key=question.id, question=question.question, **asdict(question.answer)
    )
