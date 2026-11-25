"""`lem ask demo`: show the demo pages of the question page, by name.

    lem ask demo [NAMES]... [--follow] [--size N] [--style S] ...

A stub until the step `ask` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.ask.shown import Shown, options
from lem.cli.stub import not_built


class Call(Shown, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem ask demo`."""

    names: tuple[str, ...] = ()


def run(call: Call) -> None:
    """Refuse until the step `ask` builds `lem ask demo`."""
    raise not_built("ask demo", "ask")


COMMAND = click.Command(
    "demo",
    params=[
        click.Argument(["names"], nargs=-1),
        *options(),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Show the demo pages, each by name, or every one.",
)
