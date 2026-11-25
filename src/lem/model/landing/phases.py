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
from lem.model.landing.mergeread import another_round, latest
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
# A task that ended with no landing, whose worktree and branch `clean` removes.
ENDS = frozenset(("dropped", "answered"))


def preparing(record: Record, world: World) -> Due:
    """The first row of `preparing` whose evidence does not hold."""
    for rule in PREPARING:
        found = rule(record, world)
        if isinstance(found, Due):
            return found
    return Due(step="wait", why="every step holds: the forge has the pull request")


def opened(record: Record, world: World) -> Due:
    """The due step of an open pull request: what a merge call left, a new round (a tip that
    moved, a read that says another round), the merge agent's read, then the merge."""
    landing = record.landing or Landing()
    left = reconcile.pending(landing, world)
    if left is not None:
        return left
    proposed = landing.proposed
    if proposed is None or proposed.tip != world.tip:
        return Due(step="start", why="the tip moved after the proposal: a new round")
    if another_round(landing) is not None:
        why = (
            "the merge agent's read of this tip says the moved base needs another round"
        )
        return Due(step="start", why=f"{why}: a new round")
    if read_due(landing, world):
        why = "no read of the merge agent covers this tip on origin's base as it is now"
        return Due(step="merge-review", why=why)
    return merge.due(record, world)


def read_due(landing: Landing, world: World) -> bool:
    """Whether the merge agent reads first: no read of the tip settled yet, or Lem refused
    the merge of the tip for a base that moved and no read covers origin's base now. A merge
    on a base that moved since the read is tried, and refused for the base under the merge
    lock, which keeps that refusal (`landing.md` E, "Base moved, open PR")."""
    if latest(landing) is None:
        return True
    refused = landing.refused
    tip = landing.proposed.tip if landing.proposed else None
    for_base = refused is not None and (refused.source, refused.kind, refused.tip) == (
        "lem",
        "base",
        tip,
    )
    return for_base and latest(landing, world.base_tree) is None


def settled(record: Record) -> Due | None:
    """The due step that the record alone decides, with no look at git or the forge: a task
    not ready to land, one that ended, a landing after the forge's merge; None while the
    landing prepares or its pull request is open, which the world decides."""
    landing = record.landing or Landing()
    status = record.task.status
    if status in ENDS:
        return ended(landing)
    if status not in LANDS:
        return Due(step="none", why=f"the task is {status}: it lands once it is ready")
    if landing.phase in {"merged", "ended"}:
        return after(record)
    return None


def due(record: Record, world: World) -> Due:
    """The step that is due for the task now, and why."""
    found = settled(record)
    if found is not None:
        return found
    if (record.landing or Landing()).phase == "open":
        return opened(record, world)
    return preparing(record, world)


def ended(landing: Landing) -> Due:
    """The step of a task dropped or answered: its cleanup, then nothing."""
    if landing.phase == "ended":
        return Due(step="done", why="the task ended, and its cleanup ran")
    return Due(step="clean", why="the task ended: its worktree goes")


def after(record: Record) -> Due:
    """The steps after the forge's merge: its bookkeeping, the cleanup, the end."""
    landing = record.landing or Landing()
    if landing.phase == "ended":
        return Due(step="done", why="the landing ended")
    if record.task.status != "landed":
        return Due(step="merged", why="the forge merged it: its bookkeeping is due")
    return Due(step="clean", why="it landed: its worktree and branch go")
