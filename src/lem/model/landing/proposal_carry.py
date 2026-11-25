"""What the new proposal keeps of the merge read and the owner's word."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.model.landing import carry, merge_recheck, merge_standing, review, standing
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.landing.propose import MergeRead, Proposed
    from lem.records.record import Record


def repaired(record: Record, landing: Landing, world: World) -> bool:
    """A builder's repair after red checks needs an answered review of the repaired change."""
    if not merge_recheck.repair(landing):
        return False
    return not review.unmet(record, review.newest(landing), world)


def resolved(landing: Landing, world: World) -> bool:
    """A resolution carries the proposal only after one answered, clean, non-careful read."""
    resolution, proposed = landing.resolution, landing.proposed
    if resolution is None or proposed is None or not landing.reviews:
        return False
    if (resolution.before, resolution.after, resolution.base) != (
        proposed.tip,
        world.tip,
        world.base,
    ):
        return False
    last = landing.reviews[-1]
    if (last.attempt, last.tip, last.of) != (
        resolution.read,
        resolution.after,
        "resolution",
    ):
        return False
    return (
        bool(last.answered)
        and not last.findings
        and last.careful is False
        and prior_clear(landing, resolution.before)
    )


def prior_clear(landing: Landing, before: str) -> bool:
    """The review of the prior tip left no must-fix open."""
    prior = carry.newest(landing)
    return (
        prior is not None
        and prior.tip == before
        and not any(finding.level == "must-fix" for finding in prior.findings)
    )


def carried_read(landing: Landing, world: World, *, conflict: bool) -> MergeRead | None:
    """The usable read over the resolution or the clean rebase."""
    if not conflict:
        return carry.read_carries(landing, world)
    prior = carry.latest(landing)
    return carry.moved(prior, world) if prior else None


def judged(
    record: Record, world: World, proposed: Proposed
) -> tuple[Proposed, MergeRead | None]:
    """Compute both judgments before the new proposal replaces the old one."""
    landing = record.landing or Landing()
    resolved_carry = not proposed.careful and resolved(landing, world)
    read = carried_read(landing, world, conflict=resolved_carry)
    approval = standing.standing(
        landing,
        merge_standing.digest_of(proposed.reasons, proposed.contract),
        carried=resolved_carry
        or carry.proposed_carries(landing, world)
        or repaired(record, landing, world),
    )
    why = (
        "The merge review carries after the read of the resolution."
        if resolved_carry
        else "The merge review carries over the clean rebase."
    )
    return (
        replace(
            proposed,
            merge_review="carried" if read else None,
            merge_review_why=why if read else None,
            owner_merge=approval,
        ),
        read,
    )
