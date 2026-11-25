"""`GET /HOST/WORKSPACE/stream`: server-sent events that tell an open page its workspace
changed, so that it fetches itself again (`tools/board-kit/controllers/stream.js`).

watchfiles watches the workspace's state folder; at each change, and at each tick of TICK_MS in
case a change came before the watch began, the stream reads the version of the records (a digest
of each `tasks/*/task.json`'s name, inode, size and change time) and, when it moved, sends one
message: Turbo's `refresh`, the default event, its id the version. A page's open after a render
names the version it shows (`?rendered=`) and gets a refresh at once only when the records moved
since; an open after it may have missed one (`?since=`, or the browser's `Last-Event-ID`) gets
one at once. A quiet stream sends a `ping` event every PING_SECONDS, by which the page tells a
live stream from a dead one. The server's stop ends every stream (sse-starlette).
"""

import contextlib
import hashlib
from typing import TYPE_CHECKING

import anyio
from sse_starlette import EventSourceResponse, ServerSentEvent
from watchfiles import awatch

from lem.board.pages import place
from lem.store import places

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from pathlib import Path

    from starlette.requests import Request

TICK_MS = 500
PING_SECONDS = 10
REFRESH = '<turbo-stream action="refresh"></turbo-stream>'
RECORDS = "tasks/*/task.json"
# The hex digits of a version: enough that two versions of one folder never meet.
DIGITS = 16

type Stamp = tuple[str, int, int, int]


def stamped(path: Path) -> Stamp | None:
    """A record's name, inode, size and change time; None when it went meanwhile."""
    with contextlib.suppress(FileNotFoundError):
        facts = path.stat()
        return (path.parent.name, facts.st_ino, facts.st_size, facts.st_mtime_ns)
    return None


def version(state: Path) -> str:
    """The version of the records of the state folder `state`: it moves at each write."""
    stamps = sorted(filter(None, map(stamped, state.glob(RECORDS))))
    return hashlib.sha256(repr(stamps).encode()).hexdigest()[:DIGITS]


def owes(*, rendered: str | None, missed: bool, told: str) -> bool:
    """Whether an open gets a refresh at once: it may have missed a change, or it names a
    version the records left."""
    return missed or bool(rendered and rendered != told)


def refresh(told: str) -> ServerSentEvent:
    """One message of the stream: Turbo's `refresh`, its id the version."""
    return ServerSentEvent(data=REFRESH, id=told)


async def events(
    state: Path, *, rendered: str | None, missed: bool
) -> AsyncGenerator[ServerSentEvent]:
    """The stream's messages: a refresh at the open when one is owed, then one each time the
    records moved."""
    told = await anyio.to_thread.run_sync(version, state)
    if owes(rendered=rendered, missed=missed, told=told):
        yield refresh(told)
    stopping = anyio.Event()
    watched = awatch(
        state,
        stop_event=stopping,
        rust_timeout=TICK_MS,
        yield_on_timeout=True,
        debounce=TICK_MS,
    )
    with contextlib.ExitStack() as stack:
        stack.callback(stopping.set)
        async for _ in watched:
            now = await anyio.to_thread.run_sync(version, state)
            if now != told:
                told = now
                yield refresh(now)


async def endpoint(request: Request) -> EventSourceResponse:
    """The stream of the workspace of the request's address."""
    space = place.workspace(request)
    state = places.state_of(space.checkout)
    missed = "since" in request.query_params or "last-event-id" in request.headers
    told = events(state, rendered=request.query_params.get("rendered"), missed=missed)
    return EventSourceResponse(
        told,
        ping=PING_SECONDS,
        ping_message_factory=pinged,
    )


def pinged() -> ServerSentEvent:
    """The sign of life of a quiet stream: a `ping` event, which the page hears and Turbo
    does not render."""
    return ServerSentEvent(event="ping", data="ping")
