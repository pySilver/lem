"""The board server in the foreground: uvicorn on one port of this machine until a stop,
SIGTERM or Ctrl-C, which end every stream first.

The socket is bound here before uvicorn starts, so that a port another program holds is a
refusal that names it, and the server's facts carry the port it holds. Its stop from
`POST /api/server/stop` is the same SIGTERM a `kill` sends, which uvicorn takes as a clean stop.
uvicorn raises that signal again once it stopped; the handler it then finds again is `Board`'s,
so that the command ends with its envelope and exit 0, and a signal before uvicorn's own handler
is set stops the server as soon as it started.
"""

import contextlib
import os
import signal
from typing import TYPE_CHECKING

import uvicorn

from lem.board import app, listening, opening
from lem.board.facts import Served
from lem.board.serving import Serving

if TYPE_CHECKING:
    from pathlib import Path
    from socket import socket
    from types import FrameType

    from starlette.types import ASGIApp

HOST = listening.HOST
# How long the stop waits for the answers that run, in seconds.
STOP_WAIT = 10


class Board(uvicorn.Server):
    """uvicorn's server, with the handler of the signals that stop it outside uvicorn's own."""

    def stop_by(self, sign: int, frame: FrameType | None) -> None:
        """Stop at the next look of uvicorn's loop; a stop that ended already is done."""
        self.should_exit = True

    def handle_signals(self) -> None:
        """Make `stop_by` the handler of SIGINT and SIGTERM."""
        for sign in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sign, self.stop_by)


def run(port: int, host: str = HOST, *, verbose: bool, home: Path) -> Served:
    """Serve the board on `host:port`, and the door when the settings open it, until the
    server stops."""
    opening.detached(os.environ)
    door = opening.door_of(home, os.environ, port)
    held = listening.sockets(host, port, door)
    facts = opening.facts_of(held[0], host, home, door)
    serving = Serving(
        home=home,
        environ=os.environ,
        listen=host,
        stop=listening.stop_of(facts.pid),
        door=door,
    )
    board = app.made(facts, serving)
    served(Board(config_of(board, verbose=verbose)), held)
    return Served(pid=facts.pid, port=facts.port, url=facts.url)


def config_of(board: ASGIApp, *, verbose: bool) -> uvicorn.Config:
    """uvicorn's settings for the board's app."""
    return uvicorn.Config(
        board,
        http="h11",
        ws="none",
        loop="asyncio",
        lifespan="on",
        log_level="info" if verbose else "warning",
        access_log=verbose,
        server_header=False,
        proxy_headers=False,
        timeout_graceful_shutdown=STOP_WAIT,
    )


def served(server: Board, held: list[socket]) -> None:
    """Serve on the sockets until the server stops, and close them."""
    server.handle_signals()
    with contextlib.ExitStack() as stack:
        for sock in held:
            stack.enter_context(sock)
        server.run(sockets=held)
