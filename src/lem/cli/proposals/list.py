"""`lem proposals list`: every proposal with no verdict, and the newest runs.

    lem proposals list

A stub until the step `addons-flow` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem proposals list`."""


def run(call: Call) -> None:
    """Refuse until the step `addons-flow` builds `lem proposals list`."""
    raise not_built("proposals list", "addons-flow")


COMMAND = click.Command(
    "list",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Every proposal with no verdict, and the newest runs.",
)
