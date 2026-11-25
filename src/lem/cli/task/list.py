"""`lem task list`: every task with its status and hold.

    lem task list [--ended]

The open tasks, the ended ones too with `--ended` (`app/tasks/listing.py`).
"""

import click
import msgspec

from lem.app.tasks import listing
from lem.cli import place


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task list`."""

    ended: bool = False


def run(call: Call) -> tuple[listing.Row, ...]:
    """Every task with its status and hold."""
    return listing.listed(place.folder(), ended=call.ended)


COMMAND = click.Command(
    "list",
    params=[
        click.Option(["--ended"], is_flag=True, help="the ended tasks too"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Every task with its status and hold.",
)
