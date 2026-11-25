"""`lem proposals drop`: the owner's drop of a reviewer's item.

    lem proposals drop PATH

PATH is the item's path from the main checkout, `.lem/state/backlog/NAME.md`, or whole. The
board's Drop runs it; the envelope's `result.proposals` names the proposals whose records keep
the drop (`addons/proposals/dropping.py`).
"""

import click
import msgspec

from lem.addons.proposals import dropping
from lem.cli import place
from lem.kernel import clock
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem proposals drop`."""

    path: str


def run(call: Call) -> dropping.Dropped:
    """Drop the reviewer's item, and keep the drop in the records of its proposals."""
    where = places.workspace(place.folder())
    places.state_of(where.checkout)
    return dropping.dropped(where, call.path, clock.now().date())


COMMAND = click.Command(
    "drop",
    params=[
        click.Argument(["path"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The owner's drop of a reviewer's item.",
)
