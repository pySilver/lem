"""The plan and breaker questions of the current hold, as the answer receiver reads them."""

from typing import TYPE_CHECKING

from lem.kernel.clock import compact
from lem.records.holds import BreakerHold, OwnerHold
from lem.records.questions import Question

if TYPE_CHECKING:
    from lem.records.task import Task


def standing(task: Task) -> Question | None:
    """The question of the active plan or breaker hold."""
    hold = task.hold
    if isinstance(hold, BreakerHold):
        first = breaker_of(task, hold)
    elif isinstance(hold, OwnerHold) and hold.on == "plan" and task.status == "planned":
        first = plan_of(task, hold)
    else:
        return None
    return next(
        (one for one in reversed(task.questions) if base_of(one.id) == first.id),
        first,
    )


def breaker_of(task: Task, hold: BreakerHold) -> Question:
    """The question a breaker asks at the start of its hold."""
    stamp = compact(hold.since)
    return Question(
        id=f"breaker:{task.slug}:{hold.number}:{stamp}",
        topic="breaker",
        question=f"Breaker {hold.number} of {task.slug}: help, park or drop the task?",
        options=("help", "park", "drop"),
        asked=hold.since,
    )


def plan_of(task: Task, hold: OwnerHold) -> Question:
    """The question a plan asks at the start of its hold."""
    stamp = compact(hold.since)
    return Question(
        id=f"plan:{task.slug}:{stamp}",
        topic="plan",
        question=f"Build the plan of {task.slug}, or drop the task?",
        options=("build", "drop"),
        asked=hold.since,
    )


def base_of(key: str) -> str:
    """The hold key before any sequence added by a renewed question."""
    base, _, sequence = key.rpartition("-")
    return base if sequence.isdecimal() else key
