"""The row of criteria the personas did not read (`board_task.criteria_head` on `main`): the fast
track's one criterion, which they never read, or the standard track's, not yet or not at all."""

from typing import TYPE_CHECKING

from lem.board.inputs.parts import Row

if TYPE_CHECKING:
    from lem.board.views.world import Seen

READ = "crit-read"
ENDED = frozenset(("landed", "answered", "dropped"))


def unread(seen: Seen) -> Row | None:
    """The row of criteria the personas did not read: the fast track's one criterion, or
    criteria of the standard track; none before there is a size."""
    task = seen.record.task
    sizes = [one.size for one in task.criteria.approvals]
    size = task.criteria.size or next(reversed(sizes), None)
    if size is None:
        return None
    said = "The personas have not read these criteria yet."
    if task.status in ENDED:
        said = "The personas did not read these criteria."
    if size == "small":
        said = "The personas do not read the one criterion of a task on the fast track."
    return Row(id=READ, look="quiet", icon="users", head=said)
