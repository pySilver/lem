"""Whether a review covers the change as it is now (`landing.md` D, review coverage), and when
the request goes on without one (`land.due_of` on `main`).

A review covers the tip it read, and the commit `file` made after it with only the items of its
defects: `file` moves the checks there and names the items in `items_after`, after the review.
The carry over a clean rebase is `model/landing/carry.py`'s, which the step `land-base` builds.
"""

from typing import TYPE_CHECKING, get_args

from lem.model.landing import review_due, review_said
from lem.model.landing.world import Held

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.landing.record import Landing
    from lem.records.landing.review import Reviewed

KINDS: tuple[review_said.Kind, ...] = get_args(review_said.Kind.__value__)
# Why the review holds after two attempts in a row that no source answered: the request goes on
# as not reviewed, which the merge agent does not merge.
QUIET = "not reviewed: two attempts in a row, and no source answered"


def covers(review: Reviewed, landing: Landing, world: World) -> bool:
    """Whether the review covers the tip: the tip it read, or the commit `file` made after it
    with only the items of its defects."""
    if review.tip == world.tip:
        return True
    checked = landing.checked
    if checked is None or not checked.items_after:
        return False
    return checked.tip == world.tip and checked.at <= review.at


def too_small(
    review: Reviewed, landing: Landing, least: review_due.Floor
) -> str | None:
    """Why the review is less than the change gets at the least; the read of a resolution
    is sized by the round of the change before it."""
    sized = (review,)
    if review.of == "resolution":
        sized = review_due.rounds(landing)[-1:]
    floor = max(KINDS.index(least.kind), KINDS.index(review.floor))
    small = [one.kind for one in sized if KINDS.index(one.kind) < floor]
    if not small:
        return None
    return f"it was {small[0]}, and this change gets {KINDS[floor]} at the least"


def resolution_held(landing: Landing) -> Held | None:
    """The request goes on, not reviewed, after two silent reads of a resolution; None while
    the read is due."""
    if review_due.silent_run(landing) < review_due.SILENT_REVIEWS:
        return None
    return Held(why=f"{QUIET}: the read of a conflict's resolution")


def gone_on(landing: Landing, left: tuple[str, ...]) -> Held | None:
    """The request goes on to the owner, not green: two rounds were used, or two attempts in a
    row were silent. None while another review is due."""
    if len(review_due.rounds(landing)) >= review_due.ROUNDS:
        joined = ", and ".join(left)
        return Held(why=f"two rounds reviewed it: {joined}")
    if review_due.silent_run(landing) >= review_due.SILENT_REVIEWS:
        return Held(why=f"{QUIET}: the review of the change")
    return None
