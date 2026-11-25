"""HTTP for one browser question. Its page and answer share a private address."""

import secrets
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import TYPE_CHECKING, cast

from lem.cli.ask.answer import submitted

if TYPE_CHECKING:
    from lem.cli.ask.answer import Words

ADDRESS = "127.0.0.1"
LIMIT = 65536  # the answer bound for an ordinary question page, as on main
READ_SECONDS = 2  # unmeasured estimate for a local browser to send one answer


class BrowserPage(BaseHTTPRequestHandler):
    """Get this question and post its answer at its own route."""

    def do_GET(self) -> None:
        """Send the question page and clear a pending dismissal on reload."""
        board = cast("BrowserServer", self.server)
        if self.path != board.page:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        board.dismissed = None
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(board.html)))
        self.end_headers()
        self.wfile.write(board.html)

    def do_POST(self) -> None:
        """Keep one answer from the question's browser."""
        board = cast("BrowserServer", self.server)
        refusal = self.refused(board)
        if refusal is not None:
            self.send_error(refusal)
            return
        self.record(board)
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def refused(self, board: BrowserServer) -> HTTPStatus | None:
        """Refuse an answer sent to the wrong page or from another origin."""
        if self.path != f"{board.page}answer":
            return HTTPStatus.NOT_FOUND
        if self.headers.get("origin") != board.origin:
            return HTTPStatus.FORBIDDEN
        length = self.headers.get("content-length", "")
        if (
            not length.isdecimal()
            or len(length) > len(str(LIMIT))
            or int(length) > LIMIT
        ):
            return HTTPStatus.BAD_REQUEST
        return None

    def record(self, board: BrowserServer) -> None:
        """Read the answer, or give pagehide time to be a reload."""
        self.connection.settimeout(READ_SECONDS)
        length = int(self.headers["content-length"])
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        picked = submitted(raw)
        if picked.get("status") == "dismissed":
            board.dismissed = time.monotonic()
        else:
            board.answer = picked

    def log_message(self, *args: object, **details: object) -> None:
        """This private page writes no access log."""


class BrowserServer(HTTPServer):
    """The page and its answer. Each instance binds an unused loopback port."""

    def __init__(self, html: bytes) -> None:
        """Bind the private page for one question."""
        super().__init__((ADDRESS, 0), BrowserPage)
        port = self.server_port
        self.origin = f"http://{ADDRESS}:{port}"
        self.page = f"/{secrets.token_urlsafe()}/"
        self.address = self.origin + self.page
        self.html = html
        self.answer: Words | None = None
        self.dismissed: float | None = None
