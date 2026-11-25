"""A write of an act to the task's record, and the act in its journal (`OwnerAct`, the event
`board.act` on `main`): what he did, the question and the option, and from where, never his
login.

A write names the revision it read (`store.tasks.update`); when another write came first, the
change is made again on the record as it is now, which reads the question again, so that of two
answers at once the first counts and the second says which.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.decisions.writing import updated
from lem.records.journal.task import OwnerAct

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from lem.board.acts.asker import Asker
    from lem.records.record import Record


def with_act(record: Record, entry: OwnerAct) -> Record:
    """The record with the act in its journal."""
    return replace(record, journal=(*record.journal, entry))


def act_of(
    act: str,
    asker: Asker,
    now: datetime,
    *,
    question: str | None = None,
    option: str | None = None,
) -> OwnerAct:
    """The journal's entry of an act of the owner on the board: the act, the question and
    the option it answered, and the listener it came to."""
    return OwnerAct(at=now, act=act, question=question, option=option, via=asker.via)


def noted(state: Path, slug: str, entry: OwnerAct) -> Record:
    """Put the act in the task's journal."""
    return updated(state, slug, partial(with_act, entry=entry))
