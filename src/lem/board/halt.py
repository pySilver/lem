"""The stop of the board server: sent on the one connection that asked who serves, so that it
reaches the server that answered as this build's server of this home folder and no other (a
connection the server closed after its answer is no connection to stop on, and nothing is
sent), and the wait until its port and home claim are free."""

import socket
import time
from http import HTTPStatus
from http.client import HTTPConnection, HTTPException
from pathlib import Path
from typing import TYPE_CHECKING

from lem.board import claim, client
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.board.facts import Facts

# How long a stopped server may take to free its port, and how often that is looked at.
STOP_WAIT = 10.0
POLL = 0.1


def stopped(connection: HTTPConnection, port: int, facts: Facts) -> None:
    """Send the stop on the connection that asked who serves, and require its yes."""
    fix = f"end it with kill {facts.pid}, then run this again"
    if connection.sock is None:
        raise Refusal(
            "stop-refused",
            f"the board server (pid {facts.pid}) closed the connection it answered on, "
            "so no stop was sent",
            "run this again",
        )
    try:
        reply = client.asked(connection, "POST", f"{client.SERVER}/stop")
    except (OSError, HTTPException) as error:
        raise Refusal(
            "stop-refused", f"the stop got no answer ({error})", fix
        ) from error
    if reply.status != HTTPStatus.OK:
        said = reply.body.decode(errors="replace")
        why = f"the board server (pid {facts.pid}) refused the stop: {said}"
        raise Refusal("stop-refused", why, fix)
    gone(port, facts, connection.host)


def free(port: int, host: str) -> bool:
    """Whether nothing listens on the port: a connection is refused. A server that ends may
    still take a connection and reset it, which is not free yet."""
    try:
        socket.create_connection((host, port), timeout=client.ASK_WAIT).close()
    except ConnectionRefusedError:
        return True
    except OSError:
        return False
    return False


def gone(port: int, facts: Facts, host: str) -> None:
    """Wait for the server to close its listener and release its home claim."""
    deadline = time.monotonic() + STOP_WAIT
    home = Path(facts.home)
    while not free(port, host) or not claim.released(home):
        if time.monotonic() > deadline:
            raise Refusal(
                "stop-late",
                f"the board server (pid {facts.pid}) did not end in {STOP_WAIT:g} s",
                f"end it with kill {facts.pid}, then run this again",
            )
        time.sleep(POLL)
