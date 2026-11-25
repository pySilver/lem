"""The page of the older ended tasks, `/HOST/WORKSPACE/done` (`board_pages.older_page` and
`board_model.done_older` on `main`): the ended tasks Done has no card for, those after its newest
`kanban_order.SHOWN`, the newest first, each with how and when it ended and its pull request; and
the way back to the newer ones in Done.
"""

from typing import TYPE_CHECKING

from lem.board.inputs import clock, names
from lem.board.inputs.parts import Link, When
from lem.board.inputs.tasks import Ended, Older
from lem.board.views import kanban_order, owed, rule, standing

if TYPE_CHECKING:
    from collections.abc import Iterator

    from lem.board.views.world import Seen, World

DONE = "done"
EMPTY = (
    f"Done shows every ended task: none is older than its {kanban_order.SHOWN} newest"
)


def older(world: World) -> Older:
    """The page of the world's older ended tasks."""
    ordered = kanban_order.ordered(DONE, list(ended(world)))
    shown = ordered[kanban_order.SHOWN :]
    rows = tuple(row(world, seen, where) for seen, where in shown)
    return Older(
        rows=rows,
        newer=newer_link(world, len(ordered) - len(rows)),
        empty=None if rows else EMPTY,
    )


def ended(world: World) -> Iterator[kanban_order.Placed]:
    """Each ended task with where it stands."""
    for seen in world.tasks:
        task = seen.record.task
        if task.status in rule.ENDED:
            yield seen, standing.standing(seen, owed.of_task(world, task.slug))


def row(world: World, seen: Seen, where: standing.Standing) -> Ended:
    """An ended task: how and when it ended, its board and its pull request."""
    record = seen.record
    slug = record.task.slug
    pull = record.landing.pull if record.landing else None
    return Ended(
        slug=slug,
        title=names.title_of(slug),
        href=names.task_href(world.viewer.base, slug, under=DONE),
        look=where.look,
        icon=where.icon,
        label=where.label,
        pull=names.pull_chip(pull) if pull else None,
        ended=ended_at(world, where),
    )


def ended_at(world: World, where: standing.Standing) -> When:
    """When the task ended, as a clock time."""
    now, zone = world.clock.now, world.clock.zone
    shown = clock.stamp(where.since, now, zone)
    return clock.fixed(where.since, now, zone, f"ended {shown}")


def newer_link(world: World, count: int) -> Link:
    """The way back to the ended tasks that have their card in Done."""
    verb = "is" if count == 1 else "are"
    newer = names.plural(count, "newer one")
    base = world.viewer.base
    return Link(href=f"{base}/", label=f"the {newer} {verb} in Done")
