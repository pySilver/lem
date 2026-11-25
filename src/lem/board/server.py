"""The board server in the foreground: uvicorn on one port of this machine until a stop,
SIGTERM or Ctrl-C, which end every stream first.

The socket is bound here before uvicorn starts, so that a port another program holds is a
refusal that names it, and the server's facts carry the port it holds. Its stop from
`POST /api/server/stop` is the same SIGTERM a `kill` sends, which uvicorn takes as a clean stop.
uvicorn raises that signal again once it stopped; the handler it then finds again is `Board`'s,
so that the command ends with its envelope and exit 0, and a signal before uvicorn's own handler
is set stops the server as soon as it started.
"""

import os
import signal
import socket
from functools import partial
from typing import TYPE_CHECKING

import uvicorn

from lem.board import app, install, machine
from lem.board.facts import Facts, Served
from lem.kernel import clock
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path
    from types import FrameType

HOST = "127.0.0.1"
# How long the stop waits for the answers that run, in seconds.
STOP_WAIT = 10


class Board(uvicorn.Server):
    """uvicorn's server, with the handler of the signals that stop it outside uvicorn's own."""

    def stop_by(self, sign: int, frame: FrameType | None) -> None:
        """Stop at the next look of uvicorn's loop; a stop that ended already is done."""
        self.should_exit = True


def bound(host: str, port: int) -> socket.socket:
    """A socket bound to the address; refused when another program holds it."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, port))
    except OSError as error:
        sock.close()
        raise Refusal(
            "port-held",
            f"{host}:{port} cannot be served ({error.strerror})",
            f"end the program that holds it (lsof -nP -iTCP:{port} -sTCP:LISTEN names "
            "it), or name another port: lem serve run --port N",
        ) from error
    return sock


def described(sock: socket.socket, host: str, home: Path) -> Facts:
    """The facts of the server that serves `sock`."""
    port = sock.getsockname()[1]
    return Facts(
        pid=os.getpid(),
        port=port,
        url=f"http://{host}:{port}/",
        host=machine.machine_name(),
        install=install.install_of(),
        home=str(home),
        started=clock.now(),
    )


def run(port: int, host: str = HOST, *, verbose: bool, home: Path) -> Served:
    """Serve the board on `host:port` until the server stops."""
    sock = bound(host, port)
    facts = described(sock, host, home)
    board = app.made(
        facts,
        home=home,
        listen=host,
        stop=partial(os.kill, facts.pid, signal.SIGTERM),
    )
    config = uvicorn.Config(
        board,
        http="h11",
        ws="none",
        loop="asyncio",
        lifespan="on",
        log_level="info" if verbose else "warning",
        access_log=verbose,
        server_header=False,
        timeout_graceful_shutdown=STOP_WAIT,
    )
    server = Board(config)
    for sign in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sign, server.stop_by)
    with sock:
        server.run(sockets=[sock])
    return Served(pid=facts.pid, port=facts.port, url=facts.url)
