"""Relay an owner's read of a joined board, with its stream closed at disconnect."""

from contextlib import AsyncExitStack
from http import HTTPStatus
from typing import TYPE_CHECKING

import httpx
from starlette.responses import PlainTextResponse, Response

from lem.addons.peers import requests, stream
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.types import Receive, Scope, Send

    from lem.addons.peers.look import Peer
    from lem.addons.peers.registry import Registry
    from lem.addons.peers.rows import Row

# Three old-board SSE pings and a margin (main, 2026-11-25).
STREAM_SILENCE = 35
CONNECT_SECONDS = 4
PAGE_SECONDS = 30


async def relay(
    request: Request,
    machine: Peer,
    registry: Registry,
    listed: tuple[Row, ...],
) -> Response:
    """Keep the linked host and path on the peer and pass only allowed headers."""
    try:
        base = await registry.address(machine.name, machine.port)
    except Refusal as error:
        machine.failed(error.why)
        return unavailable(machine.name)
    return forwarded(request, machine, registry, (base, listed))


def forwarded(
    request: Request,
    machine: Peer,
    registry: Registry,
    target: tuple[str, tuple[Row, ...]],
) -> Response:
    """Create the response whose lifetime owns the HTTP client."""
    base, listed = target
    url = httpx.URL(base).copy_with(raw_path=target_path(request))
    headers = requests.outgoing(dict(request.headers), listed)
    return Relay(
        machine=machine,
        registry=registry,
        outbound=httpx.Request(request.method, url, headers=headers),
    )


class Relay(Response):
    """Join the downstream and upstream lifetimes across an ASGI call."""

    def __init__(
        self, *, machine: Peer, registry: Registry, outbound: httpx.Request
    ) -> None:
        """Keep the target and the filtered request until the response is sent."""
        super().__init__()
        self.machine = machine
        self.registry = registry
        self.outbound = outbound

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Complete headers before sending, then stream until completion or disconnect."""
        timeout = httpx.Timeout(
            PAGE_SECONDS, connect=CONNECT_SECONDS, read=STREAM_SILENCE
        )
        async with self.registry.client(timeout) as client:
            try:
                upstream = await client.send(self.outbound, stream=True)
            except httpx.HTTPError as error:
                self.machine.failed(str(error))
                await unavailable(self.machine.name)(scope, receive, send)
                return
            async with AsyncExitStack() as stack:
                stack.push_async_callback(stream.close, upstream)
                downstream = stream.answer(upstream, self.outbound, self.machine.name)
                await downstream(scope, receive, send)


def target_path(request: Request) -> bytes:
    """Preserve percent escapes and the query, without accepting a different origin."""
    path = request.scope.get("raw_path") or request.url.path.encode()
    if isinstance(path, str):
        path = path.encode()
    query = request.scope["query_string"]
    return b"?".join((path, query)) if query else path


def unavailable(name: str) -> Response:
    """The board says the peer did not answer."""
    return PlainTextResponse(
        f"{name} is not reachable. The owner can see the boards that answer at /.",
        status_code=HTTPStatus.BAD_GATEWAY,
    )
