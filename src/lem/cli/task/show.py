"""`lem task show`: one task: status, hold, ticket owed, board answer, night, mode.

    lem task show SLUG

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task show`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem task show`."""
    raise not_built("task show", "task")


COMMAND = click.Command(
    "show",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="One task: status, hold, ticket owed, board answer, night, mode.",
)
