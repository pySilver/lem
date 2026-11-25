"""The view Activity (`board_pages.activity_page` on `main`): where the time of today's tasks went,
one row for each, and every event, the newest first.

The chart's axis runs from the first move of a task it draws to now while one runs (moved on
in steps of fifteen seconds), else to the last move of the last to end; the line of now stands
on it while a task runs.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.board.inputs.activity import Activity
from lem.board.views.activity import axis, feed, lanes, legend, ticks

if TYPE_CHECKING:
    from datetime import datetime

    from lem.board.views.world import World


def activity(world: World) -> Activity:
    """The view of the world's tasks."""
    rows, count = feed.everything(world)
    events = feed.count_line(count)
    now = axis.coarse(world.clock.now)
    drawn = lanes.drawn(world, now)
    if not drawn:
        return Activity(day="today", events=events, feed=rows)
    return msgspec.structs.replace(chart(world, drawn, now), events=events, feed=rows)


def chart(world: World, drawn: list[lanes.Drawn], now: datetime) -> Activity:
    """The chart of the tasks drawn: its axis, its rows and its legend."""
    runs = any(held[-1].open for _, held in drawn)
    start = min(held[0].start for _, held in drawn)
    ended = max(held[-1].end for _, held in drawn)
    scale = axis.axis_of(start, now if runs else ended)
    return Activity(
        day=ticks.day(start, world.clock.now, world.clock.zone),
        ticks=ticks.ticks(scale, world.clock.zone),
        now=scale.place(now) if runs and scale.holds(now) else None,
        shades=legend.shades(drawn, world.clock.now),
        lanes=tuple(lanes.lane(world, pair, scale) for pair in drawn),
        events="",
    )
