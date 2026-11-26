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
    """Whether the answered review found no defect in the resolution and called nothing careful."""
    return (
        review is not None
        and bool(review.answered)
        and not any(
            (
                review.counts.must_fix,
                review.counts.should,
                review.counts.nit,
            )
        )
        and review.careful is False
    )


def left_must_fix(landing: Landing) -> bool:
    """Whether the newest review of the change left a must-fix."""
    review = carry.newest(landing)
    return review is not None and bool(review.counts.must_fix)


def tip_carries(landing: Landing, world: World, *, careful: bool) -> bool:
    """Whether the tip proposed before carries onto the tip now through a builder's
    resolution: the conflict met that tip, the resolution is the tip now on the base it was
    made on, its one read was clean, the review before left no must-fix, and the request is
    not careful (`land.tip_carry` on `main`, `resolution`)."""
    resolution, proposed = landing.resolution, landing.proposed
    if careful or resolution is None or proposed is None:
        return False
    if resolution.before != proposed.tip or resolution.after != world.tip:
        return False
    if resolution.base != world.base:
        return False
    return clean(read_of(landing)) and not left_must_fix(landing)


def carries(landing: Landing, world: World, *, careful: bool) -> MergeRead | None:
    """The merge agent's read of the tip proposed before, carried onto the resolved tip, or
    None."""
    read = carry.latest(landing)
    if read is None or not tip_carries(landing, world, careful=careful):
        return None
    return carry.moved(read, world)
