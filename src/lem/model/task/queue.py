"""The queue: whether a task may start now (`project.cmd_may_start` on `main`), and his "start
SLUG now".

A task queued after others (`Task.after`) starts when each of them landed or was answered. When
one was dropped, what it waited for never came, and it waits for the owner's word. A queue by
his order (`Task.order`) is lifted only by his word; a queue by a need that went is lifted by the
read of the request again, with no `--after`. No count of tasks stops a start: by day each start
is the owner's own request (the owner, 2026-11-18: "Why block him?").
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.task.behind import behind
from lem.records.base import Frozen
from lem.records.holds import Parked

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.task import Status, Task

ENDED = frozenset(("landed", "dropped", "answered"))
LANDING = frozenset(("landing", "open"))
RUNNING = frozenset(("building", "landing"))


class May(Frozen, frozen=True, kw_only=True):
    """A task may start: the other tasks that load the machine now."""

    slug: str
    running: tuple[str, ...] = ()


def started_in(task: Task) -> Status:
    """Where his word takes a queued task: its interview comes next, or its work."""
    then = task.shape.then if task.shape else None
    return "shaping" if then in {None, "interview"} else "building"


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
