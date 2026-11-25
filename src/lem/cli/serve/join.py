"""`lem serve join`: show the boards of another machine of the tailnet.

    lem serve join HOST

A stub until the step `addons-outside` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve join`."""

    host: str


def run(call: Call) -> None:
    """Refuse until the step `addons-outside` builds `lem serve join`."""
    raise not_built("serve join", "addons-outside")


COMMAND = click.Command(
    "join",
    params=[
        click.Argument(["host"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Show the boards of another machine of the tailnet.",
)
