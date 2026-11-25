"""A duty of the board server: the wake of a task whose pull request the forge calls conflicting.

Nothing until the step `board-duties` builds it.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.store.places import Workspace


def tick(workspace: Workspace, now: Moment) -> None:
    """Do the duty for `workspace` at `now`: nothing yet."""
