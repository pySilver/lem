"""The view Waits for you (`board_pages.waits_page`, `wait_stack` and `parked_group` on `main`):
one stack for each task with something the owner does, in the place of its first thing, the most
pressing first; then the tasks he parked, of which nothing waits."""

from typing import TYPE_CHECKING

from lem.board.inputs import clock, names
from lem.board.inputs.layout import KeyGroup, Keys
from lem.board.inputs.waits import Parked, Stack, Waits
from lem.board.views import hovers, owed, telling, words
from lem.board.views.waits import rows
from lem.records.decisions import Breaker
from lem.records.holds import Parked as Park

if TYPE_CHECKING:
    from datetime import datetime

    from lem.board.inputs.waits import Wait
    from lem.board.views.world import Seen, World

KEYS = Keys(
    id="waits-keys",
    groups=(
        KeyGroup(keys=("J", "K", "↑", "↓"), word="move"),
        KeyGroup(keys=("Enter",), word="go or open"),
    ),
)


def waits(world: World) -> Waits:
    """The view: the stacks, then the parked tasks."""
    stacks = tuple(stack(world, group) for group in owed.stacks(world))
    held = sorted(filter(is_parked, world.tasks), key=parked_since)
    parked = tuple(parked_of(world, seen) for seen in held)
    return Waits(stacks=stacks, parked=parked)


def stack(world: World, group: tuple) -> Stack:
    """The things of one task, as one stack that opens."""
    seen = owed.seen(world, group[0].task)
    made: tuple[Wait, ...] = tuple(rows.wait(world, seen, row, group) for row in group)
    first = made[0]
    slug = seen.record.task.slug
    return Stack(
        slug=slug,
        id=f"wait-stack-{slug}",
        look=first.look,
        icon=first.icon,
        title=first.task,
        count=names.plural(len(made), "thing"),
        first=first.verb,
        state=first.state,
        waits=made,
    )


def parked_of(world: World, seen: Seen) -> Parked:
    """A task the owner put aside: since when, why in his words, the breaker that stopped its
    build, and the line that brings it back."""
    task = seen.record.task
    since = parked_since(seen)
    stamp = clock.stamp(since, world.clock.now, world.clock.zone)
    shown = telling.said(seen.record)
    return Parked(
        slug=task.slug,
        title=names.title_of(task.slug),
        href=names.task_href(world.viewer.base, task.slug, under="waits"),
        since=clock.since(since, world.clock.now, f"parked at {stamp}"),
        parked_at=f"Parked at {stamp}",
        why=words.capital(shown) if shown else "No reason is on record.",
        breaker=breaker_line(seen),
        resume=f"/lem resume {task.slug}",
    )


def is_parked(seen: Seen) -> bool:
    """Whether the owner parked the task."""
    return isinstance(seen.record.task.hold, Park)


def parked_since(seen: Seen) -> datetime:
    """When the owner parked the task."""
    task = seen.record.task
    return task.hold.since if isinstance(task.hold, Park) else task.since


def breaker_line(seen: Seen) -> str | None:
    """The breaker that stopped the parked task's build, in words, or None."""
    breakers = [one for one in seen.record.task.decisions if isinstance(one, Breaker)]
    if not breakers:
        return None
    newest = breakers[-1]
    why = hovers.stop_words(newest)
    return f"Breaker {newest.id} stopped its build: “{newest.what}”, since {why}."
