"""The table of statuses (the design's part 3): where `lem task move` may take a task, and why
it may not.

The landing's own statuses (`landing`, `open`, `landed`) are entered by `lem land` alone. A
task with its landing takes no lead's state (a lead that woke late), but for `ready` with a
start over, which only the landing's refusal names, `shaping` (the owner's standard track) and
the drop. An ended task stays ended. A parked task leaves its park by a resume or a drop, and a
seat's block by the owner's go on (`lem seat again`) or a drop.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.records.holds import Blocked, Parked

if TYPE_CHECKING:
    from lem.records.task import Status, Task

ENDED = frozenset(("landed", "dropped", "answered"))
LANDING = frozenset(("landing", "open"))
BY_LAND = frozenset(("landing", "open", "landed"))
DROPPED = "dropped"
READY = "ready"
MOVE = "move"
# Where each status may go by `lem task move`, a drop included.
MOVES = MappingProxyType(
    {
        "queued": "shaping building dropped",
        "shaping": "building answered queued dropped",
        "building": "queued planned ready shaping answered dropped",
        "planned": "building dropped",
        "ready": "building dropped",
        "landing": "ready shaping dropped",
        "open": "ready dropped",
    }
)
WAKE = "a reply or a message about it that comes now is a stale wake-up: nothing is written"


def held_refusal(task: Task, status: Status) -> Refusal | None:
    """Why the task's hold refuses `status`: a park, or a seat that failed."""
    hold, slug = task.hold, task.slug
    if isinstance(hold, Parked) and status != DROPPED:
        return Refusal(
            "parked",
            f"{slug} is parked: the owner put it aside, and {WAKE}",
            f"lem task resume {slug} brings it back on his word; a drop ends it",
        )
    if isinstance(hold, Blocked) and hold.seat and status != DROPPED:
        return Refusal(
            "seat-blocked",
            f"{slug} is blocked: the seat {hold.seat} failed, and only the owner's go on "
            "lifts that block",
            f"lem seat again {slug} on his word; a drop ends it",
        )
    return None


def landing_refusal(
    task: Task, status: Status, start_over: str | None
) -> Refusal | None:
    """Why a move of a task with its landing, or into it, is refused."""
    slug, now = task.slug, task.status
    if status in BY_LAND:
        return Refusal(
            MOVE,
            f"{status} is a status of the landing, which lem land moves itself",
            f"lem land next {slug} names the landing's step",
        )
    if start_over is not None and (status != READY or now not in LANDING):
        return Refusal(
            "start-over",
            f"--start-over gives a task with its landing back to ready; {slug} is {now}",
            f"lem task move {slug} {status}, with no --start-over",
        )
    if now in LANDING and status == READY and start_over is None:
        return Refusal(
            MOVE,
            f"{slug} is {now}: it is with its landing, and {WAKE}",
            "what the landing needs, lem land next says; --start-over WHY only where its "
            "refusal names it",
        )
    return None


def refusal(task: Task, status: Status, start_over: str | None) -> Refusal | None:
    """Why `lem task move` may not take `task` to `status`, or None."""
    slug, now = task.slug, task.status
    if now in ENDED:
        return Refusal(
            "ended",
            f"{slug} is {now}, and an ended task stays ended: {WAKE}",
            "new work for it is a new ask (/lem new), with a slug of its own",
        )
    found = held_refusal(task, status) or landing_refusal(task, status, start_over)
    if found is not None or status == now:
        return found
    allowed = MOVES.get(now, "").split()
    if status in allowed:
        return None
    listed = ", ".join(allowed)
    if now in LANDING:
        return Refusal(
            MOVE,
            f"{slug} is {now}: it is with its landing, and {WAKE}",
            f"lem land next {slug} names the landing's step",
        )
    return Refusal(
        "move",
        f"{slug} is {now}: lem task move takes it to {listed}, not to {status}",
        "the table of statuses is the design's part 3; lem task show SLUG says where it is",
    )
