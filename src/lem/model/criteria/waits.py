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

from lem.model.task import owner_question, question_keys
from lem.records.holds import Hold, OwnerHold
from lem.records.questions import Answer, Question

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.task import Task

TOPIC = "criterion"
QUESTION = owner_question.CRITERIA
OPTIONS = owner_question.OPTIONS[TOPIC]
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
    """The recorded question for the exact criteria wait, if one was issued."""
    hold = hold_of(task)
    if hold is None:
        return None
    return question_keys.recorded(
        task, owner_question.key_of(TOPIC, task.slug, hold.since)
    )


def said_no(task: Task) -> Answer | None:
    """His No to the wait that stands, on the board or typed, or None."""
    question = question_of(task)
    answer = question.answer if question else None
    return answer if answer and answer.option == SAID_NO else None


def question(task: Task, now: datetime, shown: str | None) -> Question:
    """The initial question of the wait, with the mark of the file it shows."""
    hold = hold_of(task)
    since = now if hold is None else hold.since
    return Question(
        id=owner_question.key_of(TOPIC, task.slug, since),
        topic=TOPIC,
        question=QUESTION,
        options=OPTIONS,
        digest=shown,
        asked=since,
    )


def asked(task: Task, now: datetime, line: str, shown: str | None) -> Task:
    """The task whose criteria wait for his yes again, under the hold `line`, with a new
    question that shows the file of mark `shown`."""
    hold = OwnerHold(on="criteria", line=line, since=now)
    initial = question(replace(task, hold=hold), now, shown)
    fresh = replace(initial, id=question_keys.fresh(task, initial.id))
    questions = (*task.questions, fresh)
    return replace(task, hold=hold, questions=questions)


def answered(task: Task, question: Question, answer: Answer) -> Task:
    """The task with `answer` to `question`, which it holds or which is new."""
    done = replace(question, answer=answer)
    kept = tuple(one for one in task.questions if one.id != question.id)
    return replace(task, questions=(*kept, done))
