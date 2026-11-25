"""A task: what was asked, its shape, its status and hold, its work, its criteria, its
decisions and its questions (the design's part 3)."""

from typing import Literal

from lem.records.base import Day, Frozen, Moment, Slug
from lem.records.criteria import Criteria
from lem.records.decisions import Decision
from lem.records.holds import Hold
from lem.records.questions import Question
from lem.records.tickets import Ticket
from lem.records.work import Investigation, Plan, Span, StandIn, Talk

type Status = Literal[
    "queued",
    "shaping",
    "building",
    "planned",
    "ready",
    "landing",
    "open",
    "landed",
    "answered",
    "dropped",
]
type TaskType = Literal[
    "feat", "fix", "docs", "refactor", "perf", "test", "chore", "question"
]
type Track = Literal["small", "full"]
# What the shape hands on to: the interview, the fast track, the lead, an investigation.
type Then = Literal["interview", "fast", "lead", "investigation"]


class Shape(Frozen, frozen=True, kw_only=True):
    """The shape `task read` gave: the type and why, the track, the careful topics, what comes
    next, whether the words fit one open task, and whether someone else asked."""

    type: TaskType
    why: str
    track: Track
    careful: tuple[str, ...] = ()
    then: Then | None = None
    fits: bool = False
    someone_else: bool = False


class Task(Frozen, frozen=True, kw_only=True):
    """One task. `ask` is the owner's words, or the backlog item's path it started from
    (`backlog_item`); `after` and `order` queue it behind another task and by his words;
    `mode` says whether it runs with the owner or alone (a night task)."""

    slug: Slug
    ask: str
    opened: Moment
    status: Status
    since: Moment
    hold: Hold | None = None
    branch: str | None = None
    backlog_item: str | None = None
    resumed_from: Slug | None = None
    ticket: Ticket | None = None
    night: Day | None = None
    plan_only: bool = False
    after: Slug | None = None
    order: str | None = None
    mode: Literal["with-owner", "alone"] = "with-owner"
    shape: Shape | None = None
    lead: Literal["builder", "session", "small"] | None = None
    plan: Plan | None = None
    investigation: Investigation | None = None
    talk: Talk | None = None
    spans: tuple[Span, ...] = ()
    stand_ins: tuple[StandIn, ...] = ()
    criteria: Criteria = Criteria()
    decisions: tuple[Decision, ...] = ()
    questions: tuple[Question, ...] = ()
