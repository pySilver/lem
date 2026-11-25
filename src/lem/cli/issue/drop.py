"""`lem issue drop`: the task was dropped: one comment, and Lem's assignee goes.

lem issue drop SLUG
"""

import click
import msgspec

from lem.app.tasks import ports
from lem.app.tasks.issues import ends
from lem.cli import place
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem issue drop`."""

    slug: str


def run(call: Call) -> object:
    """Post the drop's comment, and remove the assignee Lem added."""
    where = places.workspace(place.folder())
    return ends.ended(ports.bound(where), where, call.slug, "drop")


COMMAND = click.Command(
    "drop",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The task was dropped: one comment, and Lem's assignee goes.",
)
