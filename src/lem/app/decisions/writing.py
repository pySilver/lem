"""A write of a task's record that checks what it changes against the record it writes: the
record is read, the change made from it, and the write refused as stale when another write came
first; then it is read and made again. So two writes at once each take a number of their own,
and each check runs on the record it changes (`decisions.Task.add` on `main`, under one lock)."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from lem.records.record import Record

type Change = Callable[[Record], Record]
# What makes a write from the record as it is: the change, and what the command says of it.
type Make[Outcome] = Callable[[Record], tuple[Change, Outcome]]

# How many times a write is made again after another came first; each was one the record lock
# let through, so more means writers that never stop, not a slow one.
TRIES = 20
STALE = "stale"


def written[Outcome](state: Path, slug: str, make: Make[Outcome]) -> Outcome:
    """Write the change `make` gives for the record as it is now, at its revision, and give
    what `make` said with it."""
    for _ in range(TRIES):
        record = tasks.read(state, slug)
        change, outcome = make(record)
        try:
            tasks.update(state, slug, change, record.revision)
        except Refusal as refusal:
            if refusal.code != STALE:
                raise
        else:
            return outcome
    raise Refusal(
        STALE,
        f"{slug} was written {TRIES} times while this write waited",
        "run the command again",
    )
