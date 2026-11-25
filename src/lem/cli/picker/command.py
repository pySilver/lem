"""`lem picker`: show agterm's picker over the tasks, to go to a session or a board.

    lem picker [--list]

An agterm keymap command starts it with a chord in the session's folder (the line `lem doctor`
gives). A pick selects the task's live session, else opens its board. The chord reads refusals
on standard error. With `--list` the command prints the rows and opens nothing.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.addons.picker import looks, picking
from lem.cli import place
from lem.kernel import clock
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.ports.terminal import PickRow


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem picker`."""

    listing: bool = False


def run(call: Call) -> picking.Picked | tuple[PickRow, ...]:
    """The rows, or the picker and the way to the task picked."""
    now = clock.now()
    if call.listing:
        _, found = looks.listed(place.folder(), now)
        return found
    try:
        return picking.picked(place.folder(), now)
    except Refusal as refusal:
        line = f"lem picker: {refusal.why}. {refusal.fix}"
        click.echo(" ".join(line.split()), err=True)
        raise


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
