"""`lem serve add`: put a repository into the list of workspaces.

    lem serve add DIR

A stub until the step `board-service` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve add`."""

    folder: str


def run(call: Call) -> None:
    """Refuse until the step `board-service` builds `lem serve add`."""
    raise not_built("serve add", "board-service")


COMMAND = click.Command(
    "add",
    params=[
        click.Argument(["folder"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Put a repository into the list of workspaces.",
)
