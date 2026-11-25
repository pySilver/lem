"""The progress card of a task's Overview (`board_task.progress` and `ring` on `main`): its
phases, the ring of its plan's tasks, and its numbers."""

from typing import TYPE_CHECKING

from lem.board.inputs.task.now import Phases, Ring
from lem.board.views.panel import plan
from lem.board.views.panel.phases import phases
from lem.board.views.panel.stats import stats

if TYPE_CHECKING:
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World
    from lem.records.record import Record


def progress(world: World, seen: Seen, standing: Standing) -> Phases:
    """The progress card of the task of `seen`."""
    record = seen.record
    return Phases(
        look=standing.look,
        phases=phases(record),
        ring=ring(record),
        stats=stats(world, seen),
    )


def ring(record: Record) -> Ring:
    """The finished tasks of the plan, the one built now, and how many it has."""
    found = plan.progress(record)
    if found is None:
        return Ring(done=0, current=0, total=1, big="–", small="plan tasks")
    built = plan.done(record)
    at = found.of if built else found.at
    finished = found.of if built else max(0, found.at - 1)
    return Ring(
        done=finished,
        current=at,
        total=found.of,
        big=f"{finished}/{found.of}",
        small="plan tasks",
    )
