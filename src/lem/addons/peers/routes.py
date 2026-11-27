"""The board's only add-on import: joined-board reads, the workspace switcher, the jump to a joined
machine's session in this Mac's agterm, and the reads of this Mac's agterm that a joined board
asks for."""

from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Match, Route

from lem.addons.peers import jump, origin, registry, relay, requests, rows
from lem.board import listener

if TYPE_CHECKING:
    from starlette.responses import Response
    from starlette.types import Scope

type Rows = tuple[rows.Row, ...]

READS = ("GET", "HEAD")
GET = ("GET",)


def peers(request: Request) -> registry.Registry:
    """Create one registry per board app, on its first peer-related request."""
    return registry.held(request)


async def spaces(request: Request, own: Rows) -> Rows:
    """A request from another board never fans out to more peers."""
    if requests.HOP in request.headers:
        received = rows.from_header(request.headers.get(rows.SPACES, ""))
        return rows.with_own(received, own, request.app.state.facts.host)
    return await peers(request).spaces(own)


async def forward(request: Request) -> Response:
    """Pass the matched peer's read, along with the workspace switcher."""
    if request.method not in READS:
        return PlainTextResponse(
            "Only a read passes to another machine.",
            status_code=HTTPStatus.METHOD_NOT_ALLOWED,
        )
    registry = peers(request)
    machine = registry.known[request.path_params["peer"]]
    own = await run_in_threadpool(request.app.state.peer_own_rows, request)
    listed = await spaces(request, own)
    here = listener.from_here(request) and not listener.at_door(request)
    return await relay.relay(request, machine, registry, (listed, here))


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


class JumpRoute(JoinedRoute):
    """The jump to a joined machine's session claims only a POST: a read of the same address
    passes to the machine."""

    def matches(self, scope: Scope) -> tuple[Match, Scope]:
        """No match for a method other than POST."""
        if scope.get("method") != "POST":
            return Match.NONE, {}
        return super().matches(scope)


ROUTES = (
    JumpRoute("/{peer}/{workspace}/agterm/{session}", jump.endpoint, methods=("POST",)),
    JoinedRoute("/{peer}/{rest:path}", forward, methods=READS),
    JoinedRoute("/{peer}", forward, methods=READS),
    Route("/api/agterm", origin.agterm, methods=GET),
    Route("/{host}/{workspace}/agterm/{session}", origin.session, methods=GET),
)
