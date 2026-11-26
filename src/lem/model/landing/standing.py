"""The owner's merge refused for the base, over a new round (`landing.md` D, "Standing
merge"; `land.moved_carry` on `main`): it stands while it was his merge of the tip proposed
before, that tip carries onto the tip now and the reasons it was not green are the ones he
saw; else it ends, with why."""

from typing import TYPE_CHECKING

from lem.model.landing.rebased import why_unshown
from lem.records.landing.propose import OwnerMerge

if TYPE_CHECKING:
    from lem.records.landing.record import Landing


def rebased_from(landing: Landing) -> str | None:
    """The tip before a completed rebase or a builder's conflict resolution."""
    resolved, based = landing.resolution, landing.based
    if resolved is not None and resolved.before != resolved.after:
        return resolved.before
    if based is None or based.tip == based.before:
        return None
    return based.before


def pushed_before(landing: Landing) -> str | None:
    """The rebase began at a pushed tip which the previous proposal did not confirm: Lem's
    last push, or one before it that a cut proposal recorded."""
    before, proposed = rebased_from(landing), landing.proposed
    if before is None or proposed is None:
        return None
    if landing.pushed != before and before not in landing.unconfirmed:
        return None
    if before == proposed.tip:
        return None
    first, last = before[:9], proposed.tip[:9]
    return f"the rebase started from `{first}`, a tip pushed after the proposal of `{last}`"


def changed_after_rebase(landing: Landing, tip: str | None) -> str | None:
    """The proposal names another tip than the rebase left."""
    based = landing.based
    if tip is not None and based is not None and based.tip != tip:
        return "the tip changed after the rebase"
    return None


def standing(
    landing: Landing, digest: str, *, carried: bool, tip: str | None = None
) -> OwnerMerge | None:
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
            pushed_before(landing)
            or why_unshown(landing.based)
            or changed_after_rebase(landing, tip)
            or "the previous approval does not cover the change on the new base"
        )
        return OwnerMerge(state="ended", why=why)
    if kept.reasons_digest != digest:
        return OwnerMerge(state="ended", why="the reasons it is not green changed")
    return OwnerMerge(state="stands", why="the change and its reasons stay")
