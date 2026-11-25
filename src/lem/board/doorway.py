"""`lem serve door on|off`: the tailnet door opened or closed from now on (`serve --tailscale`
and `--tailscale-off` on `main`).

`on` checks first what the door needs (a tailscale CLI, a connected Tailscale signed in with the
owner's account, HTTPS certificates, a port of its own), so that nothing is written that would
stop every start; then it writes `serve.tailscale = true` into the machine's settings and makes
sure the server runs the new way, which replaces a server whose door differs. `off` writes
`false`, makes sure the server runs without the door, and takes Lem's entry of the door's port
out of `tailscale serve`, only when it points at Lem's door.
"""

from typing import TYPE_CHECKING, Literal

import msgspec

from lem.board import ensure, machine, publish, tailnet, tailscale
from lem.board.facts import Shown
from lem.kernel import paths
from lem.settings.places import Scope
from lem.settings.write import Asked, set_setting

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


type State = Literal["on", "off"]
ON: State = "on"
OFF: State = "off"


class Doorway(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """What the door's command did: the door's state now, the server that runs, the door's
    address on the tailnet, and whether Lem's entry left `tailscale serve`."""

    door: State
    server: Shown
    url: str | None = None
    removed: bool = False


def written(environ: Mapping[str, str], folder: Path, state: State) -> None:
    """`serve.tailscale` in the machine's settings, as `state` says."""
    word = "true" if state == ON else "false"
    asked = Asked(
        key="serve.tailscale",
        word=word,
        scope=Scope.machine,
        folder=folder,
        environ=environ,
    )
    set_setting(asked)


def opened(environ: Mapping[str, str], folder: Path) -> Doorway:
    """Open the door from now on."""
    settings = machine.settings(paths.home(environ))
    cli = tailscale.needed(environ)
    tailnet.facts(tailnet.status(cli))
    machine.guarded(settings.tailscale_port, environ)
    written(environ, folder, ON)
    shown = ensure.ensure(environ, folder)
    return Doorway(door=ON, server=shown, url=shown.tailnet)


def closed(environ: Mapping[str, str], folder: Path) -> Doorway:
    """Close the door from now on, and take Lem's entry out of `tailscale serve`."""
    port = machine.settings(paths.home(environ)).tailscale_port
    written(environ, folder, OFF)
    shown = ensure.ensure(environ, folder)
    cli = tailscale.cli(environ)
    if cli is None:
        return Doorway(door=OFF, server=shown)
    name = tailnet.status(cli).me.name.rstrip(".")
    return Doorway(door=OFF, server=shown, removed=publish.removed(cli, name, port))
