"""The ticks of a chart's time axis and its first day (`tick_label`, `hms` and the ticks of
`main`'s Activity and time card).

A tick names its date only where the axis passes into another day, and its seconds only on an
axis under six minutes, where six ticks of whole minutes would repeat one minute.
"""

from datetime import timedelta
from typing import TYPE_CHECKING

from lem.board.inputs.activity import Tick
from lem.board.inputs.clock import stamp
from lem.board.views.activity.axis import DECIMALS, MINUTE, PERCENT

if TYPE_CHECKING:
    from datetime import datetime, tzinfo

    from lem.board.views.activity.axis import Axis

# The axis is cut in six; its ticks are the seven edges.
PARTS = 6


def ticks(axis: Axis, zone: tzinfo) -> tuple[Tick, ...]:
    """The seven ticks of the axis."""
    numbers = range(PARTS + 1)
    return tuple(tick(axis, number, zone) for number in numbers)


def tick(axis: Axis, number: int, zone: tzinfo) -> Tick:
    """Tick `number`: its place, its clock, and its date where the axis passes into a day."""
    step = timedelta(seconds=axis.whole / PARTS)
    before = axis.start + step * max(0, number - 1)
    shown = label(axis.start + step * number, before, axis.whole, zone)
    date, _, clock = shown.rpartition(" ")
    return Tick(
        left=round(PERCENT * number / PARTS, DECIMALS),
        clock=clock,
        date=date or None,
        first=number == 0,
        last=number == PARTS,
    )


def label(moment: datetime, before: datetime, whole: float, zone: tzinfo) -> str:
    """A tick's words: to the second on a short axis, with the date when its day is not the
    day of the tick `before` it."""
    shown = stamp(moment, before, zone)
    if whole >= PARTS * MINUTE:
        return shown
    seconds = moment.astimezone(zone).strftime(":%S")
    return f"{shown}{seconds}"


def day(start: datetime, now: datetime, zone: tzinfo) -> str:
    """The axis's first day: `today`, or its date."""
    here = start.astimezone(zone)
    if here.date() == now.astimezone(zone).date():
        return "today"
    month = here.strftime("%b")
    return f"{month} {here.day}"
