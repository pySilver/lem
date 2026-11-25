"""A task's decisions, each taken by a level of the ladder without the owner or by him, a
criterion's change, and a breaker (`decisions.py` on `main`). The three share one sequence of
numbers."""

from typing import Literal

from lem.records.base import Frozen, Moment, Tagged, TaskPath

# The level of the ladder that took a decision.
type Level = Literal["lead", "gate", "personas", "dialectic", "experts", "owner", "lem"]


class Story(Frozen, frozen=True, kw_only=True):
    """What an important decision carries (one by the dialectic or the experts, or left
    unsettled): a case of two numbered steps or more, how the case was had, and the cause."""

    case: tuple[str, ...]
    case_was: Literal["reproduced", "derived"]
    cause: str


class Taken(Tagged, tag="taken", frozen=True, kw_only=True):
    """A decision: what was asked, what was chosen and why, by which level, and what each
    level and persona said."""

    id: int
    at: Moment
    what: str
    chose: str
    why: str
    by: Level
    said: str | None = None
    undo: str | None = None
    options: tuple[str, ...] = ()
    votes: tuple[tuple[str, str], ...] = ()
    levels: tuple[tuple[str, str], ...] = ()
    unsettled: bool = False
    chart: str | None = None
    words: str | None = None
    breaker: int | None = None
    advisers: tuple[str, ...] = ()
    story: Story | None = None


class CriterionChanged(Tagged, tag="criterion", frozen=True, kw_only=True):
    """A criterion changed, added or removed after an approval, by a decision or by the lead
    or the personas."""

    id: int
    at: Moment
    how: Literal["changed", "added", "removed"]
    criterion: int
    why: str
    approval: int
    was: str | None = None
    now: str | None = None
    decision: int | None = None
    by: Literal["lead", "personas"] | None = None
    said: str | None = None


class Breaker(Tagged, tag="breaker", frozen=True, kw_only=True):
    """The circuit breaker: why it tripped, its document, and the hand-over. It waits for the
    owner's help, park or drop; his help is a decision that names it."""

    id: int
    at: Moment
    cause: Literal["irreversible", "criteria"]
    what: str
    document: TaskPath
    handoff: TaskPath
    irreversible: Literal["data", "system", "person", "money"] | None = None


type Decision = Taken | CriterionChanged | Breaker
