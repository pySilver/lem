"""Whether a review covers the change as it is now (`landing.md` D, review coverage), and when
the request goes on without one (`land.due_of` on `main`).

A review covers the tip it read, the tip a clean rebase made of it (`model/landing/carry.py`),
and the commits that only add items `file` named in `items_after`, when Git proves their
history from the checked tip.
"""

from typing import TYPE_CHECKING, get_args

from msgspec.structs import replace

from lem.model.landing import carry, review_due, review_said
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
    """Whether the review covers the tip: the tip it read, the tip `base` showed by git's
    merge to be that tip on this base (`carry.source`), or the commit `file` made after it
    with only the items of its defects."""
    if review.tip in {world.tip, carry.source(landing, world)}:
        return True
    checked = landing.checked
    if checked is None or not world.items_from(checked.tip):
        return False
    if review.tip in world.item_chain:
        return True
    return review.tip == carry.source(landing, replace(world, tip=checked.tip))


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
