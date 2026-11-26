"""What the new proposal keeps of the merge read and the owner's word."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.model.landing import (
    careful_words,
    carry,
    merge_recheck,
    merge_standing,
    resolution,
    review,
    standing,
)
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.landing.propose import MergeRead, Proposed
    from lem.records.record import Record


def repaired(record: Record, landing: Landing, world: World) -> bool:
    """A builder's repair after red checks needs an answered review of the repaired change."""
    if not merge_recheck.repair(landing):
        return False
    resolution, proposed = landing.resolution, landing.proposed
    if (
        resolution is not None
        and proposed is not None
        and resolution.before == proposed.tip
    ):
        return False
    return not review.unmet(record, review.newest(landing), world)


def carried_read(landing: Landing, world: World, *, conflict: bool) -> MergeRead | None:
    """The usable read over the resolution or the clean rebase."""
    if not conflict:
        return carry.read_carries(landing, world)
    prior = carry.latest(landing)
    return carry.moved(prior, world) if prior else None


def resolved(landing: Landing, world: World, proposed: Proposed) -> bool:
    """Apply the last whole-change careful call to conflict carry (`land.tip_carry`)."""
    careful = proposed.careful or bool(careful_words.review_reason(landing))
    return resolution.tip_carries(landing, world, careful=careful)


def judged(
    record: Record, world: World, proposed: Proposed
) -> tuple[Proposed, MergeRead | None]:
    """Compute both judgments before the new proposal replaces the old one."""
    landing = record.landing or Landing()
    resolved_carry = resolved(landing, world, proposed)
    read = carried_read(landing, world, conflict=resolved_carry)
    approval = standing.standing(
        landing,
        merge_standing.digest_of(proposed.reasons, proposed.contract),
        carried=resolved_carry
        or carry.proposed_carries(landing, world)
        or repaired(record, landing, world),
        tip=proposed.tip,
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
