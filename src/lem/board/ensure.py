"""`lem serve ensure`: one board server for this machine.

It reads first where its home folder is, its port and who serves there; then decides; and only
then takes the serve lock, reads the port again under it, and acts: a stop goes on the
connection that asked who serves. A server of another install that this one does not replace
(the release before this one always) is left as it is with every file of the home folder, and
the outcome says which install serves. A server whose install an update replaced
(`replaced.stale`) is replaced whatever its release. `LEM_SERVE=off` makes `ensure` start
nothing, end nothing and write nothing: a test sets it, and a test that starts a server on
purpose leaves it out for that one call.
"""

from typing import TYPE_CHECKING

from lem.board import (
    addresses,
    client,
    heard,
    install,
    lock,
    machine,
    start,
    workspaces,
)
from lem.board.facts import Facts, Shown
from lem.board.halt import stopped
from lem.board.replaced import stale
from lem.board.update import swapped
from lem.kernel import paths

if TYPE_CHECKING:
    from collections.abc import Mapping
    from http.client import HTTPConnection
    from pathlib import Path

NO_START = "off"
type Found = Facts | heard.Other | None


def shown(found: Found, *, started: bool, said: str | None = None) -> Shown:
    """What `ensure` prints of the server that runs, or of none."""
    if found is None:
        return Shown(running=False, started=False, said=said)
    if isinstance(found, heard.Other):
        return Shown(
            running=True,
            started=False,
            pid=found.pid,
            url=found.url,
            install=found.install,
            said=heard.which(found),
            another_install=True,
        )
    return Shown(
        running=True,
        started=started,
        pid=found.pid,
        url=found.url,
        host=found.host,
        tailnet=found.tailnet,
        install=found.install,
        said=said,
    )


def kept(found: Found, door: int | None, *, moved: bool = False) -> Shown | None:
    """The outcome when the server that runs stays, else None: this install replaces it."""
    if found is None:
        return None
    if isinstance(found, heard.Other):
        return shown(found, started=False)
    if stale(found) is not None:
        return None
    mine = install.install_of()
    differ = moved or found.door != door
    if install.replaces(mine, found.install, settings_differ=differ):
        return None
    said = None if found.install == mine else "another install of Lem serves"
    return shown(found, started=False, said=said)


def rebound(
    home: Path,
    target: addresses.Address,
    door: int | None,
    environ: Mapping[str, str],
) -> Shown | None:
    """Keep or stop a server of this home folder at another address."""
    named = addresses.recorded(home, environ)
    if named is None or named == target:
        return None
    port = named[1]
    with client.opened(port, named[0]) as connection:
        try:
            found = client.looked(connection, port, home)
        except heard.Unrelated:
            return None
        stays = kept(found, door, moved=port != target[1])
        if stays is not None:
            return stays
        if isinstance(found, Facts) and connection is not None:
            replaced(connection, port, found, home)
    return None


def held(home: Path, environ: Mapping[str, str], folder: Path) -> Shown:
    """Check both ports under the serve lock, before any server stops."""
    settings = machine.settings(home)
    port = machine.guarded(settings.port, environ)
    door = None
    if settings.tailscale:
        door = machine.guarded(settings.tailscale_port, environ)
    stays = kept(addresses.alternate(home, environ, port), door)
    if stays is not None:
        if not stays.another_install:
            workspaces.noted(home, folder)
        return stays
    return managed(home, environ, folder, port, door)


def managed(
    home: Path,
    environ: Mapping[str, str],
    folder: Path,
    port: int,
    door: int | None,
) -> Shown:
    """After the ports check, keep or replace the server of this home folder."""
    with client.opened(port) as connection:
        found = client.looked(connection, port, home)
        stays = kept(found, door) or rebound(
            home, (client.LOOPBACK, port), door, environ
        )
        if stays is not None:
            if not stays.another_install:
                workspaces.noted(home, folder)
            return stays
        if isinstance(found, Facts) and connection is not None:
            replaced(connection, port, found, home)
    facts = start.started(port, home, environ)
    workspaces.noted(home, folder)
    return shown(facts, started=True)


def replaced(connection: HTTPConnection, port: int, found: Facts, home: Path) -> None:
    """Stop the replaced server and leave its release for the new server's notice."""
    stopped(connection, port, found)
    swapped(home, found.install.version)


def ensure(environ: Mapping[str, str], folder: Path) -> Shown:
    """Make sure one board server runs for this machine, and say which; the workspace of
    `folder` goes on its list when this build's server serves."""
    home = paths.home(environ)
    port = machine.port_of(home, environ)
    found = addresses.alternate(home, environ, port) or client.ask(port, home)
    if isinstance(found, heard.Other):
        return shown(found, started=False)
    if environ.get("LEM_SERVE") == NO_START:
        said = "LEM_SERVE=off is set: no server starts and none ends"
        return shown(found, started=False, said=said)
    with lock.serve_lock(home):
        return held(home, environ, folder)
