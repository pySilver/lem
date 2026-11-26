"""`lem serve door on|off`: the tailnet door opened or closed from now on (`serve --tailscale`
and `--tailscale-off` on `main`).

`on` checks what the door needs and sets `serve.tailscale = true` for the server to start.
It restores the setting on a definite refusal. `off` writes
`false`, makes sure the server runs without the door, and takes Lem's entry of the door's port
out of `tailscale serve`, only when it points at Lem's door.
"""

from typing import TYPE_CHECKING, Literal

import msgspec

from lem.board import (
    door_setting,
    ensure,
    machine,
    opening,
    publish,
    tailnet,
    tailscale,
)
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


def setting(environ: Mapping[str, str], folder: Path, state: State) -> Asked:
    """The machine setting for the requested state of the door."""
    word = "true" if state == ON else "false"
    return Asked(
        key="serve.tailscale",
        word=word,
        scope=Scope.machine,
        folder=folder,
        environ=environ,
    )


def opened(environ: Mapping[str, str], folder: Path) -> Doorway:
    """Open the door from now on."""
    settings = machine.settings(paths.home(environ))
    opening.checked_door_port(settings.port, settings.tailscale_port, environ)
    cli = tailscale.needed(environ)
    tailnet.facts(tailnet.status(cli))
    shown = door_setting.opened(setting(environ, folder, ON))
    return Doorway(door=ON, server=shown, url=shown.tailnet)


def closed(environ: Mapping[str, str], folder: Path) -> Doorway:
    """Close the door from now on, and take Lem's entry out of `tailscale serve`."""
    port = machine.settings(paths.home(environ)).tailscale_port
    machine.guarded(port, environ)
    set_setting(setting(environ, folder, OFF))
    shown = ensure.ensure(environ, folder)
    cli = tailscale.cli(environ)
    if cli is None:
        return Doorway(door=OFF, server=shown)
    name = tailnet.status(cli).me.name.rstrip(".")
    return Doorway(door=OFF, server=shown, removed=publish.removed(cli, name, port))
