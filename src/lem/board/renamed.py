"""The machine's other name in an address, turned to its name before any route: a page's address
would take any first word as a machine's name (`serve.ALIASES` on `main`)."""

from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.responses import RedirectResponse

from lem.board.aliases import under

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send


class Aliased:
    """The redirect of an address under the machine's other name, before any route."""

    def __init__(self, app: ASGIApp, *, host: str, aliases: tuple[str, ...]) -> None:
        """Keep the app, the machine's name and its other names."""
        self.app = app
        self.host = host
        self.aliases = aliases

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Send a request under another name of the machine to the same page under its name."""
        path = scope.get("path", "/")
        first, _, rest = path[1:].partition("/")
        if scope["type"] != "http" or first not in self.aliases:
            await self.app(scope, receive, send)
            return
        query = scope.get("query_string", b"").decode("latin-1")
        moved = RedirectResponse(under(self.host, rest, query), HTTPStatus.FOUND)
        await moved(scope, receive, send)
