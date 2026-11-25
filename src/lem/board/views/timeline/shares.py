"""How long each lane held the work and its share of the task's time (`time_of`'s totals and
`time_shares` on `main`): two stretches of one lane that overlap count once, and two lanes can
hold the same minutes (a builder inside the agent's span, the owner's wait beside the personas'
read), so the shares as shown may add up past 100."""

import math
from typing import TYPE_CHECKING

from lem.board.inputs.clock import length
from lem.board.views.timeline import shapes

if TYPE_CHECKING:
    from datetime import datetime

    from lem.board.views.timeline.frame import Drawn, Frame

PERCENT = 100
# The shares say they overlap only when the lanes' time passes the whole by more than this, so
# that a rounding of the shares to 101 says nothing (`OVERLAP_RATIO` on `main`).
OVERLAP = 1.005


def held_for(
    lane: str, held: list[shapes.Held], start: datetime, end: datetime
) -> float:
    """The seconds lane `lane` held the work between `start` and `end`."""
    parts = sorted(
        (max(start, each.start), min(end, each.end))
        for each in held
        if each.lane == lane
    )
    total: float = 0
    reach = start
    for begun, ended in parts:
        if ended > reach:
            total += (ended - max(begun, reach)).total_seconds()
            reach = ended
    return total


def share(total: float, whole: float) -> int:
    """A lane's share of the task's time, in whole percents."""
    return math.floor(PERCENT * total / whole + 0.5)


def over(totals: list[float], whole: float) -> int | None:
    """What the shares add up to, when two lanes held the same minutes and they pass 100."""
    shown = sum(share(total, whole) for total in totals)
    if sum(totals) > whole * OVERLAP and shown > PERCENT:
        return shown
    return None


def legend(
    lane: shapes.Lane, found: list[Drawn], frame: Frame
) -> tuple[str | None, str | None]:
    """How long the lane held the work and its share, and the hover that says of what; none for
    a lane that held nothing."""
    total = total_of(lane.key, found, frame)
    if total <= 0:
        return None, None
    took, whole = length(total), whole_of(frame)
    shown = f"{took} · {share(total, whole)}%"
    return shown, f"{lane.label} held the work for {took} of the task’s {length(whole)}"


def total_of(key: str, found: list[Drawn], frame: Frame) -> float:
    """The seconds lane `key` held the work in the task's time."""
    held = [each for each in found if isinstance(each, shapes.Held)]
    return held_for(key, held, frame.start, frame.end)


def whole_of(frame: Frame) -> float:
    """The task's whole time in seconds, at least one."""
    return max(1.0, (frame.end - frame.start).total_seconds())
