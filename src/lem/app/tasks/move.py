"""`lem task move`: a task to a status, by the table of statuses (the design's part 3).

The landing's own statuses (`landing`, `open`, `landed`) are entered by `lem land` alone, and a
task in `landing` or `open` leaves them by `lem land` too. A drop, from any status that is not
ended and under the step lock, and a start over are the step `task`'s.
"""

from functools import partial
from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.landing import changes
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.task import Status

# Where each status may go by `lem task move` (the table of part 3, less the landing's moves).
MOVES = MappingProxyType(
    {
        "queued": "shaping building",
        "shaping": "building answered queued",
        "building": "queued planned ready shaping answered",
        "planned": "building",
        "ready": "building",
    }
)


class Moved(Frozen, frozen=True, kw_only=True):
    """The move: the task, the status it left, and the one it is in."""

    slug: str
    was: str
    status: str


def check(slug: str, was: Status, status: Status) -> None:
    """Refuse a move the table does not have."""
    allowed = MOVES.get(was, "").split()
    if status in allowed:
        return
    listed = ", ".join(allowed) or "no status"
    raise Refusal(
        "move",
        f"{slug} is {was}: lem task move takes it to {listed}, not to {status}",
        "the landing's statuses move by lem land; lem land next names its step",
    )


def moved(folder: Path, slug: str, status: Status, lines: tuple[str, ...]) -> Moved:
    """Move the task `slug` to `status`, with the stage's lines."""
    state = places.workspace(folder).state
    record = tasks.read(state, slug)
    was = record.task.status
    check(slug, was, status)
    line = "; ".join(lines) or status
    change = partial(changes.moved, status=status, line=line, now=clock.now())
    tasks.update(state, slug, change, record.revision)
    return Moved(slug=slug, was=was, status=status)
