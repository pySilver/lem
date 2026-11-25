"""The question a command asks the board server on the loopback address: who serves a port,
on a connection that a stop (`halt.py`) may use next. What answered is judged by
`heard.judged`.
"""

from contextlib import ExitStack, contextmanager
from http.client import HTTPConnection, HTTPException
from typing import TYPE_CHECKING

import msgspec

from lem.board import heard
from lem.board.facts import HEADER, Facts
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

LOOPBACK = "127.0.0.1"
# How long a question waits for its answer, in seconds.
ASK_WAIT = 2.0
SERVER = "/api/server"


class Reply(msgspec.Struct, frozen=True, kw_only=True):
    """An answer of the port: its status, the server's own marker, its `Server` header and
    its body."""

    status: int
    marker: str
    server: str
    body: bytes


def silent(port: int, error: Exception) -> Refusal:
    """The refusal of a port that takes connections and gives no answer."""
    return Refusal(
        "port-held",
        f"port {port} on {LOOPBACK} takes connections and gave no answer ({error})",
        f"end the program that holds it (lsof -nP -iTCP:{port} -sTCP:LISTEN names it), "
        "or name another port",
    )


def asked(connection: HTTPConnection, method: str, path: str) -> Reply:
    """Ask `method path` on the connection, and read the whole answer."""
    connection.request(method, path)
    answer = connection.getresponse()
    return Reply(
        status=answer.status,
        marker=answer.getheader(HEADER) or "",
        server=answer.getheader("Server") or "",
        body=answer.read(),
    )


def connected(port: int) -> HTTPConnection | None:
    """A connection to the port, or None when nothing listens there."""
    connection = HTTPConnection(LOOPBACK, port, timeout=ASK_WAIT)
    try:
        connection.connect()
    except ConnectionRefusedError:
        return None
    except OSError as error:
        raise silent(port, error) from error
    return connection


@contextmanager
def opened(port: int) -> Iterator[HTTPConnection | None]:
    """One connection to the port while the block runs, or None when nothing listens."""
    connection = connected(port)
    with ExitStack() as stack:
        if connection is not None:
            stack.callback(connection.close)
        yield connection


def looked(
    connection: HTTPConnection | None, port: int, home: Path
) -> Facts | heard.Other | None:
    """Who serves the port, asked on `connection`: None when nothing listens."""
    if connection is None:
        return None
    try:
        reply = asked(connection, "GET", SERVER)
    except (OSError, HTTPException) as error:
        raise silent(port, error) from error
    return heard.judged(reply, port=port, home=home)


def ask(port: int, home: Path) -> Facts | heard.Other | None:
    """Who serves the port, on a connection of its own: None when nothing listens."""
    with opened(port) as connection:
        return looked(connection, port, home)
