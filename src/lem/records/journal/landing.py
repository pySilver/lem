"""The journal's entries of a landing (`landing.md` I): the review rounds, the careful call
missed, the reasons a pull request is not green, and the waits and end of the checks and the
merge, each written on a change, not on every look."""

from typing import Literal

from lem.records.base import Frozen, Moment, Sha, Slug, Tagged
from lem.records.landing.review import Reviewed


class ReviewRound(Tagged, tag="review-round", frozen=True, kw_only=True):
    """A review attempt was recorded."""

    at: Moment
    review: Reviewed


class CarefulMissed(Tagged, tag="careful-missed", frozen=True, kw_only=True):
    """A review of the fast track made the careful call the shape missed."""

    at: Moment
    round: int
    why: str


class NotGreen(Tagged, tag="not-green", frozen=True, kw_only=True):
    """`propose` found the pull request not green, for these reasons."""

    at: Moment
    tip: Sha
    reasons: tuple[str, ...]


class CheckWait(Tagged, tag="check-wait", frozen=True, kw_only=True):
    """The checks wait: for the load to fall under `start_below`, or behind another run, at a
    place in the line. Written on each change of reason or place."""

    at: Moment
    reason: Literal["load", "behind"]
    load: float | None = None
    start_below: float | None = None
    behind: Slug | None = None
    position: int | None = None


class CommandEnd(Frozen, frozen=True, kw_only=True):
    """One command's end in a check run: its name, whether it passed, its last line."""

    name: str
    passed: bool
    last: str


class CheckEnd(Tagged, tag="check-end", frozen=True, kw_only=True):
    """The checks ended: the outcome, the line for the owner, and each command."""

    at: Moment
    outcome: Literal["passed", "red", "refused", "stopped"]
    say: str
    commands: tuple[CommandEnd, ...] = ()


class MergeWait(Tagged, tag="merge-wait", frozen=True, kw_only=True):
    """The merge waits for another task's merge, which holds the merge lock."""

    at: Moment
    behind: Slug | None = None
