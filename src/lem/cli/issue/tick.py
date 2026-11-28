"""`lem issue tick`: the feature's parts on its issue: one comment with a box for each part, set
for each part that landed.

lem issue tick NAME
"""

import click
import msgspec

from lem.app.tasks import ports
from lem.app.tasks.issues import tick
from lem.cli import place
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem issue tick`."""

    slug: str


def run(call: Call) -> object:
    """Post the feature's parts comment, or edit it when the records say more."""
    where = places.workspace(place.folder())
    return tick.tick(ports.bound(where), where, call.slug)


COMMAND = click.Command(
    "tick",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help=(
        "The feature's parts on its issue: one comment with a box for each part, set for "
        "each part that landed."
    ),
)
