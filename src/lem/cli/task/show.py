"""`lem task show`: one task: status, hold, ticket owed, board answer, night, mode.

    lem task show SLUG

A read: it writes nothing (`app/tasks/listing.py`).
"""

import click
import msgspec

from lem.app.tasks import listing
from lem.cli import place


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task show`."""

    slug: str


def run(call: Call) -> listing.Row:
    """One task as its record says now."""
    return listing.shown(place.folder(), call.slug)


COMMAND = click.Command(
    "show",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="One task: status, hold, ticket owed, board answer, night, mode.",
)
