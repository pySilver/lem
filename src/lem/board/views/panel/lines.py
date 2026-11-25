"""The owner's other words to a task a breaker holds or that he parked, as lines he types in
any session (`board_task.owner_lines` on `main`)."""

from typing import TYPE_CHECKING

from lem.board.inputs.forms import Typed, Way
from lem.records.holds import BreakerHold, Parked

if TYPE_CHECKING:
    from lem.records.task import Task

SAID = "Or type in any session:"


def owner_lines(task: Task) -> tuple[Way, ...]:
    """`/lem park` and `/lem drop` for a breaker, `/lem resume` and `/lem drop` for a park;
    none for any other task."""
    slug = task.slug
    drop = Typed(command=f"/lem drop {slug}", does="ends it")
    if isinstance(task.hold, BreakerHold):
        park = Typed(command=f"/lem park {slug}", does="puts the task aside")
        return (Way(said=SAID, typed=(park, drop), kind="owner"),)
    if isinstance(task.hold, Parked):
        resume = Typed(command=f"/lem resume {slug}", does="brings it back as it was")
        return (Way(said=SAID, typed=(resume, drop), kind="owner"),)
    return ()
