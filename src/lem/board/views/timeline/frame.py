"""The span of a task's time the card draws (`time_end` and the start of `time_of` on `main`): from
its first moment on record to its last while it ended, or to now while it runs (moved on in
steps of fifteen seconds, so that the drawing holds still between two refreshes); and a stretch
of it as a lane held it.

A stretch with no end runs to now while the task runs; once the task ended it is a moment where
it began, since no end of it is on record. Nothing here guesses a time no record holds.
"""

from typing import TYPE_CHECKING, NamedTuple

from lem.board.views import rule
from lem.board.views.activity import axis
from lem.board.views.timeline.shapes import Held, Moment

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.record import Record

type Drawn = Held | Moment


class Frame(NamedTuple):
    """The drawing's first and last moment, and whether the task ended."""

    start: datetime
    end: datetime
    ended: bool


def frame_of(record: Record, now: datetime) -> Frame:
    """The span of the task's time up to `now`."""
    moments = [entry.at for entry in record.journal]
    starts = [span.start for span in record.task.spans]
    first = min([record.task.opened, *moments, *starts])
    ended = record.task.status in rule.ENDED
    end = max([first, *moments]) if ended else axis.coarse(now)
    return Frame(start=first, end=end, ended=ended)


def ran(
    frame: Frame,
    lane: str,
    start: datetime,
    end: datetime | None,
    said: tuple[str, str],
) -> Drawn:
    """A stretch lane `lane` held from `start` to `end`, with its head and line `said`."""
    head, sub = said
    if end is not None:
        return Held(lane, start, max(start, end), head, sub)
    if not frame.ended:
        return Held(lane, start, frame.end, head, sub, live=True)
    return Moment(lane, start, f"{head}: its start", "no record of its end")


def gaps(
    start: datetime, end: datetime, covers: list[tuple[datetime, datetime]]
) -> list[tuple[datetime, datetime]]:
    """The pieces of `start` to `end` that no stretch of `covers` holds."""
    cut = sorted(
        (max(start, begun), min(end, ended))
        for begun, ended in covers
        if begun < end and ended > start
    )
    pieces = []
    reach = start
    for begun, ended in cut:
        if begun > reach:
            pieces.append((reach, begun))
        reach = max(reach, ended)
    if reach < end:
        pieces.append((reach, end))
    return pieces
