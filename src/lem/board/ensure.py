"""`lem serve ensure`: one board server for this machine.

It reads first where its home folder is, its port and who serves there; then decides; and only
then takes the serve lock, reads the port again under it, and acts: a stop goes on the
connection that asked who serves. A server of another install that this one does not replace
(the release before this one always) is left as it is with every file of the home folder, and
the outcome says which install serves. `LEM_SERVE=off` makes `ensure` start nothing, end
nothing and write nothing: a test sets it, and a test that starts a server on purpose leaves it
out for that one call.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.board import (
    client,
    heard,
    install,
    lock,
    machine,
    serve_file,
    start,
    workspaces,
)
from lem.board.facts import Facts, Shown
from lem.board.halt import stopped
from lem.kernel import paths

if TYPE_CHECKING:
    from collections.abc import Mapping

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


def kept(found: Found) -> Shown | None:
    """The outcome when the server that runs stays, else None: this install replaces it."""
    if found is None:
        return None
    if isinstance(found, heard.Other):
        return shown(found, started=False)
    mine = install.install_of()
    differ = found.door != door_wanted(Path(found.home))
    if install.replaces(mine, found.install, settings_differ=differ):
        return None
    said = None if found.install == mine else "another install of Lem serves"
    return shown(found, started=False, said=said)


def door_wanted(home: Path) -> int | None:
    """The door's port the machine's settings open, None while they keep it closed."""
    settings = machine.settings(home)
    return settings.tailscale_port if settings.tailscale else None


def rebound(home: Path, port: int) -> None:
    """Stop the server of this home folder and install that `serve.json` names on another
    port than `port`: the owner moved the main port, and one server serves a machine."""
    named = serve_file.read(home)
    if named is None or named.port == port:
        return
    with client.opened(named.port) as connection:
        found = client.looked(connection, named.port, home)
        mine = install.install_of().package
        if (
            isinstance(found, Facts)
            and connection is not None
            and found.install.package == mine
        ):
            stopped(connection, named.port, found)


def held(home: Path, environ: Mapping[str, str], folder: Path) -> Shown:
    """`ensure` with the serve lock held: a server on a port the settings left stopped, the
    port read again, the server that runs kept or stopped on the connection that asked, and
    one of this install started."""
    port = machine.port_of(home, environ)
    rebound(home, port)
    with client.opened(port) as connection:
        found = client.looked(connection, port, home)
        stays = kept(found)
        if stays is not None:
            if not stays.another_install:
                workspaces.noted(home, folder)
            return stays
        if isinstance(found, Facts) and connection is not None:
            stopped(connection, port, found)
    facts = start.started(port, home, environ)
    workspaces.noted(home, folder)
    return shown(facts, started=True)


def ensure(environ: Mapping[str, str], folder: Path) -> Shown:
    """Make sure one board server runs for this machine, and say which; the workspace of
    `folder` goes on its list when this build's server serves."""
    home = paths.home(environ)
    port = machine.port_of(home, environ)
    found = client.ask(port, home)
    if isinstance(found, heard.Other):
        return shown(found, started=False)
    if environ.get("LEM_SERVE") == NO_START:
        said = "LEM_SERVE=off is set: no server starts and none ends"
        return shown(found, started=False, said=said)
    with lock.serve_lock(home):
        return held(home, environ, folder)
