"""The live workspace and task records behind the server's typed pages."""

from typing import TYPE_CHECKING
from urllib.parse import parse_qs

from lem.board import counts, workspaces
from lem.board.pages import live, spaces, workspace
from lem.board.views import pages, world
from lem.board.views.backlog.wanted import wanted
from lem.board.views.panel import confirm, opened
from lem.settings.load import settings_of

if TYPE_CHECKING:
    from starlette.requests import Request

    from lem.board.inputs.page import Page
    from lem.board.inputs.switcher import Workspaces
    from lem.store.places import Workspace


def inputs(
    request: Request, space: Workspace | None, version: str
) -> Page | Workspaces:
    """Read the workspace once for the route, after its version was read."""
    if space is None:
        state = request.app.state
        return spaces.index(
            state.counts.rows(state.home, state.facts.host), state.facts.host
        )
    settings = settings_of(
        space.checkout, request.app.state.environ, home=request.app.state.home
    ).settings
    drawn = workspace.read(request, space, settings.branch, version)
    query = request.query_params

    return pages.page(
        drawn,
        wanted(parse_qs(str(query))),
        live.note_of(query.get("note"), space.checkout, drawn.viewer.task),
        selection(request, settings.state.keep_days),
        switcher=spaces.menu(workspace_rows(request, drawn), drawn.viewer.workspace),
    )


def workspace_rows(request: Request, drawn: world.World) -> counts.Rows:
    """The workspace counts for the switcher."""
    state = request.app.state
    if len(workspaces.listed(state.home)) <= 1:
        return ()
    current = spaces.current(drawn)
    return state.counts.rows(state.home, state.facts.host, current=current)


def selection(request: Request, days: int) -> opened.Opened:
    """The task step and answer fields named by this request."""
    query = request.query_params
    words = query.get("words", "")
    asked = confirm.Asked(key=query.get("key"), words=words)
    return opened.Opened(
        page=request.path_params.get("page"), asked=asked, keep_days=days
    )
