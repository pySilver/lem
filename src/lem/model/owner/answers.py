"""The owner's answer to a question of a task, on the board or on a card (`answers.py` and
`board_model.answered_of` on `main`).

The first answer counts: a question answered once takes no second answer. An answer carries the
question's id and the digest of what he was shown, so an answer to an older question of the same
topic, or to a text that changed meanwhile, is refused. Once he answered on the board, the row
of that wait is the task's session's until the session took the answer into effect: the list
shows it no more.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.holds import OwnerHold
    from lem.records.questions import Answer, Question
    from lem.records.task import Task

# The topic of the question that each of his waits asks.
TOPICS = MappingProxyType(
    {
        "interview": "criterion",
        "criteria": "criterion",
        "skip-read": "skip",
        "plan": "plan",
    }
)


def taken_by_session(task: Task, topic: str, since: Moment) -> bool:
    """Whether he answered a question of `topic` asked since `since`, and the task's session
    has not taken the answer into effect yet."""
    return any(
        one.topic == topic
        and one.asked >= since
        and one.answer is not None
        and one.took_effect is None
        for one in task.questions
    )


def answered_hold(task: Task, hold: OwnerHold) -> bool:
    """Whether his answer to the question of the hold waits for the task's session."""
    topic = TOPICS.get(hold.on)
    return topic is not None and taken_by_session(task, topic, hold.since)


def answer(task: Task, question_id: str, digest: str | None, given: Answer) -> Task:
    """The task with his answer to the question `question_id`, shown with `digest`; refused
    for a question the task does not hold, one answered already, one a newer question of its
    topic replaced, and a digest that is not the one the question shows."""
    found = [one for one in task.questions if one.id == question_id]
    if not found:
        raise Refusal(
            "question",
            f"{task.slug} holds no question {question_id}",
            f"lem task show {task.slug} names the questions that wait",
        )
    asked = found[0]
    refusal = refused(task, asked, digest)
    if refusal is not None:
        raise refusal
    kept = tuple(one for one in task.questions if one.id != question_id)
    return replace(task, questions=(*kept, replace(asked, answer=given)))


def refused(task: Task, asked: Question, digest: str | None) -> Refusal | None:
    """Why an answer to `asked` with `digest` may not count, or None."""
    why = why_refused(task, asked, digest)
    if why is None:
        return None
    return Refusal("answered", why, "the owner reads the question as it is now")


def why_refused(task: Task, asked: Question, digest: str | None) -> str | None:
    """Why an answer may not count: answered already, asked again, or the text changed."""
    if asked.answer is not None:
        return f"{asked.id} was answered already: the first answer counts"
    newer = newer_of(task, asked)
    if newer is not None:
        return f"{asked.id} was asked again as {newer}"
    if asked.digest is None or digest == asked.digest:
        return None
    return f"the text of {asked.id} changed after the owner saw it"


def newer_of(task: Task, asked: Question) -> str | None:
    """The id of the newest question of the same topic asked after `asked`, or None."""
    newer = [
        one.id
        for one in task.questions
        if one.topic == asked.topic and one.asked > asked.asked
    ]
    return newer[-1] if newer else None
