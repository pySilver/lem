"""The live workspace and task records behind the server's typed pages."""

from typing import TYPE_CHECKING
from urllib.parse import parse_qs

from lem.board.pages import joined, live, spaces, workspace
from lem.board.views import pages
from lem.board.views.backlog.wanted import wanted
from lem.board.views.panel import confirm, opened

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
            joined.combined(request, joined.local_rows(request)),
            state.facts.host,
            problem=joined.peer_problem(request),
        )
    found = workspace.for_page(request, space)
    drawn = workspace.read(request, found, version)
    rows = joined.combined(request, joined.local_rows(request, spaces.current(drawn)))
    drawn = joined.with_addons(request, space, drawn)
    query = request.query_params
    return pages.page(
        drawn,
        wanted(parse_qs(str(query))),
        live.note_of(query.get("note"), space.checkout, drawn.viewer.task),
        selection(request, found.settings.state.keep_days),
        switcher=spaces.menu(rows, drawn.viewer.workspace, drawn.viewer.host),
    )


def selection(request: Request, days: int) -> opened.Opened:
    """The task step and answer fields named by this request."""
    query = request.query_params
    words = query.get("words", "")
    asked = confirm.Asked(key=query.get("key"), words=words)
    return opened.Opened(
        page=request.path_params.get("page"), asked=asked, keep_days=days
    )
