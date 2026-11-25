"""The facts behind questions that stop a task."""

from typing import TYPE_CHECKING, TypeIs

from lem.records.decisions import Breaker
from lem.records.holds import BreakerHold

if TYPE_CHECKING:
    from lem.addons.inbox.source import RowFacts
    from lem.records.holds import Blocked


def breaker(found: RowFacts) -> str:
    """Use the matching breaker's summary, with the reason and the owner's options."""
    task = found.look.record.task
    hold = task.hold
    if isinstance(hold, BreakerHold):
        for decision in reversed(task.decisions):
            if matches(decision, hold):
                return f"{decision.what} Give the next step with Help."
    return found.row.why or task.ask


def matches(decision: object, hold: BreakerHold) -> TypeIs[Breaker]:
    """Whether this is the breaker that still holds the task."""
    return isinstance(decision, Breaker) and decision.id == hold.number


def block(slug: str, hold: Blocked) -> str:
    """The block and its next step, including the owner's drop command."""
    return f"{hold.why} {hold.fix} The owner can also run /lem drop {slug}."
