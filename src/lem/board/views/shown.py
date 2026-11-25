"""The panel a page opens (`board_task.panel` on `main`): the task of the address on its tab or
step, with the tabs of the other views beside the panel's own."""

from types import MappingProxyType
from typing import TYPE_CHECKING, get_args

from lem.board.inputs.task.panel import Shows
from lem.board.views.artifacts.tab import artifacts
from lem.board.views.checks.tab import checks
from lem.board.views.criteria.tab import criteria
from lem.board.views.panel import panel
from lem.board.views.panel.opened import Opened, Sections
from lem.board.views.timeline import view as timeline

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.board.inputs.task.panel import Panel
    from lem.board.views.world import World


SECTIONS = Sections(
    criteria=criteria, checks=checks, timeline=timeline.tab, artifacts=artifacts
)
# Each tab or step an address may name, by its word.
SHOWS: Mapping[str, Shows] = MappingProxyType(
    {name: name for name in get_args(Shows.__value__)}
)


def panel_of(world: World, opened: Opened) -> Panel | None:
    """The panel of the task the address opens, on its tab or step; a card's step names its
    page after `card/`."""
    slug = world.viewer.task
    if slug is None:
        return None
    tab, _, page = world.viewer.tab.partition("/")
    if page:
        opened = opened._replace(page=page)
    shows = SHOWS.get(tab, "overview")
    return panel.panel(world, slug, shows, SECTIONS, opened)
