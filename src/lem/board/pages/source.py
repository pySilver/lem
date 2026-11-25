"""The input seam between the board's HTTP pages and its views."""

from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING, Protocol

from starlette.exceptions import HTTPException
from starlette.responses import HTMLResponse, Response
from starlette.routing import Route

from lem.board.inputs.switcher import Failure
from lem.board.pages import place, render, stamps, task_tab

if TYPE_CHECKING:
    from starlette.requests import Request

    from lem.board.inputs.page import Page
    from lem.board.inputs.switcher import Workspaces
    from lem.store.places import Workspace


class Source(Protocol):
    """The app supplies inputs for a fresh look at the requested page."""

    def __call__(
        self, request: Request, space: Workspace | None, version: str
    ) -> Page | Workspaces:
        """Read the request's view and return the typed inputs."""


def provided(request: Request) -> Source | None:
    """The server's input provider, when the app has bound it."""
    return getattr(request.app.state, "page_inputs", None)


def endpoint(request: Request, *, name: str = "tasks") -> Response:
    """Get the typed view for this request and render the page or its task frame."""
    request.state.page_route = name
    provider = provided(request)
    try:
        return resolved(request, provider)
    except HTTPException as refused:
        board = Failure(title="The page did not open", said=refused.detail)
        html = render.section("failure.html", board)
        return HTMLResponse(
            html, status_code=refused.status_code, headers=refused.headers
        )


def resolved(request: Request, provider: Source | None) -> Response:
    """Read the workspace version before its inputs."""
    space = place.workspace(request) if "workspace" in request.path_params else None
    if provider is None:
        raise HTTPException(
            HTTPStatus.SERVICE_UNAVAILABLE, "The board's page inputs are not available."
        )
    stamp = stamps.shown(request, space.state).version if space else ""
    board = provider(request, space, stamp)
    unknown = request.path_params.get("unknown_tab")
    if unknown:
        board = task_tab.missing(board, unknown)
    return render.page(board, fragment=request.headers.get("turbo-frame") == "task")


def route(base: str, name: str) -> Route:
    """One named view or tab under its address."""
    return bound(f"{base}/{name}", name)


def bound(path: str, name: str) -> Route:
    """Set the selected route name before asking the app for its inputs."""
    return Route(path, partial(endpoint, name=name), name=name)
