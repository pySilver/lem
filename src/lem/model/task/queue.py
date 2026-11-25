"""The queue: whether a task may start now (`project.cmd_may_start` on `main`), and his "start
SLUG now".

A task queued after another (`Task.after`) starts when that one landed or was answered. When the
other was dropped, what it waited for never came, and it waits for the owner's word. A queue by
his order (`Task.order`) is lifted only by his word; a queue by a need that went is lifted by the
read of the request again, with no `--after`. No count of tasks stops a start: by day each start
is the owner's own request (the owner, 2026-11-18: "Why block him?").
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.records.holds import Parked

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.task import Status, Task

ENDED = frozenset(("landed", "dropped", "answered"))
LANDING = frozenset(("landing", "open"))
RUNNING = frozenset(("building", "landing"))
STARTED = frozenset(("landed", "answered"))


class May(Frozen, frozen=True, kw_only=True):
    """A task may start: the other tasks that load the machine now."""

    slug: str
    running: tuple[str, ...] = ()


def started_in(task: Task) -> Status:
    """Where his word takes a queued task: its interview comes next, or its work."""
    then = task.shape.then if task.shape else None
    return "shaping" if then in {None, "interview"} else "building"


def word(slug: str) -> str:
    """The command of the owner's "start SLUG now", with his words to put in."""
    return f'lem task start {slug} --words "HIS WORDS"'


def behind(task: Task, every: tuple[Record, ...]) -> Refusal | None:
    """Why a task queued after another may not start yet, or None."""
    after, slug = task.after, task.slug
    if after is None:
        return None
    found = (record.task.status for record in every if record.task.slug == after)
    status = next(found, "no task")
    if status in STARTED:
        return None
    if status == "dropped":
        return Refusal(
            "after-dropped",
            f"{slug} is queued after {after}, which was dropped, so the result it waited "
            f'for never came: it waits for the owner\'s word, "start {slug} now" or '
            f"/lem drop {slug}",
            f"on his word, {word(slug)}; on his drop, lem task move {slug} dropped",
        )
    lift = (
        f"when it no longer needs the result of {after}, lem task read {slug} again "
        "with no --after"
        if task.order is None
        else f"only his word removes his order: {word(slug)}"
    )
    return Refusal(
        "queued",
        f"{slug} is queued after {after}, which is {status}: it starts when {after} is "
        "landed or answered",
        lift,
    )


def start_refusal(task: Task, every: tuple[Record, ...]) -> Refusal | None:
    """Why `task` gets no lead now, or None."""
    slug, status = task.slug, task.status
    if status in ENDED:
        return Refusal(
            "ended",
            f"{slug} is {status}: an ended task gets no lead",
            "new work for it is a new ask (/lem new), with a slug of its own",
        )
    if isinstance(task.hold, Parked):
        return Refusal(
            "parked",
            f"{slug} is parked: it gets no lead until the owner brings it back",
            f"lem task resume {slug}, on his /lem resume {slug}",
        )
    if status in LANDING:
        return Refusal(
            "landing",
            f"{slug} is {status}: its build is done, and it gets no lead",
            f"its landing goes on: lem land next {slug} names the step; a change he asks "
            "for now is a new ask",
        )
    return behind(task, every)


def running(slug: str, every: tuple[Record, ...]) -> tuple[str, ...]:
    """The other tasks that load the machine now: a lead builds, or the checks run."""
    return tuple(
        found.task.slug
        for found in every
        if found.task.status in RUNNING and found.task.slug != slug
    )
