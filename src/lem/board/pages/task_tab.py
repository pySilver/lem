"""An unknown tab keeps the task's navigation and says which address failed."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.board.inputs.switcher import Workspaces
from lem.board.inputs.task.panel import Missing

if TYPE_CHECKING:
    from lem.board.inputs.page import Page


def missing(board: Page | Workspaces, tab: str) -> Page | Workspaces:
    """Use the Overview's header and tabs in the 404 panel."""
    if isinstance(board, Workspaces) or board.panel is None:
        return board
    panel = board.panel
    if panel.missing and not panel.missing.found:
        return board
    viewer = board.frame.viewer
    home = f"{viewer.base}/"
    if viewer.view != "tasks":
        home += viewer.view
    unknown = Missing(title="Not found", said=f"A task has no tab “{tab}”.", back=home)
    tabs = tuple(replace(link, current=False) for link in panel.tabs)
    return replace(board, panel=replace(panel, tabs=tabs, missing=unknown))
