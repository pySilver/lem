"""The record a review agent writes, `reviews/review-N.json`, in the form step 8 of
`prompts/review.md` gives it, read strictly: a key the prompt does not name, a count under 0, a
kind or a call by the bar it does not list, or a name with no why is refused by the decoder,
which names the key (`land.cmd_read` and `land.defects_of` on `main`).

The record counts the change's findings (`must_fix`, `should`, `nit`) and lists the defects the
review saw outside the change (`outside`). The counts go in the review's record. Each defect
outside the change gets a finding `rA.N`, which `file` places.
"""

from typing import Annotated, Literal

import msgspec

from lem.records.base import Frozen
from lem.records.landing import review as records
from lem.records.landing.review import BarPlace

type Kind = Literal["read", "round", "full"]
# A text of one line with a word in it; a run (`what`) may hold several lines.
type Line = Annotated[str, msgspec.Meta(pattern=r"^[^\n]*\S[^\n]*$")]
type Text = Annotated[str, msgspec.Meta(pattern=r"\S")]
type Count = Annotated[int, msgspec.Meta(ge=0)]


class Named(Frozen, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """A profile of the round, or a source that did not answer, with why."""

    name: Line
    why: Line


class Outside(Frozen, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """A defect the base commit has too: where, its title, the run that shows it, the
    review's call by the bar, why, and the item of the base that holds it."""

    where: Line
    title: Line
    what: Text
    against: BarPlace = msgspec.field(name="bar")
    why: Line | None = None
    open: str | None = None


class Said(Frozen, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """`review-N.json` as the review agent writes it. `outside` is a list; 0 says none, as
    `main` took it."""

    attempt: int
    tip: str
    kind: Kind
    answered: tuple[Line, ...]
    ran: tuple[Named, ...] = ()
    left_out: tuple[Named, ...] = ()
    silent: tuple[Named, ...] = ()
    lowered: tuple[Named, ...] = msgspec.field(default=(), name="bar")
    must_fix: Count = 0
    should: Count = 0
    nit: Count = 0
    outside: tuple[Outside, ...] | Literal[0] = ()
    careful: bool | None = None
    careful_why: Line | None = None


def kept(entries: tuple[Named, ...]) -> tuple[records.Named, ...]:
    """Names with their why, as the task's record keeps them."""
    made = records.Named
    return tuple(made(name=one.name, why=one.why) for one in entries)


def defects(said: Said) -> tuple[Outside, ...]:
    """The defects outside the change; 0 is none."""
    return () if said.outside == 0 else said.outside


def counts(said: Said) -> records.Counts:
    """The change's findings by level, and the number of defects outside it."""
    return records.Counts(
        must_fix=said.must_fix,
        should=said.should,
        nit=said.nit,
        outside=len(defects(said)),
    )
