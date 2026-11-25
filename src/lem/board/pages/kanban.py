"""`GET /HOST/WORKSPACE/`: the kanban of a workspace, from its task records."""

from typing import TYPE_CHECKING

from starlette.responses import HTMLResponse, Response

from lem.board import watched
from lem.board.pages import place, render, source
from lem.board.views import kanban
from lem.store import tasks

if TYPE_CHECKING:
    from starlette.requests import Request


def page(request: Request) -> Response:
    """The kanban of the workspace the address names. The version it shows is read before
    the records: a write between the two reads makes the version older than the page, so that
    the stream owes the page a refresh, never newer, which would hide the write."""
    if source.provided(request) is not None:
        return source.endpoint(request)
    space = place.workspace(request)
    version = watched.look(space.state, request.app.state.home)
    board = kanban.kanban(
        tasks.every(space.state),
        host=request.path_params["host"],
        workspace=request.path_params["workspace"],
        version=version,
    )
    return HTMLResponse(render.section("kanban.html", board))
