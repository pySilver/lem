"""What a merge checks against the world read again under the merge lock (`landing.md` H 1, 2
and 4; `main:land.merge_locked`): the pull request as proposed and into the task's base, the
local tip, the checks of that tip, and origin's base, unmoved since the checks by its tree or
covered by a safe read.

The forge pins only the head; everything else is read again here, before the intent is
written. `checks` is the tree of the base the checks ran on, which the app reads from git.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import checks, mergeread
from lem.model.landing.invariants import protected
from lem.model.landing.world import Due, World
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.landing.propose import Proposed
    from lem.records.record import Record

TIP = "tip"


def forge_side(record: Record, world: World, proposed: Proposed) -> Refusal | None:
    """Why the pull request is not the one proposed: none, not open, retargeted before the
    merge, or at another head."""
    slug, pull, base = record.task.slug, world.pull, world.rules.base
    if pull is None:
        return Refusal(
            "no-pull", f"{slug} has no pull request", f"lem land next {slug}"
        )
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
            "base of the task's settings: its base was changed there; nothing was merged",
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


def our_side(record: Record, world: World, proposed: Proposed) -> Refusal | None:
    """Why the proposal is not what the checks covered: a local tip that moved, or no passed
    run of the checks of that tip as they are now."""
    if world.tip != proposed.tip:
        slug = record.task.slug
        return Refusal(
            TIP,
            f"the task's branch is at {world.tip}, not the proposed {proposed.tip}",
            f"lem land next {slug} names the new round",
        )
    return covered(record, world, proposed.tip)


def base_side(record: Record, world: World, checks_tree: str) -> Refusal | None:
    """Why origin's base may not take the merge: protected, or moved since the checks (by its
    tree) with no safe read of the merge agent that covers it now."""
    guard = protected(world.rules.base, world.rules, "merges")
    if guard is not None or world.base_tree == checks_tree:
        return guard
    read = mergeread.latest(record.landing or Landing(), world.base_tree)
    if read is not None and read.base_call == "safe":
        return None
    slug, branch = record.task.slug, world.rules.base
    return Refusal(
        "base",
        f"origin's {branch} moved after the checks ran, and no read of the merge agent "
        f"covers {branch} at {world.base} as safe: nothing was merged",
        f"lem land merge-review {slug} writes the brief of what moved; a fresh merge agent "
        "reads it, and on `Base: safe.` the merge goes on that base",
    )
