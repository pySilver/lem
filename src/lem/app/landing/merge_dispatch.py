"""The start of the merge agent on the seat in use, kept on the task's record before its brief
is published, so that no reply can name a start the record lacks (`model/landing/dispatches.py`).
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import changes
from lem.app.sessions import seats
from lem.kernel.errors import Fault
from lem.model.landing import dispatches
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.app.sessions.seating import Shown
    from lem.records.landing.propose import MergeDispatch
    from lem.records.record import Record


def dispatched(context: Context, tip: str) -> tuple[MergeDispatch, Shown]:
    """The dispatch of the merge agent for `tip` on origin's base now, on the seat in use (a
    stand-in while one holds), and that seat: the current one repeated, else a new one on
    record."""
    shown = seats.effective(context.record, "merger", context.workspace.checkout)
    if shown.seat is False:
        raise Fault("the merge agent's seat is never off")
    landing = context.record.landing or Landing()
    read = (tip, context.world.base, shown.seat)
    made = dispatches.started(landing, read, context.world.now)
    if made not in landing.dispatches:
        context.write(context.record, partial(kept, dispatch=made))
    return made, shown


def kept(record: Record, *, dispatch: MergeDispatch) -> Record:
    """The record with one more start of the merge agent."""
    landing = record.landing or Landing()
    return changes.landing(record, dispatches=(*landing.dispatches, dispatch))
