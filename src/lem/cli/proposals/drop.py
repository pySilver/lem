"""`lem proposals drop`: the owner's drop of a reviewer's item.

    lem proposals drop PATH

A stub until the step `addons-flow` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem proposals drop`."""

    path: str


def run(call: Call) -> None:
    """Refuse until the step `addons-flow` builds `lem proposals drop`."""
    raise not_built("proposals drop", "addons-flow")


COMMAND = click.Command(
    "drop",
    params=[
        click.Argument(["path"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The owner's drop of a reviewer's item.",
)
