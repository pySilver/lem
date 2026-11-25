"""`lem corrections show`: one correction of the queue.

    lem corrections show ID

Read only: every entry of one unreviewed group, in full (`addons/corrections/listing.py`).
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.addons.corrections import listing
from lem.cli import place
from lem.store import places

if TYPE_CHECKING:
    from lem.records.corrections import Correction


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem corrections show`."""

    entry: str


def run(call: Call) -> tuple[Correction, ...]:
    """Every entry of the group."""
    return listing.shown(places.workspace(place.folder()).state, call.entry)


COMMAND = click.Command(
    "show",
    params=[
        click.Argument(["entry"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="One correction of the queue.",
)
