"""The one view of a page's address (`Viewer.view`): Tasks, Waits for you, Backlog, Activity,
the older ended tasks, or a new task."""

from typing import TYPE_CHECKING

from lem.board.views import older, tasks
from lem.board.views.activity import new_task
from lem.board.views.activity import view as activity
from lem.board.views.backlog import view as backlog
from lem.board.views.waits import view as waits

# The views past the three of every day.
LATER = frozenset(("activity", "done", "new"))

if TYPE_CHECKING:
    from functools import partial

    from lem.board.inputs.page import Page
    from lem.board.views.backlog.wanted import Wanted
    from lem.board.views.world import World


def with_view(framed: partial[Page], world: World, want: Wanted) -> Page:
    """The page with the view its address names; `want` is the backlog's filter."""
    shown = world.viewer.view
    if shown == "backlog":
        return framed(backlog=backlog.backlog(world, want))
    if shown == "waits":
        return framed(waits=waits.waits(world))
    if shown in LATER:
        return later(framed, world)
    return framed(tasks=tasks.tasks(world))


def later(framed: partial[Page], world: World) -> Page:
    """The page with Activity, the older ended tasks, or a new task."""
    shown = world.viewer.view
    if shown == "activity":
        return framed(activity=activity.activity(world))
    if shown == "done":
        return framed(older=older.older(world))
    return framed(new=new_task.new_task(world))
