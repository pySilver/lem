"""The owner's question for a breaker, including the new question when it resumes."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel import clock
from lem.records.questions import Question

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.holds import BreakerHold
    from lem.records.task import Task

OPTIONS = ("help", "park", "drop")


def asked(task: Task, hold: BreakerHold, *, suffix: str = "") -> Question:
    """The breaker's question, asked when its wait began."""
    stamp = clock.compact(hold.since)
    return Question(
        id=f"breaker:{task.slug}:{hold.number}:{stamp}{suffix}",
        topic="breaker",
        question=f"Breaker {hold.number} of {task.slug}: help, park or drop the task?",
        options=OPTIONS,
        asked=hold.since,
    )


def renewed(task: Task, hold: BreakerHold, now: Moment) -> Task:
    """A resumed breaker gets a distinct question even in the same second."""
    resumed = replace(hold, since=now)
    number = len(task.questions) + 1
    question = asked(task, resumed, suffix=f"-{number}")
    return replace(task, hold=resumed, questions=(*task.questions, question))
