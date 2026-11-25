"""The due step of a landing, derived from the record's evidence and the world gathered now
(`landing.md` B and C): `due(record, world) -> Due`.

Inside an explicit phase the due step is the first whose evidence does not hold. Nothing here
remembers what the last step did: a step cut off after its effect and before its record is due
again, and finds its effect in the world.
"""

from collections.abc import Callable

from lem.model.landing import (
    base,
    checks,
    filing,
    merge,
    propose,
    reconcile,
    review,
    start,
)
from lem.model.landing.mergeread import usable
from lem.model.landing.world import Due, Held, World
from lem.records.landing.record import Landing
from lem.records.record import Record

type Rule = Callable[[Record, World], Held | Due]
# The rows of `preparing`, in their order (`landing.md` C).
PREPARING: tuple[Rule, ...] = (
    start.holds,
    base.holds,
    checks.polished,
    checks.holds,
    review.holds,
    filing.holds,
    propose.holds,
)
LANDS = frozenset(("ready", "landing", "open", "landed"))


def preparing(record: Record, world: World) -> Due:
    """The first row of `preparing` whose evidence does not hold."""
    for rule in PREPARING:
        found = rule(record, world)
        if isinstance(found, Due):
            return found
    return Due(step="wait", why="every step holds: the forge has the pull request")


def opened(record: Record, world: World) -> Due:
    """The due step of an open pull request: what a merge call left, a new round, the merge
    agent's read, then the merge."""
    landing = record.landing or Landing()
    left = reconcile.pending(landing, world)
    if left is not None:
        return left
    proposed = landing.proposed
    if proposed is None or proposed.tip != world.tip:
        return Due(step="start", why="the tip moved after the proposal: a new round")
    if usable(landing, world) is None:
        why = "no read of the merge agent covers this tip"
        return Due(step="merge-review", why=why)
    return merge.due(record, world)


def due(record: Record, world: World) -> Due:
    """The step that is due for the task now, and why."""
    landing = record.landing or Landing()
    status = record.task.status
    if status not in LANDS:
        return Due(step="none", why=f"the task is {status}: it lands once it is ready")
    if landing.phase == "open":
        return opened(record, world)
    if landing.phase == "preparing":
        return preparing(record, world)
    return after(record)


def after(record: Record) -> Due:
    """The steps after the forge's merge: its bookkeeping, the cleanup, the end."""
    landing = record.landing or Landing()
    if landing.phase == "ended":
        return Due(step="done", why="the landing ended")
    if record.task.status != "landed":
        return Due(step="merged", why="the forge merged it: its bookkeeping is due")
    return Due(step="clean", why="it landed: its worktree and branch go")
