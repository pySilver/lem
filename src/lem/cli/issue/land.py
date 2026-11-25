"""`lem issue land`: the task landed: one comment, and the issue is closed.

    lem issue land SLUG

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem issue land`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem issue land`."""
    raise not_built("issue land", "task")


COMMAND = click.Command(
    "land",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The task landed: one comment, and the issue is closed.",
)
