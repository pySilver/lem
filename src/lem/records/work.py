"""The work of a task beside its landing: its spans, its plan, its investigation, its plan
talk, and a seat that another agent stood in for."""

from typing import Literal

from lem.records.base import Frozen, Moment, TaskPath

# A span's name: the lead, the fast track's one builder, a task of the plan, and the steps
# today's events marked (`builder.start`, `interview.start`, `scout.start`, ...).
type SpanName = Literal[
    "lead",
    "small",
    "task",
    "builder",
    "interview",
    "scout",
    "investigation",
    "plan-talk",
    "polish",
    "checks",
    "review",
]


class Span(Frozen, frozen=True, kw_only=True):
    """One stretch of work for the time card: its name, the job (`task 2 of 5`, the repair of
    a failed check), who did it, when it began, and when it ended, if it did."""

    name: SpanName
    job: str | None = None
    by: str | None = None
    start: Moment
    end: Moment | None = None


class Plan(Frozen, frozen=True, kw_only=True):
    """The plan file and what its writing said: its tasks, a careful topic, a large plan."""

    path: str
    tasks: int | None = None
    careful: str | None = None
    large: bool = False


class Investigation(Frozen, frozen=True, kw_only=True):
    """A bug's or a question's investigation: its kind, its typed result and call, the line
    for the owner, where it looked, and whether it reproduced the bug."""

    kind: Literal["fix", "question"]
    found: Literal["bug", "none", "question", "unreproduced"] | None = None
    call: Literal["small", "full", "not-a-bug", "not-reproduced", "answer"] | None = (
        None
    )
    line: str | None = None
    where: str | None = None
    reproduced: bool | None = None
    report: TaskPath | None = None
    at: Moment | None = None


class Talk(Frozen, frozen=True, kw_only=True):
    """The plan talk's counts, which the pull request shows (`project.talk_form` on `main`)."""

    reviewer: str
    turns: int
    questions: int
    settled: int
    open: int
    repaired: int
    design: int
    unargued: int
    root: int
    layer: int
    shared: int
    at: Moment


class StandIn(Frozen, frozen=True, kw_only=True):
    """A seat whose agent failed, and the fallback that stood in, until the owner's go on."""

    seat: Literal["reviewer", "planner", "merger"]
    failed: str
    error: Literal["missing", "login", "tokens", "model"]
    said: str | None = None
    took: str | None = None
    at: Moment
    again: Moment | None = None
