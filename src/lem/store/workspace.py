"""The workspace lock, over a claim: the scan of every task's record and the publication of
the new task's record, together (the design's part 3, "Locks").

The rule of a claim (a ticket held by a landed task, an item held by an open task) is the
caller's pure function: it reads every record and gives the new one, or refuses.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from lem.kernel import locks
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

LOCK = "workspace.lock"

type Claim = Callable[[tuple[Record, ...]], Record]


def claimed(state: Path, claim: Claim) -> Record:
    """Under the workspace lock, give `claim` every record and create the record it gives."""
    with locks.held(places.locks_folder(state) / LOCK):
        return tasks.create(state, claim(tasks.every(state)))
