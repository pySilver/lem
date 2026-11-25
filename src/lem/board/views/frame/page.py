"""The frame of every page of a workspace (`board_pages.layout` on `main`): who asks, the head,
the phone's bar, the sidebar, the bar above the view, the status bar, the search over every card,
and the view's keys.

What the frame needs of the backlog (the Backlog key's count and the search's rows of items)
and of the machine (the switcher of its workspaces) comes in from the caller, so that the frame
reads the backlog once with its view.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.board.inputs.page import Frame
from lem.board.inputs.search import Search
from lem.board.views.frame import (
    bars,
    counted,
    keys,
    search,
    sidebar,
    status,
    summary,
    views,
)

if TYPE_CHECKING:
    from lem.board.inputs.layout import Keys
    from lem.board.inputs.search import Found
    from lem.board.inputs.switcher import Switcher
    from lem.board.views.world import World


@dataclass(frozen=True, kw_only=True, slots=True)
class Beside:
    """What the frame takes from beside the tasks: the Backlog key's count, the search's rows
    of the backlog, the backlog view's keys, the switcher of the machine's workspaces (None
    for this workspace alone), and what did not read."""

    backlog: int | None = None
    keys: Keys | None = None
    entries: tuple[Found, ...] = ()
    switcher: Switcher | None = None
    problems: tuple[str, ...] = ()


def frame(world: World, beside: Beside) -> Frame:
    """The frame of a page of the world."""
    counts = counted.counted(world)
    switcher = beside.switcher or views.lone(world, sidebar.says(counts))
    title, line = summary.said(world.viewer.view, counts)
    return Frame(
        viewer=world.viewer,
        head=bars.head(world, title, counts),
        phonebar=bars.phonebar(world, counts),
        sidebar=sidebar.sidebar(
            world, counts, beside.backlog, switcher, beside.problems
        ),
        topbar=bars.topbar(world, title, line),
        statusbar=status.statusbar(world, beside.problems),
        search=searched(world, counts, beside),
        keys=keys.keys_of(world.viewer.view, counts) or beside.keys,
        demo=world.demo,
    )


def searched(world: World, counts: counted.Counted, beside: Beside) -> Search:
    """The search over every card: the tasks, then the backlog's items."""
    rows = search.task_rows(world, counts) + beside.entries
    workspace = world.viewer.workspace
    return Search(field=f"search-q-{workspace}", rows=rows)
