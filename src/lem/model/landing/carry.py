"""Carry and coverage over a rebase (`landing.md` D), computed from facts: git's merge of the
reviewed tip onto the new base against the new tree, never from a record of the rebase.

A review carries over a rebase only where that merge is clean and is the new tip's tree, the
same tree id, so the same content and modes; matching patch ids are not enough. A must-fix the
review left stays open through any carry. A merge read carries over a clean rebase with its real
verdict, and over a conflict only where one read of the resolution found nothing.
"""

from typing import TYPE_CHECKING

from lem.records.landing.propose import MergeRead

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.base import Sha
    from lem.records.landing.propose import Proposed
    from lem.records.landing.record import Landing
    from lem.records.landing.review import Reviewed


def newest(landing: Landing) -> Reviewed | None:
    """The newest review of the change that some reviewer answered."""
    answered = [one for one in landing.reviews if one.answered and one.of == "change"]
    return answered[-1] if answered else None


def source(landing: Landing, target: World | Proposed) -> Sha | None:
    """The tip whose review carried onto the tip now: the newest answered review, which `base`
    judged by git's merge of its tip onto this base, when that merge was the tip's tree and no
    commit came after. Older records without the reviewed tip need a review that predates
    the rebase. None when no review carried."""
    review, based = newest(landing), landing.based
    if review is None or based is None or not based.carried:
        return None
    if based.tip != target.tip or based.base != target.base:
        return None
    reviewed = based.reviewed
    if reviewed is None:
        return review.tip if review.at < based.at else None
    return review.tip if reviewed == review.tip else None


def covers(landing: Landing, world: World) -> bool:
    """Whether the newest answered review covers the change at the tip now: it read this tip,
    or `base` showed that the tip it read is this tip on this base."""
    review = newest(landing)
    if review is None or world.tip is None:
        return False
    return review.tip == world.tip or source(landing, world) is not None


def proposed_carries(landing: Landing, world: World) -> bool:
    """Whether the tip proposed before is the change now: the same tip on the same base, or the
    tip whose review a rebase git showed carried onto the tip now (`land.tip_carry` on
    `main`, `same` and `rebase`)."""
    proposed = landing.proposed
    if proposed is None:
        return False
    if proposed.tip == world.tip:
        return proposed.base == world.base
    reviewed = source(landing, world)
    if reviewed is None:
        return False
    based = landing.based
    from_proposal = based is not None and based.before == proposed.tip
    return reviewed == proposed.tip or from_proposal


def latest(landing: Landing) -> MergeRead | None:
    """The merge agent's newest read of the tip proposed before, when it gave a real verdict;
    None after an unusable answer, which an older verdict never stands in for."""
    proposed = landing.proposed
    reads = [read for read in landing.reads if proposed and read.tip == proposed.tip]
    if not reads:
        return None
    last = reads[-1]
    return None if last.verdict is None or last.no_answer else last


def read_carries(landing: Landing, world: World) -> MergeRead | None:
    """The merge agent's read of the tip proposed before, carried onto the tip a clean rebase
    made; else None."""
    proposed, read = landing.proposed, latest(landing)
    if proposed is None or read is None or proposed.tip == world.tip:
        return None
    return moved(read, world) if proposed_carries(landing, world) else None


def moved(read: MergeRead, world: World) -> MergeRead:
    """The read `read` carried onto the tip and base now."""
    return MergeRead(
        tip=world.tip or read.tip,
        base=world.base,
        base_tree=world.base_tree,
        verdict=read.verdict,
        why=read.why,
        by=read.by,
        brief=read.brief,
        carried_from=read.tip,
        at=world.now,
    )
