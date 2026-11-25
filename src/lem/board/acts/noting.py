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

from lem.kernel.errors import Refusal
from lem.records.journal.task import OwnerAct
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from pathlib import Path

    from lem.board.acts.asker import Asker
    from lem.records.record import Record

# How many times a write is made again over another write that came first.
TRIES = 3
STALE = "stale"


def written(state: Path, slug: str, change: Callable[[Record], Record]) -> Record:
    """Write `change` to the task's record, made again over a write that came first."""
    for _ in range(TRIES - 1):
        record = tasks.read(state, slug)
        try:
            return tasks.update(state, slug, change, record.revision)
        except Refusal as refusal:
            if refusal.code != STALE:
                raise
    record = tasks.read(state, slug)
    return tasks.update(state, slug, change, record.revision)


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
    return written(state, slug, partial(with_act, entry=entry))
