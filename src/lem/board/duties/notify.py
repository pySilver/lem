"""A duty of the board server: a wait the owner gained, told to the notifier.

The push of each new wait is the step `board-service`'s (the ledger's `duty:push-new-waits`,
with `adapters/notify_push.py`): its builder fills this module, which the runner calls at each
tick (`notes/board-duties.md`). Until then it does nothing.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.board.duties.context import Duty


def tick(duty: Duty) -> None:
    """Do the duty for the workspace of `duty`: nothing yet."""
