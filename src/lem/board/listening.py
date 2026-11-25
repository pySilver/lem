"""The server's sockets, bound before uvicorn starts, so that a port another program holds is a
refusal that names it: the main listener's, and the door's on 127.0.0.1 with its entry in
`tailscale serve` when the door is open; and the server's stop, the SIGTERM a `kill` sends."""

import contextlib
import os
import signal
import socket
from functools import partial
from typing import TYPE_CHECKING

from lem.board import opening
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.board.door import Door

HOST = "127.0.0.1"


def bound(host: str, port: int) -> socket.socket:
    """A socket bound to the address; refused when another program holds it."""
    try:
        with contextlib.ExitStack() as stack:
            address = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)[0]
            sock = stack.enter_context(socket.socket(address[0], socket.SOCK_STREAM))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(address[4])
            stack.pop_all()
    except OSError as error:
        raise Refusal(
            "port-held",
            f"{host}:{port} cannot be served ({error.strerror})",
            f"end the program that holds it (lsof -nP -iTCP:{port} -sTCP:LISTEN names "
            "it), or name another port: lem serve run --port N",
        ) from error
    return sock


def sockets(host: str, port: int, door: Door | None) -> list[socket.socket]:
    """The main listener's socket, and the door's when it is open, with its entry in
    `tailscale serve`."""
    held = [bound(host, port)]
    if door is not None:
        held.append(bound(HOST, door.port))
        opening.published(door, os.environ)
    return held


def stop_of(pid: int) -> Callable[[], None]:
    """The stop of the server of `pid`: SIGTERM, which uvicorn takes as a clean stop."""
    return partial(os.kill, pid, signal.SIGTERM)
