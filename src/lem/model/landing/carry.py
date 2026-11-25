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


def source(landing: Landing, world: World) -> Sha | None:
    """The tip whose review carried onto the tip now: the newest answered review, which `base`
    judged by git's merge of its tip onto this base, when that merge was the tip's tree and no
    commit came after. None when no review carried."""
    review, based = newest(landing), landing.based
    if review is None or based is None or not based.carried:
        return None
    if based.tip != world.tip or based.base != world.base:
        return None
    return review.tip if review.at <= based.at else None


def covers(landing: Landing, world: World) -> bool:
    """Whether the newest answered review covers the change at the tip now: it read this tip,
    or `base` showed that the tip it read is this tip on this base."""
    review = newest(landing)
    if review is None or world.tip is None:
        return False
    return review.tip == world.tip or source(landing, world) is not None


def real(landing: Landing) -> list[MergeRead]:
    """The merge agent's reads with a real verdict, not an unusable answer, in their order."""
    return [read for read in landing.reads if read.verdict and not read.no_answer]


def read_carries(landing: Landing, world: World) -> MergeRead | None:
    """The merge agent's read carried onto the tip a clean rebase made: a real verdict of the
    tip whose review carried; else None."""
    reads, carried = real(landing), source(landing, world)
    if not reads or carried is None or reads[-1].tip != carried:
        return None
    return moved(reads[-1], world)


def moved(read: MergeRead, world: World) -> MergeRead:
    """The read `read` carried onto the tip and base now."""
    return MergeRead(
        tip=world.tip or read.tip,
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
