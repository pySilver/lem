"""The owner's question for a breaker, including the new question when it resumes."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel import clock
from lem.model.task import question_keys
from lem.records.questions import Question

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.holds import BreakerHold
    from lem.records.task import Task

OPTIONS = ("help", "park", "drop")


def asked(task: Task, hold: BreakerHold) -> Question:
    """The breaker's question, asked when its wait began."""
    stamp = clock.compact(hold.since)
    return Question(
        id=f"breaker:{task.slug}:{hold.number}:{stamp}",
        topic="breaker",
        question=f"Breaker {hold.number} of {task.slug}: help, park or drop the task?",
        options=OPTIONS,
        asked=hold.since,
    )


def current(task: Task, hold: BreakerHold) -> Question:
    """The question for this breaker number and start, including a resumed question."""
    first = asked(task, hold)
    return question_keys.recorded(task, first.id) or first


def renewed(task: Task, hold: BreakerHold, now: Moment) -> Task:
    """A resumed breaker gets a distinct question even in the same second."""
    resumed = replace(hold, since=now)
    first = asked(task, resumed)
    question = replace(first, id=question_keys.fresh(task, first.id))
    return replace(task, hold=resumed, questions=(*task.questions, question))
