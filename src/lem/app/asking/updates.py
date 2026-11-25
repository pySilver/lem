"""Write a card's change against the latest task revision."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

# Other changes in the same task need not leave the card for a new request.
ATTEMPTS = 8  # unmeasured estimate for writes one can reasonably retry at once


def changed(folder: Path, change: tasks.Change) -> Record:
    """Apply a pure change, re-read after another write, and refuse on contention."""
    state = folder.parents[1]
    for _ in range(ATTEMPTS):
        record = tasks.read(state, folder.name)
        try:
            return tasks.update(state, folder.name, change, expect=record.revision)
        except Refusal as refused:
            if refused.code != "stale":
                raise
    raise Refusal(
        "ask-busy-task",
        f"{folder.name} still has concurrent changes",
        "read the card again before the owner answers",
    )
