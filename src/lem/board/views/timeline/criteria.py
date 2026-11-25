"""The stretches of a task's criteria (`time_of` on `main`): Lem writes them from the interview's
end to the personas' read, the skip question, an approval or the next move past the shape; the
personas read them on their own lane. The owner's wait for his yes is `waits.py`'s.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.views.timeline import frame, shapes
from lem.records.journal.task import StateNoted

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime

    from lem.records.approvals import PersonaRead
    from lem.records.record import Record

FAMILIES = MappingProxyType({1: "one model family", 2: "two model families"})
WRITES = ("Lem writes the criteria", "from your answers and what the code says")


def written(record: Record, drawn: frame.Frame) -> Iterator[frame.Drawn]:
    """Lem's writing of the criteria after each end of the interview."""
    ends = (
        span.end for span in record.task.spans if span.name == "interview" and span.end
    )
    for end in ends:
        yield frame.ran(drawn, shapes.LEM, end, next_step(record, end), WRITES)


def next_step(record: Record, since: datetime) -> datetime | None:
    """The first step after `since` that ends Lem's writing of the criteria."""
    criteria = record.task.criteria
    moves = (
        entry.at
        for entry in record.journal
        if isinstance(entry, StateNoted) and entry.status != "shaping"
    )
    steps = [
        *(read.started for read in criteria.reads),
        *(approval.at for approval in criteria.approvals),
        *([criteria.skip_at] if criteria.skip_at else []),
        *moves,
    ]
    return min((step for step in steps if step > since), default=None)


def read(record: Record, drawn: frame.Frame) -> Iterator[frame.Drawn]:
    """The personas' reads of the criteria, on their own lane."""
    for one in record.task.criteria.reads:
        said = ("The personas’ read of the criteria", read_sub(one))
        yield frame.ran(drawn, shapes.PERSONAS, one.started, one.ended, said)


def read_sub(one: PersonaRead) -> str:
    """`3 of 3 answered, two model families · nobody confused`."""
    families = len(one.families)
    named = FAMILIES.get(families, f"{families} model families")
    flagged = f"{one.flagged} flagged" if one.flagged else "nobody confused"
    split = " · the families split" if one.split else ""
    return f"{one.answered} of {one.asked} answered, {named} · {flagged}{split}"
