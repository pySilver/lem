"""The server's own addresses: who it is, its stop, the workspaces as data, a task's raw files,
and the board's notifications.

`GET /api/server` and `POST /api/server/stop` are built (the slice of `slice-board`); the rest
answer 501 until the step `board-service` builds them. Only a program on this machine stops the
server: the request comes from the loopback address and carries no `Origin` and no
`Sec-Fetch-Site`, one of which a browser adds to each request of a web page, so that no page
can stop it (`serve.stop_refusal` on `main`).
"""

from http import HTTPStatus
from typing import TYPE_CHECKING

import msgspec
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

from lem.board import stub
from lem.board.facts import HEADER

if TYPE_CHECKING:
    from starlette.requests import Request

SERVICE = "board-service"
LOOPBACK = ("127.0.0.1", "::1", "::ffff:127.0.0.1")
TASK = "/{host}/{workspace}/tasks/{slug}"


async def server(request: Request) -> Response:
    """Who this server is, as JSON, with its own header."""
    return Response(
        msgspec.json.encode(request.app.state.facts),
        media_type="application/json",
        headers={HEADER: "lem"},
    )


def stop_refusal(request: Request) -> str | None:
    """None when the request may stop the server, else the line its 403 says."""
    if request.client is None or request.client.host not in LOOPBACK:
        return "Only a program on this machine stops the server: lem serve stop there."
    if "origin" in request.headers or "sec-fetch-site" in request.headers:
        return (
            "A web page does not stop the server: lem serve stop on this machine does."
        )
    return None


async def stop(request: Request) -> Response:
    """End the server after this answer, when the request may."""
    refused = stop_refusal(request)
    if refused is not None:
        return PlainTextResponse(refused, status_code=HTTPStatus.FORBIDDEN)
    request.app.state.stop()
    return PlainTextResponse("the board server stops")


ROUTES = (
    Route("/api/server", server, methods=["GET"]),
    Route("/api/server/stop", stop, methods=["POST"]),
    *stub.routes(
        SERVICE,
        "GET",
        "/api/workspaces",
        "/manifest.webmanifest",
        "/sw.js",
        "/push/key",
        "/push/latest",
        f"{TASK}/raw/{{path:path}}",
        f"{TASK}/media/{{path:path}}",
    ),
    *stub.routes(SERVICE, "POST", "/push/subscribe", "/push/unsubscribe", "/push/test"),
)
