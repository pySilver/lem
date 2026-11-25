"""`lem serve door`: open or close the tailnet door, from now on.

    lem serve door on|off

A stub until the step `board-service` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type State = Literal["on", "off"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve door`."""

    state: State


def run(call: Call) -> None:
    """Refuse until the step `board-service` builds `lem serve door`."""
    raise not_built("serve door", "board-service")


COMMAND = click.Command(
    "door",
    params=[
        click.Argument(["state"], type=choice(State)),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Open or close the tailnet door, from now on.",
)
