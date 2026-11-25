"""`GET /HOST/WORKSPACE/stream`: server-sent events that tell an open page its workspace
changed, so that it fetches itself again (`tools/board-kit/controllers/stream.js`).

At each tick of TICK seconds the stream looks at every file the pages read (`watched.look`: the
records, the owner's mark, the settings, the demo mark, the forge's look, the Inbox's record, the
reviewer's items, and with `?task=SLUG` that task's files) and, when the look moved, sends one
message: Turbo's `refresh`, the default event, its id the digest of the watched files.
It polls: a burst of writes in
one tick is one message (`serve.WATCH_SECONDS` on `main`). A page's open after a render
names the version it shows (`?rendered=`) and gets a refresh at once only when the files moved
since; an open after it may have missed one (`?since=`, or the browser's `Last-Event-ID`) gets
one at once. A quiet stream sends a `ping` event every PING_SECONDS, by which the page tells a
live stream from a dead one. The server's stop ends every stream (sse-starlette).
"""

from typing import TYPE_CHECKING

import anyio
from sse_starlette import EventSourceResponse, ServerSentEvent
from starlette.responses import Response

from lem.board import watched
from lem.board.pages import place
from lem.store import places

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from pathlib import Path

    from starlette.requests import Request

TICK = 0.5
PING_SECONDS = 10
REFRESH = '<turbo-stream action="refresh"></turbo-stream>'
EVENTS = "text/event-stream"


def owes(*, rendered: str | None, missed: bool, told: str) -> bool:
    """Whether an open gets a refresh at once: it may have missed a change, or it names a
    version the files left."""
    return missed or bool(rendered and rendered != told)


def refresh(told: str) -> ServerSentEvent:
    """One message of the stream: Turbo's `refresh`, its id the version."""
    return ServerSentEvent(data=REFRESH, id=told)


async def events(
    state: Path,
    *,
    rendered: str | None,
    missed: bool,
    home: Path,
    task: str | None = None,
) -> AsyncGenerator[ServerSentEvent]:
    """The stream's messages: a refresh at the open when one is owed, then one each time a
    file the pages read moved."""
    seen = await anyio.to_thread.run_sync(watched.look, state, home, task)
    if owes(rendered=rendered, missed=missed, told=seen):
        yield refresh(seen)
    while True:
        await anyio.sleep(TICK)
        now = await anyio.to_thread.run_sync(watched.look, state, home, task)
        if now != seen:
            seen = now
            yield refresh(now)


async def endpoint(request: Request) -> Response:
    """The stream of the workspace of the request's address; to HEAD, its headers alone."""
    space = place.workspace(request)
    if request.method == "HEAD":
        return Response(media_type=EVENTS)
    state = places.state_of(space.checkout)
    missed = "since" in request.query_params or "last-event-id" in request.headers
    told = events(
        state,
        rendered=request.query_params.get("rendered"),
        missed=missed,
        home=request.app.state.home,
        task=request.query_params.get("task"),
    )
    return EventSourceResponse(
        told,
        ping=PING_SECONDS,
        ping_message_factory=pinged,
    )


def pinged() -> ServerSentEvent:
    """The sign of life of a quiet stream: a `ping` event, which the page hears and Turbo
    does not render."""
    return ServerSentEvent(event="ping", data="ping")
