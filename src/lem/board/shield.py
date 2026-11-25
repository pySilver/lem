"""What stands between a request and the board: the check of the listener it came to, and the
page of a failure.

The main listener reads a request only when it carries one `Host`, a name of its own: 127.0.0.1,
localhost, [::1] or the address it listens on, with its port or without (`serve.own_names` and
`serve.host_refusal` on `main`). A page of another site whose name the site points at this
machine (DNS rebinding) carries that site's name, so the board's files never reach that site's
script; it gets a 403 that names the address to open. The door, the second listener, checks
every request against the owner's Tailscale login instead (`board/door.py`). One app serves
both: the port a request came to tells them apart.
"""

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse

from lem.board import door as doors
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


class Shield:
    """The check of the listener a request came to, before any route: the door's at the
    door's port, else the main listener's `Host`."""

    def __init__(
        self, app: ASGIApp, *, port: int, listen: str, door: doors.Door | None
    ) -> None:
        """Keep the app, the main listener's port and address, and the door, if open."""
        self.app = app
        self.port = port
        self.listen = listen
        self.door = door

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Answer 403 to a request the listener does not read, and pass every other on."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        refused = self.refusal(scope)
        if refused is None:
            await self.app(scope, receive, send)
            return
        answer = PlainTextResponse(refused, status_code=HTTPStatus.FORBIDDEN)
        await answer(scope, receive, send)

    def refusal(self, scope: Scope) -> str | None:
        """The line of the 403 of the request of `scope`, None when it is read."""
        headers = [
            (name.decode("latin-1"), word.decode("latin-1"))
            for name, word in scope["headers"]
        ]
        door = self.door
        if door is not None and scope["server"][1] == door.port:
            return door.refusal(doors.seen_of(headers), scope["method"])
        hosts = [word for name, word in headers if name == "host"]
        return host_refusal(hosts, self.port, self.listen)


def shields(port: int, listen: str, door: doors.Door | None) -> list[Middleware]:
    """The check of each listener: the main one on `listen:port`, and the door."""
    return [Middleware(Shield, port=port, listen=listen, door=door)]


def handlers() -> dict[Any, ExceptionHandler]:
    """The page of each failure the app answers itself: a `Fault` of Lem."""
    return {Fault: faulted}


async def faulted(request: Request, error: Exception) -> Response:
    """A page whose files did not read: what failed, in one line."""
    path = request.url.path
    said = f"the board could not read {path}: {error}"
    return PlainTextResponse(said, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
