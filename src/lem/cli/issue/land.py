"""`lem issue land`: the task landed: one comment, and the issue is closed.

lem issue land SLUG
"""

import click
import msgspec

from lem.app.tasks import ports
from lem.app.tasks.issues import land
from lem.cli import place
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem issue land`."""

    slug: str


def run(call: Call) -> object:
    """Post the landing's comment, then close the issue as completed."""
    where = places.workspace(place.folder())
    return land.land(ports.bound(where), where, call.slug)


COMMAND = click.Command(
    "land",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The task landed: one comment, and the issue is closed.",
)
