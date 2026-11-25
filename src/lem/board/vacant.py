"""Whether `lem serve run` may serve in the foreground: it looks first at the port it would
serve and at the home folder's own port, and serves only when no board server answers on
either, so that a server of another install in the home folder (the release before this one)
keeps its port and every file of the home folder as they are."""

from typing import TYPE_CHECKING

from lem.board import client, heard, machine
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


type Environ = Mapping[str, str]


def ports(home: Path, environ: Environ, given: int | None) -> tuple[int, ...]:
    """The port to serve, and the home folder's own when it is another that may be asked."""
    port = machine.port_of(home, environ, given)
    setting = machine.settings(home).port
    if setting == port or not machine.allowed(setting, environ):
        return (port,)
    return (port, setting)


def vacant(home: Path, environ: Environ, given: int | None) -> int:
    """The port to serve; refused while a board server answers for this home folder."""
    looked = ports(home, environ, given)
    for port in looked:
        found = client.ask(port, home)
        if isinstance(found, heard.Other):
            raise Refusal(
                "other-install",
                heard.which(found),
                "use that install, or stop its server with its own lem serve stop",
            )
        if found is not None:
            raise Refusal(
                "running",
                f"the board server of this home folder runs on port {port} (pid "
                f"{found.pid})",
                "lem serve stop ends it",
            )
    return looked[0]
