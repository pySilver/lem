"""The card Where the time went of a task's Timeline (`board_task.time_card` on `main`): one lane
for each who held the work, the stages as bands behind them, the task's whole time and the
shares on the legend, and the axis from the task's first moment."""

from typing import TYPE_CHECKING

from lem.board.inputs.clock import length
from lem.board.inputs.task.timeline import Band, Time
from lem.board.views.activity import axis, ticks
from lem.board.views.timeline import drawn, shapes, shares, stages, tracks

if TYPE_CHECKING:
    from lem.board.inputs.text import Look
    from lem.board.views.timeline.frame import Frame
    from lem.board.views.world import Clock
    from lem.records.record import Record

OVER = "the shares add up to {over}%, as two rows can hold the same minutes"


def time_card(record: Record, look: Look, frame: Frame, clock: Clock) -> Time:
    """The card of the task's time."""
    found = drawn.drawn(record, frame)
    scale = axis.axis_of(frame.start, frame.end)
    shown = ticks.ticks(scale, clock.zone)
    whole = length(shares.whole_of(frame))
    return Time(
        look=look,
        whole=f"{whole} in all",
        over=over_of(found, frame),
        bands=bands(record, frame, scale),
        tracks=tracks.tracks(found, scale, frame),
        day=ticks.day(frame.start, clock.now, clock.zone),
        ticks=shown,
        dated=any(tick.date for tick in shown),
        now=None if frame.ended else scale.place(frame.end),
    )


def over_of(found: list[drawn.Drawn], frame: Frame) -> str | None:
    """What the shares add up to, said, when they pass 100."""
    totals = [shares.total_of(lane.key, found, frame) for lane in shapes.LANES]
    added = shares.over(
        [total for total in totals if total > 0], shares.whole_of(frame)
    )
    return None if added is None else OVER.format(over=added)


def bands(record: Record, frame: Frame, scale: axis.Axis) -> tuple[Band, ...]:
    """The task's stages, each with its id."""
    slug = record.task.slug
    found = enumerate(stages.stages(record, frame))
    return tuple(
        band(f"tb-{slug}-{number}", number, stage, scale) for number, stage in found
    )


def band(ident: str, number: int, stage: shapes.Stage, scale: axis.Axis) -> Band:
    """A stage behind every lane, every other one shaded."""
    left = scale.place(stage.start)
    return Band(
        id=ident,
        left=left,
        width=round(max(0, scale.place(stage.end) - left), 3),
        odd=number % 2 == 1,
        now=stage.live,
        short=stage.short,
        head=stage.label,
        sub=stage.sub or None,
        start=stage.start,
        end=None if stage.live else stage.end,
    )
