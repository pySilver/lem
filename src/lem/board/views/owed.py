"""What waits for the owner in a workspace, as every view counts it: the rows of
`model/owner/waiting.py` from the world's look at each task, and the same rows by task.

The sidebar, the title, the phone's icon, Waits for you and a task's header all read these
rows, so that each place says the same.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.model.owner import waiting

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Look, Row, Rows


def look_of(seen: Seen, conflicts: frozenset[str]) -> Look:
    """One task as the list reads it."""
    return replace(
        seen.merge_look(),
        session=seen.session,
        stop=seen.stop,
        worktree=seen.worktree,
        conflict=seen.record.task.slug in conflicts,
    )


def rows(world: World) -> Rows:
    """Every row of what waits for the owner, in the list's order."""
    conflicts = world.forge.conflicts
    looks = tuple(look_of(seen, conflicts) for seen in world.tasks)
    return waiting.rows(looks, away=world.presence.away, now=world.clock.now)


def stacks(world: World) -> tuple[Rows, ...]:
    """The rows by task, each in the place of its first row."""
    return waiting.stacks(rows(world))


def of_task(world: World, slug: str) -> tuple[Row, ...]:
    """The rows of one task, in the list's order."""
    return mine(rows(world), slug)


def mine(found: Rows, slug: str) -> Rows:
    """The rows of `found` that are of the task `slug`."""
    return tuple(row for row in found if row.task == slug)


def seen(world: World, slug: str) -> Seen:
    """The task `slug` of the world."""
    return next(each for each in world.tasks if each.record.task.slug == slug)
