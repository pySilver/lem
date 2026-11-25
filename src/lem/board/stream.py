"""The workspace's version and the SSE stream that tells its page to read again."""

from functools import partial
from typing import TYPE_CHECKING

import anyio
from sse_starlette import EventSourceResponse, ServerSentEvent
from starlette.responses import Response

from lem.board.pages import place, stamps

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from starlette.requests import Request

    from lem.board import watched

    type Look = Callable[[], watched.ViewStamp]

TICK_SECONDS = 0.5
PING_SECONDS = 10
REFRESH = '<turbo-stream action="refresh"></turbo-stream>'
EVENTS = "text/event-stream"


def owes(*, rendered: str | None, missed: bool, told: str) -> bool:
    """Whether the page could have missed a change."""
    return missed or bool(rendered and rendered != told)


def refresh(told: str) -> ServerSentEvent:
    """One Turbo refresh, with the version as its event ID."""
    return ServerSentEvent(data=REFRESH, id=told)


def pinged() -> ServerSentEvent:
    """The sign of life of a quiet stream."""
    return ServerSentEvent(event="ping", data="ping")


async def refreshed(
    look: Look, *, rendered: str | None, missed: bool
) -> AsyncGenerator[ServerSentEvent]:
    """Compare the workspace version on open, and all watched stamps after a poll."""
    told = await anyio.to_thread.run_sync(look)
    starting = told.rendered if rendered and "." in rendered else told.version
    if owes(rendered=rendered, missed=missed, told=starting):
        yield refresh(told.version)
    while True:
        await anyio.sleep(TICK_SECONDS)
        now = await anyio.to_thread.run_sync(look)
        if now != told:
            told = now
            yield refresh(now.version)


async def endpoint(request: Request) -> Response:
    """The stream of this workspace, or its headers for HEAD."""
    space = place.workspace(request)
    if request.method == "HEAD":
        return Response(media_type=EVENTS)
    missed = "since" in request.query_params or "last-event-id" in request.headers
    look = partial(stamps.shown, request, space.state, space)
    told = refreshed(look, rendered=request.query_params.get("rendered"), missed=missed)
    return EventSourceResponse(
        told,
        ping=PING_SECONDS,
        ping_message_factory=pinged,
        headers={"Cache-Control": "no-store"},
    )
