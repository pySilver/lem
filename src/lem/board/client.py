"""The questions a command asks the board server on the loopback address: who serves a port,
and its stop.

A port that answers as no board server of this home folder is refused, never stopped: the owner's
server of another release, or of another home folder, answers without the header `Lem-Server` or
with its own home, and so stays as it is.
"""

import contextlib
import time
from http import HTTPStatus
from http.client import HTTPConnection, HTTPException
from typing import TYPE_CHECKING

import msgspec

from lem.board.facts import HEADER, Facts
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

LOOPBACK = "127.0.0.1"
# How long a question waits for its answer, in seconds, and the most of an answer it reads.
ASK_WAIT = 2.0
LIMIT = 65536
# How long a stopped server may take to free its port, and how often that is looked at.
STOP_WAIT = 10.0
POLL = 0.1
SERVER = "/api/server"


class Reply(msgspec.Struct, frozen=True, kw_only=True):
    """An answer of the port: its status, the server's own header, and its body."""

    status: int
    server: str
    body: bytes


def exchange(port: int, method: str, path: str) -> Reply:
    """Ask `method path` of the port, and read the answer."""
    connection = HTTPConnection(LOOPBACK, port, timeout=ASK_WAIT)
    with contextlib.closing(connection):
        connection.request(method, path)
        answer = connection.getresponse()
        return Reply(
            status=answer.status,
            server=answer.getheader(HEADER) or "",
            body=answer.read(LIMIT),
        )


def answered(port: int, method: str, path: str) -> Reply | None:
    """The answer of the port, or None when nothing listens there."""
    try:
        return exchange(port, method, path)
    except ConnectionRefusedError:
        return None
    except (OSError, HTTPException) as error:
        raise Refusal(
            "port-held",
            f"port {port} on {LOOPBACK} takes connections and gave no answer ({error})",
            f"end the program that holds it (lsof -nP -iTCP:{port} -sTCP:LISTEN names "
            "it), or name another port",
        ) from error


def ask(port: int, home: Path) -> Facts | None:
    """Who serves the port: the board server of this home folder, or None when nothing
    listens; anything else there is refused."""
    reply = answered(port, "GET", SERVER)
    if reply is None:
        return None
    try:
        facts = msgspec.json.decode(reply.body, type=Facts)
    except msgspec.DecodeError:
        facts = None
    if facts is None or not reply.server:
        raise Refusal(
            "port-held",
            f"port {port} on {LOOPBACK} is held by a program that does not answer {SERVER} "
            "as Lem's board server",
            f"end it (lsof -nP -iTCP:{port} -sTCP:LISTEN names it), or name another port",
        )
    if facts.home != str(home):
        raise Refusal(
            "other-home",
            f"port {port} is held by the board server (pid {facts.pid}) of another home "
            f"folder of Lem, {facts.home}; this one is {home}",
            "name another port for this home folder",
        )
    return facts


def stop(port: int, home: Path, facts: Facts) -> None:
    """Ask the server on the port to end, and wait until its port is free."""
    reply = answered(port, "POST", f"{SERVER}/stop")
    if reply is not None and reply.status != HTTPStatus.OK:
        said = reply.body.decode(errors="replace")
        raise Refusal(
            "stop-refused",
            f"the board server (pid {facts.pid}) refused the stop: {said}",
            f"end it with kill {facts.pid}, then run this again",
        )
    deadline = time.monotonic() + STOP_WAIT
    while ask(port, home) is not None:
        if time.monotonic() > deadline:
            raise Refusal(
                "stop-late",
                f"the board server (pid {facts.pid}) did not end in {STOP_WAIT:g} s",
                f"end it with kill {facts.pid}, then run this again",
            )
        time.sleep(POLL)
