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
from lem.model.landing.careful_words import after_proposal
from lem.model.landing.merge_evidence import hold_refusal
from lem.model.landing.merge_recheck import due as recheck_due
from lem.model.landing.mergeread import another_round, latest
from lem.model.landing.repair_limit import due as repair_due
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
MERGED = "merged"
LANDS = frozenset(("ready", "landing", "open", "landed"))
# A task that ended with no landing, whose worktree and branch `clean` removes.
ENDS = frozenset(("dropped", "answered"))


def preparing(record: Record, world: World) -> Due:
    """The first row of `preparing` whose evidence does not hold; first, a pull request on
    record that the forge merged meanwhile (the owner's merge on GitHub while a new round runs
    its checks, `main:land.cmd_merged`), whose bookkeeping comes before any row. A request
    closed meanwhile is refused by `propose`, which names `merged`, taken beside it
    (`app/landing/merged.py: admits`)."""
    pull = world.pull
    if (record.landing or Landing()).pull and pull and pull.state == MERGED:
        return Due(step=MERGED, why="the forge shows the pull request merged")
    repair = repair_due(record.task)
    if repair is not None:
        return repair
    for rule in PREPARING:
        found = rule(record, world)
        if isinstance(found, Due):
            return found
    # The proposal is always due in the preparing phase.
    return Due(  # pragma: no mutate
        step="wait",  # pragma: no mutate
        why="every step holds: the forge has the pull request",  # pragma: no mutate
    )


def pending(record: Record, world: World, landing: Landing) -> Due | None:
    """Settle the forge's answer first, then honor the park or seat block."""
    left = reconcile.pending(landing, world)
    if left is not None and (left.step != "merge" or landing.intent is not None):
        return left
    refused = hold_refusal(record)
    if refused is not None:
        return Due(step="wait", why=f"{refused.why}; {refused.fix}")
    if after_proposal(record):
        return Due(
            step=start.STEP, why="the owner called the request careful: a new round"
        )
    checked = checks.holds(record, world)
    if (
        isinstance(checked, Due)
        and landing.proposed
        and landing.proposed.tip == world.tip
    ):
        return Due(step="start", why=f"{checked.why}: a new round")
    return left or recheck_due(landing, world)


def opened(record: Record, world: World) -> Due:
    """The due step of an open pull request: what a merge call left, a new round (a tip that
    moved, a read that says another round), the merge agent's read, then the merge."""
    landing = record.landing or Landing()
    left = pending(record, world, landing)
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
    if latest(landing, world.base_tree) is None:
        why = "no read of the merge agent covers this tip on origin's base as it is now"
        return Due(step="merge-review", why=why)
    return merge.due(record, world)


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
