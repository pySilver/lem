"""The moments on the lanes of a task's time card: an answer or an act of the owner, the end of a
run of the checks and of a review round, the merge agent's read, a refusal, the merge, and a
proposal that is not green, each in the feed's words, on the lane of who did it."""

from typing import TYPE_CHECKING

from lem.board.inputs.names import plural
from lem.board.views.activity import journal_told
from lem.board.views.timeline import shapes
from lem.records.journal.landing import CheckEnd, NotGreen, ReviewRound
from lem.records.journal.merge import MergeNoted, ReadNoted, RefusalNoted
from lem.records.journal.task import OwnerAct

if TYPE_CHECKING:
    from collections.abc import Iterator

    from lem.board.views.activity.told import Told
    from lem.records.journal.entry import Entry
    from lem.records.record import Record

LANES = (
    (CheckEnd, shapes.CHECKS),
    (ReviewRound, shapes.REVIEW),
    (OwnerAct, shapes.YOU),
    (ReadNoted, shapes.MERGER),
    (RefusalNoted, shapes.MERGER),
    (MergeNoted, shapes.MERGER),
    (NotGreen, shapes.LEM),
)


def marks(record: Record) -> Iterator[shapes.Moment]:
    """The task's moments, each on its lane."""
    for entry in record.journal:
        lane = lane_of(entry)
        told = journal_told.told_of(entry, record.task) if lane else ()
        if lane and told:
            yield moment(lane, entry, told[-1])


def lane_of(entry: Entry) -> str | None:
    """The lane of an entry that is a moment of the card, or None."""
    return next((lane for kind, lane in LANES if isinstance(entry, kind)), None)


def moment(lane: str, entry: Entry, told: Told) -> shapes.Moment:
    """An entry's moment on its lane; a proposal that is not green counts its reasons."""
    if isinstance(entry, NotGreen):
        return shapes.Moment(
            lane, entry.at, told.head, plural(len(entry.reasons), "reason")
        )
    sub = " · ".join(filter(None, (told.text, told.sub)))
    return shapes.Moment(lane, entry.at, told.head, sub)
