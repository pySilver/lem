"""`lem serve remove`: take a repository out of the list of workspaces.

    lem serve remove DIR

A stub until the step `board-service` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve remove`."""

    folder: str


def run(call: Call) -> None:
    """Refuse until the step `board-service` builds `lem serve remove`."""
    raise not_built("serve remove", "board-service")


COMMAND = click.Command(
    "remove",
    params=[
        click.Argument(["folder"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Take a repository out of the list of workspaces.",
)
