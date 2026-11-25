"""`lem task list`: every task with its status and hold.

    lem task list [--ended]

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task list`."""

    ended: bool = False


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem task list`."""
    raise not_built("task list", "task")


COMMAND = click.Command(
    "list",
    params=[
        click.Option(["--ended"], is_flag=True, help="the ended tasks too"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Every task with its status and hold.",
)
