"""`lem issue start`: the build started: the person signed in becomes the assignee.

lem issue start SLUG
"""

import click
import msgspec

from lem.app.tasks import ports
from lem.app.tasks.issues import start
from lem.cli import place
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem issue start`."""

    slug: str


def run(call: Call) -> object:
    """Make the person signed in the assignee of an issue that has none."""
    where = places.workspace(place.folder())
    return start.start(ports.bound(where), where, call.slug)


COMMAND = click.Command(
    "start",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The build started: the person signed in becomes the assignee.",
)
