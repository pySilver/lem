"""The merge agent's read carried over a conflict with the base (`landing.md` D, "Merge read
carry, conflict"; `stages/conflict.md`): the read before had a real verdict, and the one read
of the builder's resolution found nothing, was answered and called nothing careful, with no
commit after the resolution, on the base it was made on, and no must-fix left by the review
before it. A careful request never carries over a resolved conflict."""

from typing import TYPE_CHECKING

from lem.model.landing import carry

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.landing.propose import MergeRead
    from lem.records.landing.record import Landing
    from lem.records.landing.review import Reviewed


def read_of(landing: Landing) -> Reviewed | None:
    """The review that read the resolution, when one did."""
    resolution = landing.resolution
    if resolution is None or resolution.read is None:
        return None
    found = (
        review
        for review in landing.reviews
        if review.attempt == resolution.read and review.of == "resolution"
    )
    return next(found, None)


def clean(review: Reviewed | None) -> bool:
    """Whether a review was answered, found nothing and called nothing careful."""
    return (
        review is not None
        and bool(review.answered)
        and not review.findings
        and review.careful is False
    )


def left_must_fix(landing: Landing) -> bool:
    """Whether the newest review of the change left a must-fix."""
    review = carry.newest(landing)
    return review is not None and any(
        finding.level == "must-fix" for finding in review.findings
    )


def carries(landing: Landing, world: World, *, careful: bool) -> MergeRead | None:
    """The read before carried onto the resolved tip, or None."""
    resolution, reads = landing.resolution, carry.real(landing)
    if careful or resolution is None or not reads:
        return None
    if resolution.after != world.tip or resolution.base != world.base:
        return None
    if not clean(read_of(landing)) or left_must_fix(landing):
        return None
    return carry.moved(reads[-1], world)
