"""The order of the cards in each column of Tasks (`board_model.lanes_sorted` on `main`): the one
that waited longest first; in "Waits for you" the most pressing first; a landing on top of the
checks; and in Done the newest first, its first `SHOWN` as cards and the rest on a page of their
own."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.records.holds import Blocked, BreakerHold, OwnerHold

if TYPE_CHECKING:
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen
    from lem.records.base import Moment
    from lem.records.task import Task

    # A task with where it stands.
    type Placed = tuple[Seen, Standing]

# The ended tasks Done draws as cards: an unmeasured estimate of a column that fits one screen
# of the large board (`DONE_SHOWN` on `main`, docs/plans/2026-11-21-done-column-shows-newest.md).
SHOWN = 20
# What presses most of the owner's, first.
PRESSING = MappingProxyType(
    {"breaker": 0, "held": 1, "queued": 2, "blocked": 3, "planned": 4, "open": 5}
)
STATUSES = (
    "queued",
    "shaping",
    "building",
    "planned",
    "ready",
    "landing",
    "open",
    "landed",
    "dropped",
    "answered",
)


def pressing(task: Task) -> int:
    """How much the owner's thing on the task presses: a breaker most, an open pull request
    least."""
    hold = task.hold
    if isinstance(hold, BreakerHold):
        return PRESSING["breaker"]
    if isinstance(hold, OwnerHold):
        return PRESSING["held"]
    if isinstance(hold, Blocked):
        return PRESSING["blocked"]
    return PRESSING.get(task.status, len(PRESSING))


def ordered(key: str, placed: list[Placed]) -> list[Placed]:
    """The cards of the column `key` in the board's order."""
    if key == "done":
        return sorted(placed, key=newest_first)
    if key == "you":
        return sorted(placed, key=pressing_first)
    if key == "checks":
        return sorted(placed, key=landing_first)
    return sorted(placed, key=status_first)


def newest_first(pair: Placed) -> float:
    """The task that ended last first."""
    return -pair[1].since.timestamp()


def pressing_first(pair: Placed) -> tuple[int, Moment]:
    """The owner's most pressing thing first, then the one that waited longest."""
    seen, where = pair
    return pressing(seen.record.task), where.since


def status_first(pair: Placed) -> tuple[int, Moment]:
    """By status, in the order a task goes through them, then the one that waited longest."""
    seen, where = pair
    return STATUSES.index(seen.record.task.status), where.since


def landing_first(pair: Placed) -> tuple[bool, Moment]:
    """A landing first, then the rest by how long they waited."""
    seen, where = pair
    return seen.record.task.status != "landing", where.since
