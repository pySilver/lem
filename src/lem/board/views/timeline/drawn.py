"""Everything the time card draws on its lanes, from a task's record (`time_of` on `main`): the
stretches of its spans and of its criteria, the plan talk, the time of each state that none of
these holds, and the moments of its journal.

A state's time is cut where a span or the criteria's writing and read hold it; the plan talk and
the owner's wait for his yes are drawn beside the work, on lanes of their own. The agent's own
span is no cover: the states say who held the work in it (a build is the agent's, a breaker
the owner's), as `main` drew them before spans of the agent were on record.
"""

from typing import TYPE_CHECKING

from lem.board.views.timeline import (
    blocks,
    criteria,
    marks,
    shapes,
    waits,
    worked,
)

if TYPE_CHECKING:
    from lem.board.views.timeline.frame import Drawn, Frame
    from lem.records.record import Record


def drawn(record: Record, frame: Frame) -> list[Drawn]:
    """The card's stretches and moments of the task, moments outside its time left out."""
    task = record.task
    spans = list(worked.worked(task, frame))
    covering = [*spans, *criteria.written(record, frame)]
    covering.extend(criteria.read(record, frame))
    covers = [
        (each.start, each.end) for each in covering if isinstance(each, shapes.Held)
    ]
    found: list[Drawn] = [*covering, *blocks.rest(record, frame, covers)]
    found.extend(worked.talked(task, frame))
    found.extend(waits.waited(record))
    found.extend(marks.marks(record))
    return [each for each in found if inside(each, frame)]


def inside(each: Drawn, frame: Frame) -> bool:
    """Whether a moment is inside the task's time; a stretch always is."""
    if isinstance(each, shapes.Held):
        return True
    return frame.start <= each.at <= frame.end
