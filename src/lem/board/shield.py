"""What stands between a request and the board: the one `Host` the main listener reads a
request for, and the page of a failure.

A request reaches the board only when it carries one `Host`, and that is a name of the main
listener's own: 127.0.0.1, localhost, [::1] or the address it listens on, with its port or
without (`serve.own_names` and `serve.host_refusal` on `main`). A page of another site whose
name the site points at this machine (DNS rebinding) carries that site's name, so the board's
files never reach that site's script; it gets a 403 that names the address to open.
"""

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse

from lem.kernel.errors import Fault

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.types import ASGIApp, ExceptionHandler, Receive, Scope, Send

LOOPBACK_NAMES = ("127.0.0.1", "localhost", "[::1]")


def own_names(port: int, listen: str) -> frozenset[str]:
    """The `Host` values of the main listener's own, each with its port and without it, in
    lower case."""
    address = listen.lower()
    if ":" in address:
        address = f"[{address}]"
    names = {*LOOPBACK_NAMES, address}
    return frozenset(names | {f"{name}:{port}" for name in names})


def host_refusal(seen: list[str], port: int, listen: str) -> str | None:
    """None when the request carries one `Host` of the listener's own, else the line of its
    403."""
    named = {word.strip().lower() for word in seen}
    if len(seen) != 1 or not named <= own_names(port, listen):
        return (
            "This address is not the board's own on this Mac: "
            f"open it as http://127.0.0.1:{port}/."
        )
    return None


class OwnHost:
    """The main listener's check of `Host`, before any route."""

    def __init__(self, app: ASGIApp, *, port: int, listen: str) -> None:
        """Keep the app, and the port and address the listener serves."""
        self.app = app
        self.port = port
        self.listen = listen

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Answer 403 to a request of another `Host`, and pass every other on."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        seen = [
            word.decode("latin-1") for name, word in scope["headers"] if name == b"host"
        ]
        refused = host_refusal(seen, self.port, self.listen)
        if refused is None:
            await self.app(scope, receive, send)
            return
        answer = PlainTextResponse(refused, status_code=HTTPStatus.FORBIDDEN)
        await answer(scope, receive, send)


def hosts(port: int, listen: str) -> list[Middleware]:
    """The check of `Host` for the listener on `listen:port`."""
    return [Middleware(OwnHost, port=port, listen=listen)]


def handlers() -> dict[Any, ExceptionHandler]:
    """The page of each failure the app answers itself: a `Fault` of Lem."""
    return {Fault: faulted}


async def faulted(request: Request, error: Exception) -> Response:
    """A page whose files did not read: what failed, in one line."""
    path = request.url.path
    said = f"the board could not read {path}: {error}"
    return PlainTextResponse(said, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
