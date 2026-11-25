"""The journal's entries of the merge (`landing.md` I): a merge read, a refusal, the merge,
and a new round, each with its evidence as the landing record holds it."""

from lem.records.base import Moment, Tagged
from lem.records.landing.merge import Merged, Refused
from lem.records.landing.propose import MergeRead


class ReadNoted(Tagged, tag="merge-read", frozen=True, kw_only=True):
    """The merge agent's read was recorded."""

    at: Moment
    read: MergeRead


class RefusalNoted(Tagged, tag="refused", frozen=True, kw_only=True):
    """A merge was refused."""

    at: Moment
    refusal: Refused


class MergeNoted(Tagged, tag="merged", frozen=True, kw_only=True):
    """The pull request was merged."""

    at: Moment
    merged: Merged


class LandAgain(Tagged, tag="land-again", frozen=True, kw_only=True):
    """A new round was admitted: the round, the count of rounds after the first, and whether a
    conflict on the forge brought it."""

    at: Moment
    round: int
    relands: int
    conflicting: bool = False
