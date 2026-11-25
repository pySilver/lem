"""`lem issue read`: one issue of origin's repository, by number or address.

lem issue read ISSUE
"""

import click
import msgspec

from lem.app.tasks import ports
from lem.app.tasks.issues import reading
from lem.cli import place
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem issue read`."""

    issue: str


def run(call: Call) -> object:
    """Read the issue: its words, state, people and comments; writes nothing."""
    where = places.workspace(place.folder())
    return reading.read(ports.bound(where), where, call.issue)


COMMAND = click.Command(
    "read",
    params=[
        click.Argument(["issue"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="One issue of origin's repository, by number or address.",
)
