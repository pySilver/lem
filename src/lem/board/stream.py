"""The workspace's version and the SSE stream that tells its page to read again."""

from functools import partial
from typing import TYPE_CHECKING

import anyio
from sse_starlette import EventSourceResponse, ServerSentEvent
from starlette.responses import Response

from lem.board.pages import place, source, stamps

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable
    from pathlib import Path

    from starlette.requests import Request

TICK_SECONDS = 0.5
PING_SECONDS = 10
REFRESH = '<turbo-stream action="refresh"></turbo-stream>'
EVENTS = "text/event-stream"


def version(state: Path) -> str:
    """The version of the task records of this workspace."""
    return stamps.digest(state.glob(stamps.RECORDS))


def owes(*, rendered: str | None, missed: bool, told: str) -> bool:
    """Whether the page could have missed a change."""
    return missed or bool(rendered and rendered != told)


def refresh(told: str) -> ServerSentEvent:
    """One Turbo refresh, with the version as its event ID."""
    return ServerSentEvent(data=REFRESH, id=told)


def pinged() -> ServerSentEvent:
    """The sign of life of a quiet stream."""
    return ServerSentEvent(event="ping", data="ping")


async def events(
    state: Path, *, rendered: str | None, missed: bool
) -> AsyncGenerator[ServerSentEvent]:
    """The record changes of a workspace."""
    look = partial(version, state)
    async for message in refreshed(look, rendered=rendered, missed=missed):
        yield message


async def refreshed(
    look: Callable[[], str], *, rendered: str | None, missed: bool
) -> AsyncGenerator[ServerSentEvent]:
    """Read a version again after each poll and refresh when it moves."""
    told = await anyio.to_thread.run_sync(look)
    if owes(rendered=rendered, missed=missed, told=told):
        yield refresh(told)
    while True:
        await anyio.sleep(TICK_SECONDS)
        now = await anyio.to_thread.run_sync(look)
        if now != told:
            told = now
            yield refresh(now)


async def endpoint(request: Request) -> Response:
    """The stream of this workspace, or its headers for HEAD."""
    space = place.workspace(request)
    if request.method == "HEAD":
        return Response(media_type=EVENTS)
    missed = "since" in request.query_params or "last-event-id" in request.headers
    look = partial(version, space.state)
    if source.provided(request) is not None:
        look = partial(stamps.shown, request, space.state)
    told = refreshed(look, rendered=request.query_params.get("rendered"), missed=missed)
    return EventSourceResponse(
        told,
        ping=PING_SECONDS,
        ping_message_factory=pinged,
        headers={"Cache-Control": "no-store"},
    )
