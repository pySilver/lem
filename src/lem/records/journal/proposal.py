"""Each confirmed proposal, kept for the retro after the next tip replaces it."""

from lem.records.base import Moment, Sha, Tagged


class ProposalNoted(Tagged, tag="proposed", frozen=True, kw_only=True):
    """What the owner saw at this tip."""

    at: Moment
    tip: Sha
    green: bool
    reasons: tuple[str, ...]
