"""`lem proposals list`: every proposal with no verdict, and the newest runs.

    lem proposals list

Read only: every record of the night and the retro (`addons/proposals/listing.py`).
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.addons.proposals import listing
from lem.cli import place
from lem.store import places

if TYPE_CHECKING:
    from lem.addons.proposals.listed import Read


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem proposals list`."""


def run(call: Call) -> Read:
    """Every proposal with no verdict, every verdict and drop, and the newest runs."""
    return listing.listed(places.workspace(place.folder()).state)


COMMAND = click.Command(
    "list",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Every proposal with no verdict, and the newest runs.",
)
