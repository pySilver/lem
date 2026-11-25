"""Stream a peer's response and keep its disconnect listener beside it."""

from typing import TYPE_CHECKING

import anyio
from starlette.responses import Response, StreamingResponse

from lem.addons.peers import requests

if TYPE_CHECKING:
    import httpx
    from starlette.types import Receive, Scope, Send


class Stream(StreamingResponse):
    """Close the upstream when the ASGI client disconnects or the server cancels."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Race the stream against the HTTP disconnect message."""
        async with anyio.create_task_group() as group:
            group.start_soon(stream_to, self, send, group)
            await self.listen_for_disconnect(receive)
            group.cancel_scope.cancel()


async def stream_to(stream: Stream, send: Send, group: anyio.abc.TaskGroup) -> None:
    """End the disconnect listener when the peer ends its response."""
    await stream.stream_response(send)
    group.cancel_scope.cancel()


def answer(upstream: httpx.Response, outbound: httpx.Request, name: str) -> Response:
    """Relay bytes and headers, omitting a body for HEAD."""
    response = (
        Response(status_code=upstream.status_code)
        if outbound.method == "HEAD"
        else Stream(upstream.aiter_bytes(), status_code=upstream.status_code)
    )
    base = str(outbound.url.copy_with(path="", query=None))
    for key, text in upstream.headers.multi_items():
        passed = requests.returned(key, text, name, base)
        if passed is not None:
            response.headers.append(key, passed)
    if outbound.method == "HEAD" and "content-length" in upstream.headers:
        response.headers["content-length"] = upstream.headers["content-length"]
    return response


async def close(upstream: httpx.Response) -> None:
    """Close the upstream body even if the downstream connection has ended."""
    with anyio.CancelScope(shield=True):
        await upstream.aclose()
