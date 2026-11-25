"""What a merge checks against the world read again under the merge lock (`landing.md` H 1, 2 and
4; `main:land.merge_locked`): the pull request as proposed, the local tip, the checks of that
tip, origin's base, and the base not protected.

The forge pins only the head; everything else is read again here, before the intent is written.
A base that moved after the checks with no safe read is refused; the safe read itself is the
step `land-merge`'s.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import checks
from lem.model.landing.invariants import protected
from lem.model.landing.world import World, later
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.landing.propose import Proposed
    from lem.records.record import Record

TIP = "tip"


def forge_side(record: Record, world: World, proposed: Proposed) -> Refusal | None:
    """Why the pull request is not the one proposed: none, another target, another head."""
    slug, pull = record.task.slug, world.pull
    if pull is None:
        return Refusal(
            "no-pull", f"{slug} has no pull request", f"lem land next {slug}"
        )
    if pull.base != world.rules.base:
        return later(
            f"the merge of a pull request retargeted to {pull.base}", "land-merge"
        )
    if pull.head != proposed.tip:
        return Refusal(
            TIP,
            f"the pull request's head is {pull.head}, not the proposed {proposed.tip}",
            f"lem land next {slug} names the new round",
        )
    return None


def our_side(record: Record, world: World, proposed: Proposed) -> Refusal | None:
    """Why the proposal is not what the checks covered: a local tip that moved, checks of
    another tip or that did not pass, or commands that changed since they ran."""
    slug = record.task.slug
    checked = (record.landing or Landing()).checked
    if world.tip != proposed.tip:
        return Refusal(
            TIP,
            f"the task's branch is at {world.tip}, not the proposed {proposed.tip}",
            f"lem land next {slug} names the new round",
        )
    if checked is None or checked.tip != proposed.tip or checked.outcome != "passed":
        return Refusal(
            "checks-changed",
            f"no passed run of the checks covers {proposed.tip}",
            f"lem land next {slug}",
        )
    if checked.inputs != checks.inputs(world.rules):
        return Refusal(
            "checks-changed",
            "the checks' commands changed since they ran",
            f"lem land start {slug} begins a round that runs them",
        )
    return None


def base_side(record: Record, world: World) -> Refusal | None:
    """Why origin's base may not take the merge: protected, or moved since the checks."""
    guard = protected(world.rules.base, world.rules, "merges")
    if guard is not None:
        return guard
    checked = (record.landing or Landing()).checked
    if checked is None or checked.base == world.base:
        return None
    branch, ran = world.rules.base, checked.base
    slug = record.task.slug
    return Refusal(
        "base",
        f"origin's {branch} moved after the checks ran on {ran}",
        f"lem land next {slug}: a read of the moved base comes first",
    )


def stale(record: Record, world: World, proposed: Proposed) -> Refusal | None:
    """The first reason the merge may not go to the forge with the world as it is now."""
    return (
        base_side(record, world)
        or forge_side(record, world, proposed)
        or our_side(record, world, proposed)
    )
