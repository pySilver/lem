"""`lem picker`: show agterm's picker over the tasks, to go to a session or a board.

    lem picker [--list]

An agterm keymap command starts it with a chord, in the session's folder (`lem --repo
"$AGT_SESSION_PWD" picker`, the line `lem doctor` gives); a pick selects the task's live
session, else opens its board (`addons/picker/picking.py`). With `--list` it prints the rows and
opens nothing.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.addons.picker import looks, picking
from lem.cli import place
from lem.kernel import clock

if TYPE_CHECKING:
    from lem.addons.picker.row import PickRow


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem picker`."""

    listing: bool = False


def run(call: Call) -> picking.Picked | tuple[PickRow, ...]:
    """The rows, or the picker and the way to the task picked."""
    now = clock.now()
    if call.listing:
        _, found = looks.listed(place.folder(), now)
        return found
    return picking.picked(place.folder(), now)


COMMAND = click.Command(
    "picker",
    params=[
        click.Option(
            ["--list", "listing"],
            is_flag=True,
            help="print the rows as JSON and open nothing",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Show agterm's picker over the tasks, to go to a session or a board.",
)
