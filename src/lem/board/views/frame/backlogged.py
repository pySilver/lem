"""What the frame of a page takes of the backlog: the Backlog key's count, the search's rows of
items, and the Backlog view's keys."""

from typing import TYPE_CHECKING

from lem.board.views.backlog import groups, search, view
from lem.board.views.frame.page import Beside

if TYPE_CHECKING:
    from lem.board.inputs.switcher import Switcher
    from lem.board.views.world import World


def beside(world: World, switcher: Switcher | None = None) -> Beside:
    """What the frame takes of the backlog: the Backlog key's count, the search's rows of
    items, and the Backlog view's keys."""
    records = tuple(seen.record for seen in world.tasks)
    keys = view.KEYS if world.viewer.view == "backlog" else None
    return Beside(
        switcher=switcher,
        problems=world.problems,
        backlog=groups.undecided(world.backlog, records),
        keys=keys,
        entries=search.search_rows(world.backlog, records, world.viewer.base),
    )
