"""The breaker that stopped a task's build (`Task.stopped` on `main`): the one that waits for the
owner, or, for a parked task, the one the park put aside or the newest his help never answered.
Once his help is on record, Artifacts and Criteria and decisions keep it, and the Overview
does not."""

from typing import TYPE_CHECKING

from lem.records.decisions import Breaker, Taken
from lem.records.holds import BreakerHold, Parked

if TYPE_CHECKING:
    from lem.records.task import Task


def stopped(task: Task) -> Breaker | None:
    """The breaker that stopped the task's build, or None."""
    breakers = [one for one in task.decisions if isinstance(one, Breaker)]
    number = number_of(task)
    if number is not None:
        return next((one for one in breakers if one.id == number), None)
    if not isinstance(task.hold, Parked):
        return None
    helped = {one.breaker for one in task.decisions if isinstance(one, Taken)}
    open_ones = [one for one in breakers if one.id not in helped]
    return open_ones[-1] if open_ones else None


def number_of(task: Task) -> int | None:
    """The number of the breaker that holds the task, or that its park put aside."""
    hold = task.hold
    if isinstance(hold, Parked):
        hold = hold.held
    return hold.number if isinstance(hold, BreakerHold) else None
