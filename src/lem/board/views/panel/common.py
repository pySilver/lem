"""What several parts of a task's panel read of its record (`board_model.careful_of`,
`track_of` and `pr_of` on `main`): whether it ended, its pull request, its careful call, its
track, and a moment as the page's clock says it."""

from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple

from lem.board.inputs import clock
from lem.board.views.rule import ENDED
from lem.records.journal.landing import CarefulMissed

if TYPE_CHECKING:
    from datetime import datetime

    from lem.board.views.world import World
    from lem.records.landing.record import Pull
    from lem.records.record import Record
    from lem.records.task import Task

TRACKS = MappingProxyType({"small": "fast", "full": "standard"})


class Careful(NamedTuple):
    """The careful call: whether the change is careful, why, and who made it."""

    careful: bool
    why: str
    by: str


def closed(task: Task) -> bool:
    """Whether the task ended."""
    return task.status in ENDED


def pull_of(record: Record) -> Pull | None:
    """The task's pull request, or None."""
    return record.landing.pull if record.landing else None


def careful_of(record: Record) -> Careful | None:
    """The careful call: the one a review made that the shape missed, else the newest
    review's that made one; None while none did."""
    missed = next(
        (one for one in reversed(record.journal) if isinstance(one, CarefulMissed)),
        None,
    )
    if missed is not None:
        return Careful(
            careful=True,
            why=missed.why,
            by="the review called it careful, and the plan did not",
        )
    reviews = record.landing.reviews if record.landing else ()
    made = [review for review in reviews if review.careful is not None]
    if not made:
        return None
    newest = made[-1]
    return Careful(
        careful=bool(newest.careful),
        why=newest.careful_why or "",
        by=f"the review of round {newest.attempt}",
    )


def track_of(task: Task) -> str | None:
    """`fast track` or `standard track`, from its lead or its criteria's size; None before
    either says."""
    if task.lead == "small":
        return "fast track"
    size = size_of(task)
    return f"{TRACKS[size]} track" if size else None


def size_of(task: Task) -> str | None:
    """The size of the task's criteria, or of its newest approval."""
    approvals = task.criteria.approvals
    if task.criteria.size or not approvals:
        return task.criteria.size
    return approvals[-1].size


def stamp(world: World, moment: datetime) -> str:
    """A moment as the page's clock says it (`15:40`, `Nov 24 23:50`)."""
    return clock.stamp(moment, world.clock.now, world.clock.zone)
