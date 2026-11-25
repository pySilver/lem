"""Which questions still wait for the owner on the task's record."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.model.criteria import waits
from lem.model.task.table import ENDED
from lem.records.holds import BreakerHold, OwnerHold, Parked, ReleaseHold

if TYPE_CHECKING:
    from lem.records.questions import Question
    from lem.records.task import Task

# The topic of the question each of his holds asks.
TOPICS = MappingProxyType(
    {
        "interview": "criterion",
        "criteria": "criterion",
        "skip-read": "skip",
        "plan": "plan",
    }
)


def current(task: Task, asked: Question) -> bool:
    """Whether the question still belongs to the task's current wait."""
    hold = task.hold
    if task.status in ENDED or isinstance(hold, (Parked, ReleaseHold)):
        return False
    if asked.topic == "card":
        return True
    if asked.topic == "criterion":
        return waits.question_of(task) == asked
    if asked.topic == "breaker":
        return isinstance(hold, BreakerHold) and asked.asked >= hold.since
    return (
        isinstance(hold, OwnerHold)
        and TOPICS.get(hold.on) == asked.topic
        and asked.asked >= hold.since
        and (asked.topic != "plan" or task.status == "planned")
    )
