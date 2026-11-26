"""Each confirmed proposal, kept for the retro after the next tip replaces it."""

from typing import Literal

from lem.records.base import Moment, Sha, Tagged
from lem.records.landing.propose import OwnerMerge


class ProposalNoted(Tagged, tag="proposed", frozen=True, kw_only=True):
    """What the owner saw at this tip."""

    at: Moment
    tip: Sha
    green: bool
    reasons: tuple[str, ...]
    review_carry: str | None = None
    merge_review: Literal["carried"] | None = None
    owner_merge: OwnerMerge | None = None
