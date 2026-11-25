"""`lem serve stop`: the end of the board server of this install and home folder.

It reads first its port and who serves there; a server of another install, or none, changes
nothing. Only then it takes the serve lock, reads the port again under it, and sends the stop on
the connection that asked who serves.
"""

import os
from typing import TYPE_CHECKING

from lem.board import client, halt, heard, install, lock, machine
from lem.board.facts import Facts, Stopped
from lem.kernel import paths

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


def mine() -> str:
    """The package folder of this install."""
    return install.install_of().package


def left(found: Facts | heard.Other) -> Stopped:
    """What `stop` says of a server of another install, which it leaves as it is."""
    served = found.install
    said = (
        f"another install of Lem serves: release {served.version} from {served.package}"
    )
    return Stopped(stopped=False, pid=found.pid, version=served.version, said=said)


def stop(environ: Mapping[str, str] = os.environ) -> Stopped:
    """End the board server of this install and home folder, if one runs on its port; a
    server of another install is left as it is."""
    home = paths.home(environ)
    port = machine.port_of(home, environ)
    found = client.ask(port, home)
    if found is None:
        return Stopped(stopped=False, said=f"no board server runs on port {port}")
    if isinstance(found, heard.Other) or found.install.package != mine():
        return left(found)
    with lock.serve_lock(home):
        return stop_held(home, environ)


def stop_held(home: Path, environ: Mapping[str, str]) -> Stopped:
    """`stop` with the serve lock held: the port read again, and the stop on the connection
    that asked who serves."""
    port = machine.port_of(home, environ)
    with client.opened(port) as connection:
        found = client.looked(connection, port, home)
        if not isinstance(found, Facts) or found.install.package != mine():
            return Stopped(
                stopped=False, said=f"no board server of this install on {port}"
            )
        if connection is None:
            return Stopped(stopped=False, said=f"no board server runs on port {port}")
        halt.stopped(connection, port, found)
    return Stopped(stopped=True, pid=found.pid, version=found.install.version)
