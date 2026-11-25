"""`lem corrections list`: the corrections in the queue.

    lem corrections list

Read only: the queue's groups no retro decided about, most sessions first, after the failures
of the hook and the worker, and whether this machine collects (`addons/corrections/listing.py`).
Settings that do not read stop it, with the fix.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.addons.corrections import listing
from lem.cli import place
from lem.settings.load import settings_of
from lem.store import places

if TYPE_CHECKING:
    from lem.addons.corrections.listed import Listing


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem corrections list`."""


def run(call: Call) -> Listing:
    """The unreviewed groups of the queue."""
    where = places.workspace(place.folder())
    collect = settings_of(where.checkout).settings.corrections.collect
    return listing.listed(where.state, collect=collect)


COMMAND = click.Command(
    "list",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The corrections in the queue.",
)
