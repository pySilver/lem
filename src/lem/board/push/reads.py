"""The board's notifications, read: their service worker at the root so that its scope is the
whole board, the machine's public key (made at first use), and what the worker shows for the
newest push (`Handler.push_read` on `main`). Each answers HEAD with its headers alone, as
Starlette answers HEAD for a GET.
"""

from http import HTTPStatus
from typing import TYPE_CHECKING

import msgspec
from starlette.responses import FileResponse, Response

from lem.adapters import notify_push_key as keys
from lem.board.push import listing
from lem.kernel import paths
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from starlette.requests import Request

JSON = "application/json"
NO_CACHE = "no-cache"


def json_of(body: object, status: int = HTTPStatus.OK) -> Response:
    """`body` as JSON, kept by no cache."""
    return Response(msgspec.json.encode(body), status_code=status, media_type=JSON)


async def worker(request: Request) -> Response:
    """The service worker, whose scope is the whole board."""
    path = paths.root() / "skills" / "lem" / "assets" / "sw.js"
    headers = {"Cache-Control": NO_CACHE, "Service-Worker-Allowed": "/"}
    return FileResponse(path, media_type="text/javascript", headers=headers)


async def key(request: Request) -> Response:
    """The machine's public key, made at first use."""
    try:
        made = keys.public_of(keys.key_of(request.app.state.home))
    except Refusal as refused:
        return json_of({"said": refused.why}, HTTPStatus.SERVICE_UNAVAILABLE)
    return json_of({"key": made})


async def latest(request: Request) -> Response:
    """What the worker shows for the newest push."""
    return json_of(listing.latest_of(request.app.state.home))
