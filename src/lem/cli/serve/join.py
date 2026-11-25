"""`lem serve join`: show the boards of another machine of the tailnet.

lem serve join HOST
"""

import click
import msgspec

from lem.addons.peers import commands


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve join`."""

    host: str


def run(call: Call) -> commands.Answer:
    """Run the peer command."""
    return commands.joined(call.host)


COMMAND = click.Command(
    "join",
    params=[
        click.Argument(["host"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Show the boards of another machine of the tailnet.",
)
