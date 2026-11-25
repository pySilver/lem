"""`lem issue check`: whether origin's issues can be Lem's tracker; writes nothing.

lem issue check
"""

import click
import msgspec

from lem.app.tasks import ports
from lem.app.tasks.issues import check
from lem.cli import place
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem issue check`."""


def run(call: Call) -> object:
    """Run the tracker's check; refused with each missing thing and its fix."""
    where = places.workspace(place.folder())
    return check.check(ports.bound(where))


COMMAND = click.Command(
    "check",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Whether origin's issues can be Lem's tracker; writes nothing.",
)
