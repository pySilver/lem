"""What a server opens at its start, besides its main socket: the tailnet door when the machine's
settings say `serve.tailscale = true`, with its own socket on 127.0.0.1 and its entry in
`tailscale serve`, and the machine's names in the board's addresses (`serve.listen` on `main`).

A server started from a task's session leaves that session first (`detach_from_session` on
`main`): `lem session`, which its duties run, reads agterm's variables as its caller's place,
and the server is no part of any session.
"""

import os
import re
import sys
from typing import TYPE_CHECKING

from lem.board import install, machine, publish, tailnet, tailscale
from lem.board.door import Door
from lem.board.facts import Facts
from lem.kernel import clock, errors
from lem.settings.checked import serve_ports

if TYPE_CHECKING:
    import socket
    from collections.abc import Mapping, MutableMapping
    from pathlib import Path

# The variables of the session a server was started from: agterm's, its short names, and a
# task's `LEM_TASK` (`serve.SESSION_VARIABLES` on `main`).
SESSION = re.compile(r"AGTERM_\w+|AGT_(SESSION_ID|SOCKET|WINDOW_ID)|LEM_TASK")


def detached(environ: MutableMapping[str, str]) -> None:
    """Drop the variables of the session the server was started from."""
    for name in tuple(filter(SESSION.fullmatch, environ)):
        environ.pop(name)


def login_now(cli: str, before: str) -> str:
    """The owner's login read again; the one before, with a line in the log, when the CLI
    does not answer."""
    try:
        return tailnet.facts(tailnet.status(cli))[1]
    except errors.Refusal as refused:
        sys.stderr.write(
            f"the door: the owner's login was not read again: {refused.why}\n"
        )
        return before


def checked_door_port(port: int, door: int, environ: Mapping[str, str]) -> int:
    """Both listeners need distinct ports that this home may use."""
    serve_ports(port, door)
    machine.guarded(port, environ)
    return machine.guarded(door, environ)


def door_of(home: Path, environ: MutableMapping[str, str], port: int) -> Door | None:
    """The door the machine's settings open, None when they keep it closed; refused when it
    cannot open, with the main listener's port named."""
    settings = machine.settings(home)
    if not settings.tailscale:
        return None
    door_port = checked_door_port(port, settings.tailscale_port, environ)
    cli = tailscale.needed(environ)
    name, login = tailnet.facts(tailnet.status(cli))
    return Door(
        name=name,
        port=door_port,
        owner=login,
        reread=lambda before: login_now(cli, before),
    )


def published(door: Door, environ: MutableMapping[str, str]) -> str:
    """The door's entry in `tailscale serve`: kept or published."""
    return publish.publish(tailscale.needed(environ), door.name, door.port)


def names(
    door: Door | None, environ: MutableMapping[str, str]
) -> tuple[str, tuple[str, ...]]:
    """The machine's name in the board's addresses and its other name."""
    found = tailnet.name_of(environ) if door is None else door.name
    return machine.names_of(found)


def facts_of(sock: socket.socket, host: str, home: Path, door: Door | None) -> Facts:
    """The facts of the server that serves `sock`, and the door when it is open."""
    port = sock.getsockname()[1]
    name, aliases = names(door, os.environ)
    authority = f"[{host}]" if ":" in host else host
    return Facts(
        pid=os.getpid(),
        port=port,
        url=f"http://{authority}:{port}/",
        host=name,
        aliases=aliases,
        install=install.install_of(),
        home=str(home),
        door=None if door is None else door.port,
        tailnet=None if door is None else door.url(),
        started=clock.now(),
    )
