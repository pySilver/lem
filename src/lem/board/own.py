"""The server's own addresses: who it is, its stop, and the workspaces as data.

`GET /api/server` says who serves, with the server's own header, and the board's notifications
(their devices, the last push, and what the watcher last failed at). Only a program on this
machine stops the server, on the main listener: the request comes from the loopback address and
carries no `Origin` and no `Sec-Fetch-Site`, one of which a browser adds to each request of a web
page, so that no page can stop it; at the door the stop is no address (`serve.stop_refusal` on
`main`). `GET /api/workspaces` lists the workspaces with their counts (`counts.py`).
"""

from http import HTTPStatus
from typing import TYPE_CHECKING

import anyio
import msgspec
from starlette.responses import PlainTextResponse, Response

from lem.board import listener
from lem.board.facts import HEADER, MARK, Facts
from lem.board.push import listing

if TYPE_CHECKING:
    from starlette.requests import Request

JSON = "application/json"


class Told(Facts, frozen=True, kw_only=True):
    """The server's answer: its facts, and its notifications."""

    push: listing.Shown


async def server(request: Request) -> Response:
    """Who this server is, as JSON, with its own header."""
    state = request.app.state
    shown = listing.status_of(state.home)
    shown = msgspec.structs.replace(
        shown, problem=shown.problem or state.watcher.problem
    )
    told = Told(**msgspec.structs.asdict(state.facts), push=shown)
    body = msgspec.json.encode(told)
    return Response(body, media_type=JSON, headers={HEADER: MARK})


def stop_refusal(request: Request) -> str | None:
    """None when the request may stop the server, else the line its 403 says."""
    if not listener.from_here(request):
        return "Only a program on this machine stops the server: lem serve stop there."
    if "origin" in request.headers or "sec-fetch-site" in request.headers:
        return (
            "A web page does not stop the server: lem serve stop on this machine does."
        )
    return None


async def stop(request: Request) -> Response:
    """End the server after this answer, when the request may."""
    if listener.at_door(request):
        return PlainTextResponse(
            "The door does not stop the server.",
            status_code=HTTPStatus.METHOD_NOT_ALLOWED,
        )
    refused = stop_refusal(request)
    if refused is not None:
        return PlainTextResponse(refused, status_code=HTTPStatus.FORBIDDEN)
    request.app.state.stop()
    return PlainTextResponse("the board server stops")


async def spaces(request: Request) -> Response:
    """The workspaces of the machine's list as JSON, each with its counts."""
    state = request.app.state
    rows = await anyio.to_thread.run_sync(
        state.counts.rows, state.home, state.facts.host
    )
    return Response(msgspec.json.encode(rows), media_type=JSON)
