"""`lem land clean`: remove the landed task's worktree and branch.

    lem land clean SLUG

The step `land-merge` owns it.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import clean
from lem.cli import place

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land clean`."""

    slug: str


def run(call: Call) -> Envelope:
    """Remove the landed task's worktree and branch."""
    return clean.run(place.folder(), call.slug)


COMMAND = click.Command(
    "clean",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Remove the landed task's worktree and branch.",
)
