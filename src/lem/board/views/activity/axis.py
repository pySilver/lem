"""The time axis of a chart (`nice_ceil` and the axis of `main`'s Activity and time card): a
length that reads well from the first moment drawn, and a place on it as a percent of the
chart's width."""

import math
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

MINUTE = 60
DAY = 24 * 60 * MINUTE
NICE_MINUTES = (
    1,
    2,
    5,
    10,
    15,
    20,
    30,
    45,
    60,
    90,
    120,
    180,
    240,
    360,
    480,
    720,
    1080,
)
PERCENT = 100
# While a task runs, the end of the axis moves on in steps of this many seconds, so that the
# drawing holds still between two refreshes (`LIVE_TICK_MS` on `main`).
STEP = 15
# A place is written to this many decimals, as `main`'s pages printed it.
DECIMALS = 3


@dataclass(frozen=True, slots=True)
class Axis:
    """A chart's axis: its first moment and its length in seconds."""

    start: datetime
    whole: float

    def place(self, moment: datetime) -> float:
        """Where `moment` is, as a percent of the axis, held inside it."""
        offset = (moment - self.start).total_seconds()
        held = min(self.whole, max(0, offset))
        return round(PERCENT * held / self.whole, DECIMALS)

    def holds(self, moment: datetime) -> bool:
        """Whether `moment` is not past the axis's end."""
        return (moment - self.start).total_seconds() <= self.whole


def axis_of(start: datetime, end: datetime) -> Axis:
    """The axis from `start` that holds `end`, at least a minute long."""
    span = max(MINUTE, (end - start).total_seconds())
    return Axis(start=start, whole=nice(span))


def nice(seconds: float) -> float:
    """The next length of NICE_MINUTES, or whole days past them."""
    fits = (each * MINUTE for each in NICE_MINUTES if each * MINUTE >= seconds)
    found = next(fits, None)
    if found is None:
        found = math.ceil(seconds / DAY) * DAY
    return float(found)


def coarse(now: datetime) -> datetime:
    """`now`, moved on to the next step of STEP seconds."""
    since = now.timestamp()
    stepped = math.ceil(since / STEP) * STEP
    return now + timedelta(seconds=stepped - since)
