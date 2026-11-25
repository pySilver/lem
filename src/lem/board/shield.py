"""What stands between a request and the board: the names it may give the server by, and the
page of a failure."""

from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import PlainTextResponse

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response

# The names of this machine a request may give in `Host`, beside the address it listens on.
OWN_NAMES = ("127.0.0.1", "localhost")


def hosts(listen: str) -> list[Middleware]:
    """Only a request that names this machine by its own address reaches the board, so that
    a page of another site that points its own name here reads nothing."""
    return [Middleware(TrustedHostMiddleware, allowed_hosts=[*OWN_NAMES, listen])]


async def faulted(request: Request, error: Exception) -> Response:
    """A page whose files did not read: what failed, in one line."""
    path = request.url.path
    said = f"the board could not read {path}: {error}"
    return PlainTextResponse(said, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
