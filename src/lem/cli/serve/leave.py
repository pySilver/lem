"""`lem serve leave`: show the boards of a joined machine no more.

    lem serve leave HOST

A stub until the step `addons-outside` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve leave`."""

    host: str


def run(call: Call) -> None:
    """Refuse until the step `addons-outside` builds `lem serve leave`."""
    raise not_built("serve leave", "addons-outside")


COMMAND = click.Command(
    "leave",
    params=[
        click.Argument(["host"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Show the boards of a joined machine no more.",
)
