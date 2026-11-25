"""`lem owner watch`: wait for the owner's next word.

    lem owner watch [--seen N] [--every SECONDS]

A stub until the step `owner` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem owner watch`."""

    seen: int | None = None
    every: int = 5


def run(call: Call) -> None:
    """Refuse until the step `owner` builds `lem owner watch`."""
    raise not_built("owner watch", "owner")


COMMAND = click.Command(
    "watch",
    params=[
        click.Option(
            ["--seen"], type=click.INT, help="the number of records in the owner's mark"
        ),
        click.Option(
            ["--every"],
            type=click.INT,
            default=5,
            help="seconds between two looks at the mark",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Wait for the owner's next word.",
)
