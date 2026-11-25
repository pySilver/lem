"""The Tasks page when the app supplies only the workspace's files."""

from typing import TYPE_CHECKING

from lem.board.pages import viewer
from lem.board.views import gather, pages

if TYPE_CHECKING:
    from starlette.requests import Request

    from lem.board.inputs.page import Page
    from lem.store.places import Workspace


def inputs(request: Request, space: Workspace, version: str) -> Page:
    """Draw Tasks with its usual template and no live ports."""
    wanted = viewer.asking(request, space, None, version)
    return pages.page(gather.gather(space.checkout, wanted))
