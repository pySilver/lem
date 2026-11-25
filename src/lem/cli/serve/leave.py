"""`lem serve leave`: show the boards of a joined machine no more.

lem serve leave HOST
"""

import click
import msgspec

from lem.addons.peers import commands


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve leave`."""

    host: str


def run(call: Call) -> dict[str, object]:
    """Run the peer command."""
    return commands.leave(call.host)


COMMAND = click.Command(
    "leave",
    params=[
        click.Argument(["host"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Show the boards of a joined machine no more.",
)
