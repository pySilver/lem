"""`lem land next`: the due step of the landing, and why.

    lem land next SLUG

The step `land-merge` owns it.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.landing import next as due
from lem.cli import place

if TYPE_CHECKING:
    from lem.kernel.envelope import Envelope


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land next`."""

    slug: str


def run(call: Call) -> Envelope:
    """Say the due step of the landing, and why."""
    return due.due_now(place.folder(), call.slug)


COMMAND = click.Command(
    "next",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The due step of the landing, and why.",
)
