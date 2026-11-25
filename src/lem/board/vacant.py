"""Whether `lem serve run` may serve in the foreground: it looks first at the port it would
serve and at the home folder's own port, and serves only when no board server answers on
either, so that a server of another install in the home folder (the release before this one)
keeps its port and every file of the home folder as they are."""

from contextlib import suppress
from typing import TYPE_CHECKING

from lem.board import addresses, client, heard, machine
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


type Environ = Mapping[str, str]


def targets(
    home: Path, environ: Environ, given: int | None, host: str
) -> tuple[addresses.Address, ...]:
    """The address to serve, and the configured port when it is another that may be asked."""
    port = machine.port_of(home, environ, given)
    primary = (addresses.local(host), port)
    setting = machine.settings(home).port
    if setting == port or not machine.allowed(setting, environ):
        return (primary,)
    return primary, (client.LOOPBACK, setting)


def vacant(home: Path, environ: Environ, given: int | None, host: str) -> int:
    """The port to serve; refused while a board server answers for this home folder."""
    wanted = targets(home, environ, given, host)
    for address in wanted:
        checked(home, address)
    named = addresses.recorded(home, environ)
    if named is not None and named not in wanted:
        with suppress(heard.Unrelated):
            checked(home, named)
    return wanted[0][1]


def checked(home: Path, address: addresses.Address) -> None:
    """Refuse to start another server of this home folder."""
    host, port = address
    found = client.ask(port, home, host)
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
