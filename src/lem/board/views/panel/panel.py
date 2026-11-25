"""The panel of one task (`board_task.panel` on `main`): its header and its tabs, and the one tab
or step its address shows; or, for an address that names no task, the panel that says so.

The tabs Criteria and decisions, Checks and review, Timeline and Artifacts are other views'; the
caller passes the function of each it draws (`Sections`). A step of an act draws the header with
no act of its own, and no tab is the current one."""

from functools import partial
from typing import TYPE_CHECKING

from lem.board.inputs.task.panel import Missing, Panel
from lem.board.views import owed, standing
from lem.board.views.artifacts.listing import count
from lem.board.views.panel import head, overview, shown, steps, tabs
from lem.board.views.panel.opened import NO_SECTIONS, NOTHING_OPENED, Shown

if TYPE_CHECKING:
    from lem.board.inputs.task.overview import Overview
    from lem.board.inputs.task.panel import Shows
    from lem.board.views.panel.opened import Opened, Sections
    from lem.board.views.world import Seen, World

# The addresses that open a step of an act, not a tab.
STEPS = frozenset(("merge", "park", "drop", "card"))


def panel(
    world: World,
    slug: str,
    shows: Shows,
    sections: Sections = NO_SECTIONS,
    opened: Opened = NOTHING_OPENED,
) -> Panel:
    """The panel of task `slug` on the tab or step `shows`."""
    seen = found(world, slug)
    if seen is None:
        return missing(world, slug)
    rows = owed.of_task(world, slug)
    task = Shown(world, seen, rows, standing.standing(seen, rows))
    step = shows in STEPS
    base = partial(
        Panel,
        slug=slug,
        shows=shows,
        head=head.head(world, seen, rows, task.standing, acting=not step),
        tabs=tabs.tabs(world, slug, "" if step else shows, count(seen)),
    )
    if shows == "overview":
        return base(overview=first(task, opened))
    return steps.body(base, shows, task, opened, sections)


def found(world: World, slug: str) -> Seen | None:
    """The task `slug` of the world, or None."""
    named = (one for one in world.tasks if one.record.task.slug == slug)
    return next(named, None)


def first(task: Shown, opened: Opened) -> Overview:
    """The tab Overview."""
    world, seen = task.world, task.seen
    return overview.overview(world, seen, task.rows, task.standing, opened.keep_days)


def missing(world: World, slug: str) -> Panel:
    """The panel of an address that names no task."""
    said = f"No task “{slug}” is on record in this repository."
    back = shown.view_href(world.viewer.base, world.viewer.view)
    return Panel(slug=slug, missing=Missing(title="Not found", said=said, back=back))
