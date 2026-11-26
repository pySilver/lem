"""The journal's entries of a task's life outside the landing: a span's mark, a state, a
decision, an act of the owner, and the summary that retention folds an old journal into.

The journal is what views render and what the Activity chart, the Timeline and the retro read;
no rule reads it (the design's part 3).
"""

from typing import Literal

from lem.records.approvals import ApprovedBy, Size
from lem.records.base import Frozen, Moment, Sha, Tagged
from lem.records.work import SpanName


class SpanMark(Tagged, tag="span", frozen=True, kw_only=True):
    """A span began or ended, as `Task.spans` holds it, for the Timeline."""

    at: Moment
    name: SpanName
    edge: Literal["start", "end"]
    job: str | None = None
    by: str | None = None
    carried_from: str | None = None


class StateNoted(Tagged, tag="state", frozen=True, kw_only=True):
    """A move of the task: its new status, the hold's kind, and the stage's line."""

    at: Moment
    status: str
    hold: str | None = None
    line: str | None = None
    opening: str | None = None
    branch: str | None = None
    head: Sha | None = None
    subject: str | None = None


class DecisionNoted(Tagged, tag="decision", frozen=True, kw_only=True):
    """A decision, a criterion's change or a breaker was recorded, by its id."""

    at: Moment
    id: int
    what: str
    carried_from: str | None = None


class OwnerAct(Tagged, tag="owner-act", frozen=True, kw_only=True):
    """An act of the owner on the board or in a card: the act, the question it answered, the
    option, and from where."""

    at: Moment
    act: str
    question: str | None = None
    option: str | None = None
    via: Literal["local", "door", "session"] | None = None


class Total(Frozen, frozen=True, kw_only=True):
    """The seconds of one name of span or wait, over the folded journal."""

    name: str
    seconds: int


class Summary(Tagged, tag="summary", frozen=True, kw_only=True):
    """What retention keeps of a folded journal (`project.summary_of` on `main`): the run of
    statuses, the last state with its line (why a task ended), the first and last moments, the
    pull request, the proposal, the plan talk, and the totals of spans and waits. The task's own
    fields (type, track, lead, careful, investigation, night) stay on the task."""

    at: Moment
    statuses: tuple[str, ...]
    last_state: StateNoted | None = None
    first: Moment
    last: Moment
    entries: int
    pull: int | None = None
    green: bool | None = None
    reasons: tuple[str, ...] = ()
    talked: bool = False
    spans: tuple[Total, ...] = ()
    waits: tuple[Total, ...] = ()


class CriteriaNoted(Tagged, tag="criteria", frozen=True, kw_only=True):
    """The action and its counts as they stood when it took place."""

    at: Moment
    event: Literal[
        "read-start", "read-done", "approved", "recorded", "skip-asked", "skip-yes"
    ]
    by: ApprovedBy | Literal["lead"] | None = None
    number: int | None = None
    size: Size | None = None
    asked: int | None = None
    answered: int | None = None
    flagged: int | None = None
    split: bool = False
    carried_from: str | None = None
