"""The workspace lock, over a claim: the scan of every task's record and the publication of
the new task's record, together (the design's part 3, "Locks").

The rule of a claim (a ticket held by a landed task, an item held by an open task) is the
caller's pure function: it reads every record and gives the new one, or refuses.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from lem.kernel import locks
from lem.store import guard, places, reviewer_items, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

LOCK = "workspace.lock"

type Claim = Callable[[tuple[Record, ...]], Record]


def claimed(state: Path, claim: Claim) -> Record:
    """Under the workspace lock, give `claim` every record and create the record it gives."""
    guard.writable(state)
    with locks.held(places.locks_folder(state) / LOCK):
        return published(state, claim(tasks.every(state)))


def published(state: Path, record: Record) -> Record:
    """Check the reviewer item and publish its claim together, inside the workspace lock."""
    checkout = state.parent.parent
    path = reviewer_items.relative(checkout, record.task.backlog_item or "")
    if path is None:
        return tasks.create(state, record)
    with reviewer_items.held(state):
        reviewer_items.require(checkout, path)
        return tasks.create(state, record)
