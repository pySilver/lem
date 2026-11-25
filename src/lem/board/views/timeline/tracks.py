"""The lanes of the time card as the page prints them (`time_card` on `main`): "You" always, and
each other lane that holds a stretch or a moment; each stretch and moment at its place, with the
moments its tip spans; and on the legend how long the lane held the work and its share.

Each id names its lane and the moment it begins (`ts-builders-1764061740000-1`), counted when
two begin at one moment, so that a refresh keeps it.
"""

from collections import Counter
from typing import TYPE_CHECKING

from lem.board.inputs.task.timeline import Mark, Spell, Track
from lem.board.views.timeline import shapes, shares

if TYPE_CHECKING:
    from datetime import datetime

    from lem.board.views.activity.axis import Axis
    from lem.board.views.timeline.frame import Drawn, Frame

MILLI = 1000


def tracks(found: list[Drawn], scale: Axis, frame: Frame) -> tuple[Track, ...]:
    """The card's lanes."""
    used = {each.lane for each in found}
    lanes = (
        lane for lane in shapes.LANES if lane.key == shapes.YOU or lane.key in used
    )
    return tuple(track(lane, found, scale, frame) for lane in lanes)


def track(lane: shapes.Lane, found: list[Drawn], scale: Axis, frame: Frame) -> Track:
    """One lane: its stretches and moments, and its share on the legend."""
    ids: Counter[str] = Counter()
    mine = [each for each in found if each.lane == lane.key]
    spells = tuple(
        spell(lane, each, scale, ids) for each in mine if isinstance(each, shapes.Held)
    )
    shown = tuple(
        mark(lane, each, scale, ids) for each in mine if isinstance(each, shapes.Moment)
    )
    legend = shares.legend(lane, found, frame)
    return Track(
        key=lane.key,
        label=lane.label,
        fill=lane.fill,
        spells=spells,
        marks=shown,
        held=legend[0],
        held_title=legend[1],
    )


def spell(
    lane: shapes.Lane, each: shapes.Held, scale: Axis, ids: Counter[str]
) -> Spell:
    """A stretch the lane held, with the moments its tip spans (to now while it runs)."""
    left = scale.place(each.start)
    return Spell(
        id=counted(ids, f"ts-{lane.key}-{milli(each.start)}"),
        left=left,
        width=round(scale.place(each.end) - left, 3),
        live=each.live,
        head=f"{lane.label} · {each.head}",
        sub=each.sub or None,
        start=each.start,
        end=None if each.live else each.end,
    )


def mark(
    lane: shapes.Lane, each: shapes.Moment, scale: Axis, ids: Counter[str]
) -> Mark:
    """A moment on the lane."""
    return Mark(
        id=counted(ids, f"tm-{lane.key}-{milli(each.at)}"),
        left=scale.place(each.at),
        head=f"{lane.label} · {each.head}",
        sub=each.sub or None,
        at=each.at,
    )


def counted(ids: Counter[str], key: str) -> str:
    """`key` with how many times it came so far."""
    ids[key] += 1
    return f"{key}-{ids[key]}"


def milli(moment: datetime) -> int:
    """A moment in milliseconds since the epoch."""
    return int(moment.timestamp() * MILLI)
