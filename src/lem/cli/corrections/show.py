"""`lem corrections show`: one correction of the queue.

    lem corrections show ID

A stub until the step `addons-flow` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem corrections show`."""

    entry: str


def run(call: Call) -> None:
    """Refuse until the step `addons-flow` builds `lem corrections show`."""
    raise not_built("corrections show", "addons-flow")


COMMAND = click.Command(
    "show",
    params=[
        click.Argument(["entry"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="One correction of the queue.",
)
