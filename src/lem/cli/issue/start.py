"""`lem issue start`: the build started: the person signed in becomes the assignee.

    lem issue start SLUG

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem issue start`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem issue start`."""
    raise not_built("issue start", "task")


COMMAND = click.Command(
    "start",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The build started: the person signed in becomes the assignee.",
)
