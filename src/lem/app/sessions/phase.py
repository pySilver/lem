"""The phase of a task's session, from its record: the shape with the owner, the build, the
landing, or the fast track, one session from the request to the merge.

The phase comes from the task, never from an argument. An owner's hold on the interview, the
criteria, the persona read, a fact or the order is the shape's, the fast track's criteria too; a
breaker's and a plan's are the build's. Then a task on the fast track is `fast`; a queued task
no lead started goes on in the shape; `queued`, `building` and `planned` are the build's;
`ready`, `landing` and `open` the landing's. A landed or dropped task whose worktree is still
there is in the landing, whose session cleans it up. A parked task, a task two releases back and
an ended one get no session, and are refused with the way on.
"""

from typing import TYPE_CHECKING, Literal

from lem.kernel.errors import Refusal
from lem.records.holds import BreakerHold, OwnerHold, Parked, ReleaseHold

if TYPE_CHECKING:
    from lem.records.task import Status, Task

type Phase = Literal["shape", "build", "land", "fast"]

SHAPE: Phase = "shape"
BUILD: Phase = "build"
LAND: Phase = "land"
# The status each phase takes when no hold decides it.
BY_STATUS: tuple[tuple[Status, Phase], ...] = (
    ("shaping", SHAPE),
    ("queued", BUILD),
    ("building", BUILD),
    ("planned", BUILD),
    ("ready", LAND),
    ("landing", LAND),
    ("open", LAND),
)
ENDED: tuple[Status, ...] = ("landed", "answered", "dropped")


def phase_of(task: Task, *, worktree: bool) -> Phase:
    """The phase of the task's session; refused for a task that gets no session."""
    refused(task, worktree=worktree)
    held = held_phase(task)
    if held is not None:
        return held
    if task.shape is not None and task.shape.track == "small":
        return "fast"
    if task.status in ENDED:
        return LAND
    if task.status == "queued" and task.lead is None:
        return SHAPE
    return dict(BY_STATUS)[task.status]


def phase_or_none(task: Task, *, worktree: bool) -> Phase | None:
    """The phase of the task's session; None for a task that gets none."""
    try:
        return phase_of(task, worktree=worktree)
    except Refusal:
        return None


def held_phase(task: Task) -> Phase | None:
    """The phase a hold gives: the owner's answer in the shape, a breaker or a plan in the
    build; None when no hold decides."""
    hold = task.hold
    if isinstance(hold, BreakerHold):
        return BUILD
    if isinstance(hold, OwnerHold):
        return BUILD if hold.on == "plan" else SHAPE
    return None


def refused(task: Task, *, worktree: bool) -> None:
    """Refuse a task that gets no session: parked, two releases back, or ended with no
    worktree left (a landed or dropped task's session cleans up its worktree)."""
    slug = task.slug
    if isinstance(task.hold, Parked):
        raise Refusal(
            "parked",
            f"the task {slug} is parked: it gets no session until the owner resumes it",
            f"lem task resume {slug} brings it back",
        )
    if isinstance(task.hold, ReleaseHold):
        raise Refusal("release", task.hold.say, f"lem task show {slug} says the way on")
    cleans = task.status in {"landed", "dropped"} and worktree
    if task.status in ENDED and not cleans:
        raise Refusal(
            "ended",
            f"the task {slug} is {task.status}: an ended task gets no session",
            "new work for it is a new ask, with a task of its own",
        )


def phase_noted(task: Task, status: str, hold: str | None) -> Phase | None:
    """The phase a state entry of the task's journal gave (its status and its hold's kind),
    with the task's track and lead as they are; None for an entry that gives no phase (a park,
    a release stop, an answered task), which a change of phase passes over."""
    if hold in {"parked", "release"} or status == "answered":
        return None
    return given_phase(task, status, hold) or by_status(status)


def by_status(status: str) -> Phase | None:
    """The phase a status gives when no hold, track or end decides it."""
    found = (phase for named, phase in BY_STATUS if named == status)
    return next(found, None)


def given_phase(task: Task, status: str, hold: str | None) -> Phase | None:
    """The phase a breaker's or the owner's hold, the fast track, an end or a queue of the
    shape gives, else None."""
    small = task.shape is not None and task.shape.track == "small"
    shaped = status == "queued" and task.lead is None
    given = (
        (hold == "breaker", BUILD),
        (hold == "owner", SHAPE),
        (small, "fast"),
        (status in ENDED, LAND),
        (shaped, SHAPE),
    )
    return next((phase for holds, phase in given if holds), None)
