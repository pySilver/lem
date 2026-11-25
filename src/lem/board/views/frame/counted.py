"""What the frame of every page counts of a workspace, read once: the stacks of what waits for
the owner, where each task stands, and the numbers the title, the bars, the sidebar and the
switcher say (`board_pages.layout`, `summary_of` and `space_says` on `main`)."""

from typing import TYPE_CHECKING, NamedTuple

from lem.board.inputs.names import plural
from lem.board.views import owed, standing

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World
    from lem.model.owner.looks import Rows


class Counted(NamedTuple):
    """The workspace's stacks of what waits, each task with where it stands, and its
    numbers."""

    stacks: tuple[Rows, ...]
    placed: tuple[tuple[Seen, standing.Standing], ...]

    @property
    def waits(self) -> int:
        """How many tasks wait for the owner."""
        return len(self.stacks)

    @property
    def things(self) -> int:
        """How many things the owner does, in those tasks."""
        return sum(len(group) for group in self.stacks)

    def count(self, column: str, status: str | None = None) -> int:
        """How many tasks stand in `column`, of `status` when it is named."""
        return sum(
            1
            for seen, where in self.placed
            if where.column == column and status in {None, seen.record.task.status}
        )


def counted(world: World) -> Counted:
    """The counts of the world."""
    rows = owed.rows(world)
    placed = tuple(
        (seen, standing.standing(seen, mine(rows, seen))) for seen in world.tasks
    )
    return Counted(stacks=owed.stacks(world), placed=placed)


def mine(rows: Rows, seen: Seen) -> Rows:
    """The rows of the task of `seen`."""
    slug = seen.record.task.slug
    return tuple(row for row in rows if row.task == slug)


def waits_said(count: int) -> str:
    """`5 wait for you`, `1 waits for you`."""
    verb = "waits" if count == 1 else "wait"
    return f"{count} {verb} for you"


def tasks_said(count: int) -> str:
    """`5 tasks wait for you`, `1 task waits for you`."""
    verb = "waits" if count == 1 else "wait"
    return f"{plural(count, 'task')} {verb} for you"
