"""`GET /HOST/WORKSPACE/`: the kanban of a workspace, from its task records."""

from typing import TYPE_CHECKING

from lem.board import stream
from lem.board.pages import place, render
from lem.board.views import kanban
from lem.store import tasks

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response


def page(request: Request) -> Response:
    """The kanban of the workspace the address names, at the version of its records."""
    space = place.workspace(request)
    board = kanban.kanban(
        tasks.every(space.state),
        host=request.path_params["host"],
        workspace=request.path_params["workspace"],
        version=stream.version(space.state),
    )
    return render.page(request, "kanban.html", board)
