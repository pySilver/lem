"""`lem picker`: show agterm's picker over the tasks, to go to a session or a board.

    lem picker [--list]

A stub until the step `addons-flow` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem picker`."""

    listing: bool = False


def run(call: Call) -> None:
    """Refuse until the step `addons-flow` builds `lem picker`."""
    raise not_built("picker", "addons-flow")


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
