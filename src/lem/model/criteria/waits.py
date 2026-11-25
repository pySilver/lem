"""The criteria's wait for the owner's yes, and his answer to it (`criteria.newest_block`,
`owners_no` and `new_wait` on `main`).

The criteria wait for his yes while the task's hold is the owner's, on the interview or on the
criteria. The wait is one question of the task, of the topic `criterion`, "Approve the
criteria?": asked when the wait began, or when a change of the criteria asked again, and answered
once, on the board or typed in the task's session; the first answer counts. A question asked
again is a new one, with an id of its own, so his No to the text before never answers the text
after, also in the same second.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel import clock
from lem.records.holds import Hold, OwnerHold
from lem.records.questions import Answer, Question

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.task import Task

TOPIC = "criterion"
QUESTION = "Approve the criteria?"
OPTIONS = ("yes", "no")
SAID_NO = "no"
# The holds under which the criteria wait for his yes.
WAITING = ("interview", "criteria")
CHANGED = "the criteria wait for the owner: changed from the owner's note"
UNCHANGED = "the criteria wait for the owner: the owner's note changed no criterion"


def hold_of(task: Task) -> OwnerHold | None:
    """The owner's hold under which the criteria wait for his yes, or None."""
    hold = task.hold
    if isinstance(hold, OwnerHold) and hold.on in WAITING:
        return hold
    return None


def hold_after(task: Task, *, ends: bool) -> Hold | None:
    """The task's hold after an answer to the wait: none when the answer `ends` it and the
    criteria wait for his yes, else the hold as it is."""
    return None if ends and hold_of(task) is not None else task.hold


def question_of(task: Task) -> Question | None:
    """The question of the wait that stands: the newest of the topic, asked since the hold
    began; None when none was asked yet, or when the criteria wait for nothing."""
    hold = hold_of(task)
    if hold is None:
        return None
    found = (one for one in reversed(task.questions) if one.topic == TOPIC)
    newest = next(found, None)
    if newest is None or newest.asked < hold.since:
        return None
    return newest


def said_no(task: Task) -> Answer | None:
    """His No to the wait that stands, on the board or typed, or None."""
    question = question_of(task)
    answer = question.answer if question else None
    return answer if answer and answer.option == SAID_NO else None


def question(task: Task, now: datetime, shown: str | None) -> Question:
    """A new question of the wait, asked `now`, that shows the file of mark `shown`."""
    number = len(task.questions) + 1
    return Question(
        id=f"{TOPIC}-{number}-{clock.compact(now)}",
        topic=TOPIC,
        question=QUESTION,
        options=OPTIONS,
        digest=shown,
        asked=now,
    )


def asked(task: Task, now: datetime, line: str, shown: str | None) -> Task:
    """The task whose criteria wait for his yes again, under the hold `line`, with a new
    question that shows the file of mark `shown`."""
    hold = OwnerHold(on="criteria", line=line, since=now)
    questions = (*task.questions, question(task, now, shown))
    return replace(task, hold=hold, questions=questions)


def answered(task: Task, question: Question, answer: Answer) -> Task:
    """The task with `answer` to `question`, which it holds or which is new."""
    done = replace(question, answer=answer)
    kept = tuple(one for one in task.questions if one.id != question.id)
    return replace(task, questions=(*kept, done))
