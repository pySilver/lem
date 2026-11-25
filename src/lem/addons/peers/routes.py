"""The board's only add-on import: joined-board reads and the workspace switcher."""

from http import HTTPStatus
from typing import TYPE_CHECKING, cast

from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Match, Route

from lem.addons.peers import registry, relay, requests, rows

if TYPE_CHECKING:
    from collections.abc import Callable

    from starlette.responses import Response
    from starlette.types import Scope

type Rows = tuple[rows.Row, ...]
type OwnRows = Callable[[Request], Rows]


def peers(request: Request) -> registry.Registry:
    """Create one registry per board app, on its first peer-related request."""
    state = request.app.state
    if not hasattr(state, "peer_registry"):
        host = state.facts.host
        state.peer_registry = registry.Registry(home=state.home, own=host)
    return cast("registry.Registry", state.peer_registry)


async def spaces(request: Request, own: Rows) -> Rows:
    """A request from another board never fans out to more peers."""
    if requests.HOP in request.headers:
        received = rows.from_header(request.headers.get(rows.SPACES, ""))
        return rows.with_own(received, own, request.app.state.facts.host)
    return await peers(request).spaces(own)


async def forward(request: Request) -> Response:
    """Pass the matched peer's read, along with the workspace switcher."""
    if request.method not in {"GET", "HEAD"}:
        return PlainTextResponse(
            "Only a read passes to another machine.",
            status_code=HTTPStatus.METHOD_NOT_ALLOWED,
        )
    host = request.path_params["peer"]
    registry = peers(request)
    machine = registry.known[host]
    local = getattr(request.app.state, "peer_own_rows", empty)
    listed = await spaces(request, local(request))
    return await relay.relay(request, machine, registry, listed)


def empty(request: Request) -> Rows:
    """The slice board has no workspace rows until the pages step supplies them."""
    return ()


class JoinedRoute(Route):
    """A route claims a first path component only when it names a joined peer."""

    def matches(self, scope: Scope) -> tuple[Match, Scope]:
        """Fall through for this board, unknown peers and any incoming Lem-Hop."""
        match, child = super().matches(scope)
        if match is Match.NONE:
            return match, child
        request = Request(scope)
        if requests.HOP in request.headers:
            return Match.NONE, {}
        host = child["path_params"]["peer"]
        joined = peers(request).reload()
        return (Match.FULL, child) if host in joined else (Match.NONE, {})


ROUTES = (
    JoinedRoute("/{peer}/{rest:path}", forward, methods=["GET", "HEAD"]),
    JoinedRoute("/{peer}", forward, methods=["GET", "HEAD"]),
)
