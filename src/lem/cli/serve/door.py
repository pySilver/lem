"""`lem serve door`: open or close the tailnet door, from now on.

    lem serve door on|off

`on` checks what the door needs, writes `serve.tailscale = true` into the machine's settings,
and makes sure the server runs with the door: a second listener on 127.0.0.1 behind
`tailscale serve --bg --https=PORT`, which lets in only the owner's own Tailscale login. `off`
writes `false`, makes sure the server runs without it, and takes Lem's entry out of
`tailscale serve`. Funnel is never used.
"""

import os
from typing import Literal

import click
import msgspec

from lem.board import doorway
from lem.cli import place
from lem.cli.words import choice

type State = Literal["on", "off"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve door`."""

    state: State


def run(call: Call) -> doorway.Doorway:
    """Open or close the door, and say what runs now."""
    if call.state == "on":
        return doorway.opened(os.environ, place.folder())
    return doorway.closed(os.environ, place.folder())


COMMAND = click.Command(
    "door",
    params=[
        click.Argument(["state"], type=choice(State)),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Open or close the tailnet door, from now on.",
)
