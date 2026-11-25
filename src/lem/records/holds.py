"""What holds a task where it is, beside its status (the design's part 3, "a status and a
hold"): the owner's answer, a breaker, a block, his park, or a release two back."""

from typing import Literal

from lem.records.base import Moment, Slug, Tagged

# What the owner's answer is awaited on.
# `request` is the read of the request's one question (`stages/new.md` step 1).
type OwnerWait = Literal[
    "interview", "criteria", "skip-read", "fact", "step", "plan", "order", "request"
]


class OwnerHold(Tagged, tag="owner", frozen=True, kw_only=True):
    """The task waits for the owner's answer on `on`; `line` is what the stage says."""

    on: OwnerWait
    line: str
    since: Moment


class BreakerHold(Tagged, tag="breaker", frozen=True, kw_only=True):
    """Breaker `number` waits for his help, park or drop."""

    number: int
    since: Moment


class Blocked(Tagged, tag="blocked", frozen=True, kw_only=True):
    """A machine failure, a red base, no checks, a failed seat or a gone repair session: why,
    the fix that names the way on, and the task whose landing clears it."""

    why: str
    fix: str
    after: Slug | None = None
    seat: str | None = None
    since: Moment


class Parked(Tagged, tag="parked", frozen=True, kw_only=True):
    """His park: the status stays, and his resume clears it and gives back the hold the park
    put aside (`held`: a breaker that waited waits again)."""

    since: Moment
    words: str | None = None
    held: OwnerHold | BreakerHold | Blocked | None = None


class ReleaseHold(Tagged, tag="release", frozen=True, kw_only=True):
    """The task began on a release two back: a drop, then a resume, is the way on."""

    began: str
    running: str
    say: str
    since: Moment


type Hold = OwnerHold | BreakerHold | Blocked | Parked | ReleaseHold
