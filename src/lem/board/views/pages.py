"""A whole page of a workspace from its world (`board_pages.kanban_page`, `waits_page`,
`backlog_page`, `activity_page`, `older_page`, `new_page` and `board_task.panel` on `main`): the
frame, the one view of its address, and the panel of the task it opens.

The address says the view (`Viewer.view`), the task and its tab (`Viewer.task`, `Viewer.tab`);
the backlog's filter is the address's query (`want`), and the result of an act comes in as
`note`. A route of `board/pages/` reads the world (`gather.py`) and renders what this gives.
"""

from typing import TYPE_CHECKING

from lem.board.inputs.page import Page
from lem.board.views import tasks
from lem.board.views.backlog import groups, search, view
from lem.board.views.backlog.wanted import Wanted
from lem.board.views.frame.page import Beside, frame
from lem.board.views.waits import view as waits

if TYPE_CHECKING:
    from lem.board.inputs.parts import Note
    from lem.board.views.world import World

NOTHING = Wanted()


def page(world: World, want: Wanted = NOTHING, note: Note | None = None) -> Page:
    """The page the world's viewer asks for."""
    shown = world.viewer.view
    return Page(
        frame=frame(world, beside(world)),
        note=note,
        tasks=tasks.tasks(world) if shown == "tasks" else None,
        waits=waits.waits(world) if shown == "waits" else None,
        backlog=view.backlog(world, want) if shown == "backlog" else None,
    )


def beside(world: World) -> Beside:
    """What the frame takes of the backlog: the Backlog key's count, the search's rows of
    items, and the Backlog view's keys."""
    records = tuple(seen.record for seen in world.tasks)
    keys = view.KEYS if world.viewer.view == "backlog" else None
    return Beside(
        backlog=groups.undecided(world.backlog, records),
        keys=keys,
        entries=search.search_rows(world.backlog, records, world.viewer.base),
    )
