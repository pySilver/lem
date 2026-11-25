"""The feed's words of a seat whose agent gave an error (`Task.stand_ins`): the fallback that
stood in, or the block when none did, and the owner's go on that tries the seat again
(`seat.stand-in`, `seat.blocked` and `seat.again` of `main`'s `SAYS`). Each is told at its own
moment."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.views.activity.told import ALERT, LEM, SPLIT, USER, YOU, Told
from lem.records.holds import Blocked

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.task import Task
    from lem.records.work import StandIn

SEATS = MappingProxyType(
    {
        "reviewer": "the reviewer",
        "planner": "the planner",
        "merger": "the merge agent",
    }
)


def seat(stood: StandIn, task: Task) -> tuple[tuple[datetime, Told], ...]:
    """The seat's error, and the go on when the owner gave one."""
    told = stood_in(stood) if stood.took else blocked(stood, task)
    first = (stood.at, told)
    if stood.again is None:
        return (first,)
    who = SEATS[stood.seat]
    said = f"your go on: {who} {stood.failed} is tried again"
    go_on = Told(YOU, USER, "Your go on: the seat is tried again", said)
    return first, (stood.again, go_on)


def stood_in(stood: StandIn) -> Told:
    """The fallback that stood in for the seat, and what the failed agent said."""
    who = SEATS[stood.seat]
    took = f"{stood.took} in place of {stood.failed}"
    return Told(
        LEM,
        SPLIT,
        f"The fallback stood in for {who}",
        took,
        stood.said or stood.error,
    )


def blocked(stood: StandIn, task: Task) -> Told:
    """A seat no fallback stood in for: the task's block says why, while it holds it."""
    who = SEATS[stood.seat]
    hold = task.hold
    said = stood.failed
    if isinstance(hold, Blocked) and hold.seat == stood.seat:
        said = hold.why
    head = f"The seat of {who} gave an error, and no fallback stood in"
    return Told(YOU, ALERT, head, said, stood.said or "")
