"""`lem owner watch`: wait for the owner's next word.

    lem owner watch [--seen N] [--every SECONDS]

It ends with the owner's presence once the machine's mark holds another number of changes than
`--seen`, the count `lem waiting` gave as `owner.seen`; it writes nothing (`app/owner/watch.py`).
"""

import click
import msgspec

from lem.app.owner import watch


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem owner watch`."""

    seen: int | None = None
    every: int = 5


def run(call: Call) -> watch.Seen:
    """Wait for the owner's next word, and give his presence."""
    return watch.watched(call.seen, call.every)


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
