"""His yes to the wait of the criteria, as an approval answers it: the question the page showed
must be the wait's own, and his yes is written on it in the same write as the approval, so that
the first answer counts on the board and in the session alike (`serve.row_refusal` on `main`;
the design's part 3, "an answer carries the question's id and the digest it showed")."""

from typing import TYPE_CHECKING, Literal

from lem.kernel.errors import Refusal
from lem.model.criteria import waits
from lem.records.questions import Answer

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.task import Task

type Via = Literal["board", "session"]


def page_of(task: Task, named: str | None) -> None:
    """Refuse a yes from a page of a question that is not the wait's open one."""
    if named is None:
        return
    open_one = waits.question_of(task)
    if open_one is not None and open_one.id == named and open_one.answer is None:
        return
    now = open_one.id if open_one else "none"
    raise Refusal(
        "other-question",
        f"the page answered question {named}, and the wait of {task.slug}'s criteria asks "
        f"{now}: nothing was approved",
        "put the criteria to him again, on the page of the question that waits",
    )


def answered_yes(task: Task, via: Via, shown: str | None, now: datetime) -> Task:
    """The task whose wait for his yes is answered Yes, on its open question, or on one asked
    now when none was; a task whose criteria wait for nothing stays as it is."""
    if waits.hold_of(task) is None:
        return task
    question = waits.question_of(task) or waits.question(task, now, shown)
    said = Answer(option="yes", label="Yes", source=via, at=now)
    return waits.answered(task, question, said)
