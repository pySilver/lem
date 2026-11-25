"""The owner's merge refused for the base, over a new round (`landing.md` D, "Standing
merge"; `land.moved_carry` on `main`): it stands while it was his merge of the tip proposed
before, that tip carries onto the tip now and the reasons it was not green are the ones he
saw; else it ends, with why."""

from typing import TYPE_CHECKING

from lem.model.landing.rebased import why_unshown
from lem.records.landing.propose import OwnerMerge

if TYPE_CHECKING:
    from lem.records.landing.record import Landing


def standing(landing: Landing, digest: str, *, carried: bool) -> OwnerMerge | None:
    """The owner's merge refused for the base: it stands while it was his merge of the tip
    proposed before, that tip carries onto the tip now (`carried`: `proposed_carries`, or a
    resolution's carry) and the reasons it was not green are the same; else it ended, with
    why."""
    kept, proposed = landing.standing, landing.proposed
    if kept is None:
        return None
    if proposed is None or kept.tip != proposed.tip:
        return OwnerMerge(
            state="ended", why="the change is not the one the owner merged"
        )
    if not carried:
        why = (
            why_unshown(landing.based) or "no review covers the change on the new base"
        )
        return OwnerMerge(state="ended", why=why)
    if kept.reasons_digest != digest:
        return OwnerMerge(state="ended", why="the reasons it is not green changed")
    return OwnerMerge(state="stands", why="the change and its reasons stay")
