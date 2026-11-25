"""`lem serve list`: the workspaces as the server shows them.

    lem serve list

A stub until the step `board-service` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve list`."""


def run(call: Call) -> None:
    """Refuse until the step `board-service` builds `lem serve list`."""
    raise not_built("serve list", "board-service")


COMMAND = click.Command(
    "list",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The workspaces as the server shows them.",
)
