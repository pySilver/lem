"""A whole page of a workspace from its world (`board_pages.kanban_page`, `waits_page`,
`backlog_page`, `activity_page`, `older_page`, `new_page` and `board_task.panel` on `main`): the
frame, the one view of its address, and the panel of the task it opens.

The address says the view (`Viewer.view`), the task and its tab (`Viewer.task`, `Viewer.tab`);
the backlog's filter is the address's query (`want`), and the result of an act comes in as
`note`. A route of `board/pages/` reads the world (`gather.py`) and renders what this gives.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.board.inputs.page import Page
from lem.board.views import viewed
from lem.board.views.backlog.wanted import Wanted
from lem.board.views.frame import backlogged
from lem.board.views.frame import page as layout
from lem.board.views.panel.opened import NOTHING_OPENED, Opened
from lem.board.views.shown import panel_of

if TYPE_CHECKING:
    from lem.board.inputs.parts import Note
    from lem.board.inputs.switcher import Switcher
    from lem.board.views.world import World

NOTHING = Wanted()


def page(
    world: World,
    want: Wanted = NOTHING,
    note: Note | None = None,
    opened: Opened = NOTHING_OPENED,
    *,
    switcher: Switcher | None = None,
) -> Page:
    """The page the world's viewer asks for; `opened` is what the address of a step of the
    task's panel names."""
    framed = partial(
        Page,
        frame=layout.frame(world, backlogged.beside(world, switcher)),
        note=note,
        panel=panel_of(world, opened),
    )
    return viewed.with_view(framed, world, want)
