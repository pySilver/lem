"""A duty of the board server: the hourly keeping of the state folder.

Nothing until the step `board-duties` builds it.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.store.places import Workspace


def tick(workspace: Workspace, now: Moment) -> None:
    """Do the duty for `workspace` at `now`: nothing yet."""
