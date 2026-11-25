"""The record a review agent writes, in the form `prompts/review.md` gives it ("The record of a
review" of `lem land --help` on `main`), read strictly: a key it does not name is refused.

The record counts the change's findings (`must_fix`, `should`, `nit`) and lists the defects the
review saw outside the change (`outside`). The task's record keeps each as a finding: the counts
as findings `rA.cN` that only count, the defects outside as `rA.N`, which `file` places. A
lowered bar's answer and an item of the base that holds a defect are the steps `land-checks`'
and `land-review`'s.
"""

from typing import Literal

import msgspec

from lem.kernel.errors import Refusal
from lem.model.landing.world import World, later
from lem.records.base import Frozen, Sha
from lem.records.landing.review import BarPlace, Finding, Named

type Kind = Literal["read", "round", "full"]
type Level = Literal["must-fix", "should", "nit"]
# The mark of a finding that only counts one of the change's findings by its level.
COUNTED = "c"


class Outside(Frozen, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """A defect the base commit has too: where, its title, the run that shows it, the
    review's call by the bar, why, and the item of the base that holds it."""

    where: str
    title: str
    what: str
    against: BarPlace = msgspec.field(name="bar")
    why: str | None = None
    open: str | None = None


class Said(Frozen, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """`review-N.json` as the review agent writes it."""

    attempt: int
    tip: Sha
    kind: Kind
    ran: tuple[Named, ...] = ()
    left_out: tuple[Named, ...] = ()
    answered: tuple[str, ...] = ()
    silent: tuple[Named, ...] = ()
    lowered: tuple[Named, ...] = msgspec.field(default=(), name="bar")
    must_fix: int = 0
    should: int = 0
    nit: int = 0
    outside: tuple[Outside, ...] = ()
    careful: bool | None = None
    careful_why: str | None = None


def levels_of(said: Said) -> list[Level]:
    """The level of each of the change's findings, as many of each as the record counts."""
    counts: tuple[tuple[Level, int], ...] = (
        ("must-fix", said.must_fix),
        ("should", said.should),
        ("nit", said.nit),
    )
    return [level for level, count in counts for _ in range(count)]


def counted(said: Said) -> tuple[Finding, ...]:
    """The change's findings, each a finding that only counts its level."""
    review = f"review-{said.attempt}.md"
    return tuple(
        Finding(
            id=f"r{said.attempt}.{COUNTED}{place}",
            level=level,
            where=review,
            title=f"a {level} of the change",
            what=f"{review} names it",
            against="over",
        )
        for place, level in enumerate(levels_of(said), 1)
    )


def outside_of(said: Said) -> tuple[Finding, ...]:
    """The defects outside the change, each numbered by the attempt and its place."""
    return tuple(
        Finding(
            id=f"r{said.attempt}.{place}",
            level="nit",
            where=found.where,
            title=found.title,
            what=found.what,
            against=found.against,
            why=found.why,
            open=found.open,
        )
        for place, found in enumerate(said.outside, 1)
    )


def of_form(said: Said, attempt: int, world: World) -> Refusal | None:
    """Why the record is not one of the attempt that is due, for the tip now."""
    if said.attempt != attempt:
        return Refusal(
            "attempt",
            f"the record is of attempt {said.attempt}, and the attempt due is {attempt}",
            "the review writes the attempt that lem land read printed",
        )
    if said.tip != world.tip:
        return Refusal(
            "tip",
            f"the record is of {said.tip}, and the branch's tip is {world.tip} now",
            "lem land read SLUG prints the tip the review reads; review that tip",
        )
    if said.lowered:
        return later("the review's answer on a lowered bar", "land-checks")
    if any(found.open for found in said.outside):
        return later(
            "a defect outside the change that an item of the base holds", "land-review"
        )
    return None
