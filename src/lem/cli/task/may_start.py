"""`lem task may-start`: whether a task may start now, and the commands of its start.

    lem task may-start SLUG

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task may-start`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem task may-start`."""
    raise not_built("task may-start", "task")


COMMAND = click.Command(
    "may-start",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Whether a task may start now, and the commands of its start.",
)
