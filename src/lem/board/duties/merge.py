"""A duty of the board server: the merge agent's merge, and the owner's that a read made due again.

Nothing until the step `board-duties` builds it.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.store.places import Workspace


def tick(workspace: Workspace, now: Moment) -> None:
    """Do the duty for `workspace` at `now`: nothing yet."""
