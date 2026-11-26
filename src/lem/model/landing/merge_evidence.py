"""What a merge checks against the world read again under the merge lock (`landing.md` H 1, 2
and 4; `main:land.merge_locked`): the pull request as proposed and into the task's base, the
local tip, the checks of that tip, and origin's base. An owner-approved merge takes checks on
the current base commit. The merge agent can use a safe read of a moved base.

The forge pins only the head; everything else is read again here, before the intent is
written. `checks` is the tree of the base the checks ran on, which the app reads from git.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import checks, destination, merge_recheck, mergeread
from lem.model.landing.invariants import protected
from lem.model.landing.world import Due, World
from lem.model.task.release import guard
from lem.model.task.table import held_refusal
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.landing.propose import Proposed
    from lem.records.record import Record

TIP = "tip"


def hold_refusal(record: Record) -> Refusal | None:
    """A park or failed seat stops a new merge."""
    # The hold gives the same refusal for every destination other than dropped.
    return held_refusal(record.task, "open")  # pragma: no mutate


def new_call_refusal(record: Record) -> Refusal | None:
    """A release stop, park or seat block prevents a new call to the forge."""
    return guard(record) or hold_refusal(record)


def forge_side(record: Record, world: World, proposed: Proposed) -> Refusal | None:
    """Why the pull request is not the one proposed: not the one on record, not open,
    retargeted before the merge, or at another head."""
    slug, pull = record.task.slug, world.pull
    base = destination.recorded(record.landing) or world.rules.base
    wrong = destination.same_pull(record, (pull.number, pull.url) if pull else None)
    if wrong is not None or pull is None:
        return wrong
    if pull.state != "open":
        return Refusal(
            "closed",
            f"the pull request {pull.url} is {pull.state} on GitHub: nothing was merged",
            f"lem land merged {slug} writes it down first",
        )
    if pull.base != base:
        return Refusal(
            "target",
            f"the pull request {pull.url} is on {pull.base} on GitHub, not on {base}, the "
            "base of the task: its base was changed there; nothing was merged",
            f"gh pr edit {pull.number} --base {base}, then lem land merge {slug} again",
        )
    if pull.head != proposed.tip:
        return Refusal(
            TIP,
            f"the pull request's head is {pull.head}, not the proposed {proposed.tip}",
            f"lem land next {slug} names the new round",
        )
    return None


def covered(record: Record, world: World, tip: str) -> Refusal | None:
    """Why no passed run of the checks covers `tip` with the definitions as now (H 1), by the
    checks' own rule."""
    found = checks.holds(record, replace(world, tip=tip))
    if not isinstance(found, Due):
        return None
    slug = record.task.slug
    return Refusal(
        "checks-changed",
        f"no passed run of the checks covers {tip} with the checks as they are now: "
        f"{found.why}",
        f"lem land next {slug} names the step that runs them",
    )


def changed_tip(record: Record, proposed: Proposed, tip: str | None) -> Refusal | None:
    """The proposal differs from the branch tip or the last push on record."""
    pushed = (record.landing or Landing()).pushed
    if pushed == proposed.tip == tip:
        return None
    slug = record.task.slug
    return Refusal(
        TIP,
        f"the task's branch is at {tip} and Lem pushed {pushed} last, not the "
        f"proposed {proposed.tip}",
        f"lem land next {slug} names the new round",
    )


def base_side(
    record: Record, world: World, checks_tree: str, *, approved: bool = False
) -> Refusal | None:
    """Why origin's base cannot take the merge: protection or missing evidence of this base."""
    branch = destination.recorded(record.landing) or world.rules.base
    guard = protected(branch, world.rules, "merges")
    if approved:
        return guard or merge_recheck.refusal(record, world)
    if guard is not None or world.base_tree == checks_tree:
        return guard
    read = mergeread.latest(record.landing or Landing(), world.base_tree)
    if read is not None and read.base_call == "safe":
        return None
    slug = record.task.slug
    return Refusal(
        "base",
        f"origin's {branch} moved after the checks ran, and no read of the merge agent "
        f"covers {branch} at {world.base} as safe: nothing was merged",
        f"lem land merge-review {slug} writes the brief of what moved; a fresh merge agent "
        "reads it, and on `Base: safe.` the merge goes on that base",
    )
