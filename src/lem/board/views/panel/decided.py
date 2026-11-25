"""The stat of a task's decisions (`board_task.progress` on `main`): how many were taken, how
many went past the personas, how many breakers; in the owner's look while a breaker waits."""

from typing import TYPE_CHECKING

from lem.board.inputs.names import plural
from lem.board.inputs.task.now import Stat
from lem.board.views.panel.common import closed
from lem.board.views.panel.important import PAST_PERSONAS
from lem.records.decisions import Breaker, Taken
from lem.records.holds import BreakerHold

if TYPE_CHECKING:
    from lem.board.inputs.text import Look
    from lem.records.record import Record


def decisions(record: Record) -> Stat:
    """The task's decisions as one number and its line."""
    task = record.task
    taken = [one for one in task.decisions if isinstance(one, Taken)]
    past = sum(1 for one in taken if one.by in PAST_PERSONAS)
    breakers = sum(1 for one in task.decisions if isinstance(one, Breaker))
    look: Look | None = "bad" if past else None
    if isinstance(task.hold, BreakerHold):
        look = "you"
    return Stat(
        label="Decisions",
        shown=str(len(taken)),
        said=said_of(record, len(taken), past, breakers),
        look=look,
    )


def said_of(record: Record, taken: int, past: int, breakers: int) -> str:
    """`2 taken, 1 past the personas, 1 breaker`, or none."""
    if not record.task.decisions:
        return "none" if closed(record.task) else "none yet"
    said = f"{taken} taken"
    if past:
        said = f"{said}, {past} past the personas"
    if breakers:
        said = f"{said}, {plural(breakers, 'breaker')}"
    return said
