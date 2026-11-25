"""`lem decisions changes`: the changes of a task's criteria in the build.

    lem decisions changes SLUG

The approved criteria, each recorded change of them in order, and the criteria they give,
which the plan's criteria must be.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.decisions import listing
from lem.cli import place

if TYPE_CHECKING:
    from lem.model.decisions.changes import Changes


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem decisions changes`."""

    slug: str


def run(call: Call) -> Changes:
    """The approvals, the changes of the newest one, and the criteria they give."""
    return listing.changes_of(place.folder(), call.slug)


COMMAND = click.Command(
    "changes",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The changes of a task's criteria in the build.",
)
