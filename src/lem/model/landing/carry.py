"""Carry and coverage over a rebase (`landing.md` D), computed from facts: git's merge of the
reviewed tip onto the new base against the new tree, never from a record of the rebase.

A review carries over a rebase only where that merge is clean and is the new tip's tree, the
same tree id, so the same content and modes; matching patch ids are not enough. A must-fix the
review left stays open through any carry. A merge read carries over a clean rebase with its real
verdict, and over a conflict only where one read of the resolution found nothing.
"""

from typing import TYPE_CHECKING

from lem.model.landing.rebased import why_unshown
from lem.records.landing.propose import MergeRead, OwnerMerge

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.base import Sha
    from lem.records.landing.record import Landing
    from lem.records.landing.review import Reviewed


def newest(landing: Landing) -> Reviewed | None:
    """The newest review of the change that some reviewer answered."""
    answered = [one for one in landing.reviews if one.answered and one.of == "change"]
    return answered[-1] if answered else None


def covers(landing: Landing, tip: Sha | None) -> bool:
    """Whether the newest answered review covers the change at `tip`: it read this tip, or
    `base` put the tip it read onto the base by a rebase git's merge shows."""
    review, based = newest(landing), landing.based
    if review is None or tip is None:
        return False
    if review.tip == tip:
        return True
    return (
        based is not None
        and based.carried
        and based.tip == tip
        and based.before == review.tip
    )


def read_carries(landing: Landing, world: World) -> MergeRead | None:
    """The merge agent's read carried onto the tip a clean rebase made: a real verdict (not an
    unusable answer) of the tip the rebase started from, a rebase whose merge git shows, and no
    commit after it; else None."""
    based = landing.based
    reads = [read for read in landing.reads if read.verdict and not read.no_answer]
    if based is None or not reads or not based.carried:
        return None
    if based.tip != world.tip:
        return None
    read = reads[-1]
    if read.tip != based.before or based.base != world.base:
        return None
    return MergeRead(
        tip=based.tip,
        base=world.base,
        base_tree=world.base_tree,
        verdict=read.verdict,
        why=read.why,
        carried_from=read.tip,
        at=world.now,
    )


def standing(landing: Landing, digest: str, *, covered: bool) -> OwnerMerge | None:
    """The owner's merge refused for the base: it stands while the review covers the change
    and the reasons it was not green are the same; else it ended, with why."""
    kept = landing.standing
    if kept is None:
        return None
    if not covered:
        why = (
            why_unshown(landing.based) or "no review covers the change on the new base"
        )
        return OwnerMerge(state="ended", why=why)
    if kept.reasons_digest != digest:
        return OwnerMerge(state="ended", why="the reasons it is not green changed")
    return OwnerMerge(state="stands", why="the change and its reasons stay")
