"""The rows of the chart Where the time went (`board_pages.timeline` on `main`): one for each
task that runs or ended today, the first to begin on top, each a bar for every state it held in
the color of who acted then, with its status, who acted and its times in its hover.

A row appears when a task writes its first state.
"""

from typing import TYPE_CHECKING

from lem.board.inputs.activity import Lane, Stretch
from lem.board.inputs.clock import length, stamp
from lem.board.views import rule
from lem.board.views.activity import feed, states, stretches

if TYPE_CHECKING:
    from datetime import datetime

    from lem.board.views.activity.axis import Axis
    from lem.board.views.world import Seen, World

type Drawn = tuple[Seen, tuple[stretches.Stretch, ...]]


def drawn(world: World, end: datetime) -> list[Drawn]:
    """The tasks the chart draws, each with its stretches up to `end`, the first to begin
    first: every task that runs, and each that ended today."""
    found = [
        (seen, stretches.stretches(seen.record, end))
        for seen in world.tasks
        if today(world, seen)
    ]
    return sorted(
        ((seen, held) for seen, held in found if held),
        key=lambda pair: pair[1][0].start,
    )


def today(world: World, seen: Seen) -> bool:
    """Whether a task runs, or ended on the day of the page."""
    task = seen.record.task
    zone = world.clock.zone
    ended = task.since.astimezone(zone).date()
    return (
        task.status not in rule.ENDED
        or ended == world.clock.now.astimezone(zone).date()
    )


def lane(world: World, pair: Drawn, axis: Axis) -> Lane:
    """A task's row, its title linked to its Timeline."""
    seen, held = pair
    shown = tuple(piece(world, each, axis) for each in held)
    link = feed.task_link(world, seen)
    return Lane(slug=seen.record.task.slug, task=link, stretches=shown)


def piece(world: World, held: stretches.Stretch, axis: Axis) -> Stretch:
    """One stretch on the row: a bar, or a dot where an ended task's last state is a moment."""
    said = states.said_of(held.key)
    left = axis.place(held.start)
    if held.end == held.start and not held.open:
        title = f"{said.label} at {at(world, held.start)}"
        return Stretch(
            left=left, width=0, status=held.key, look=said.look, dot=True, title=title
        )
    width = round(axis.place(held.end) - left, 3)
    return Stretch(
        left=left,
        width=width,
        status=held.key,
        look=said.look,
        live=held.open and said.live,
        title=hover(world, held),
    )


def hover(world: World, held: stretches.Stretch) -> str:
    """`Building · The agent · 14:09 to now · 1h 51m`."""
    said = states.said_of(held.key)
    end = world.clock.now if held.open else held.end
    to = "now" if held.open else at(world, end)
    took = length((end - held.start).total_seconds())
    begun = at(world, held.start)
    return f"{said.label} · {said.who} · {begun} to {to} · {took}"


def at(world: World, moment: datetime) -> str:
    """A moment's clock time on the page."""
    return stamp(moment, world.clock.now, world.clock.zone)
