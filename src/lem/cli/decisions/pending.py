"""`lem decisions pending`: the decisions that wait for the owner's read.

    lem decisions pending [SLUG]

The breakers that wait, of one task or of every task: a parked task's under `parked`; a task
that is dropped, landed or answered has none waiting, and its breakers are named under `ended`.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.decisions import listing
from lem.cli import place

if TYPE_CHECKING:
    from lem.model.decisions.pending import Pending


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem decisions pending`."""

    slug: str | None = None


def run(call: Call) -> Pending:
    """The breakers that wait for the owner."""
    return listing.waiting(place.folder(), call.slug)


COMMAND = click.Command(
    "pending",
    params=[
        click.Argument(["slug"], required=False),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The decisions that wait for the owner's read.",
)
