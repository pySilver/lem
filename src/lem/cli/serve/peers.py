"""`lem serve peers`: each machine joined, and whether it answers now.

lem serve peers
"""

import click
import msgspec

from lem.addons.peers import report


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve peers`."""


def run(call: Call) -> object:
    """Run the peer command."""
    return report.listed()


COMMAND = click.Command(
    "peers",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Each machine joined, and whether it answers now.",
)
