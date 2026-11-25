"""A duty of the board server: a wait the owner gained, told to the notifier.

Nothing until the step `board-duties` builds it.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.store.places import Workspace


def tick(workspace: Workspace, now: Moment) -> None:
    """Do the duty for `workspace` at `now`: nothing yet."""
