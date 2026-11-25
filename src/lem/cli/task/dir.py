"""`lem task dir`: the folder of a task.

    lem task dir SLUG

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task dir`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem task dir`."""
    raise not_built("task dir", "task")


COMMAND = click.Command(
    "dir",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The folder of a task.",
)
