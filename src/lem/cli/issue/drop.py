"""`lem issue drop`: the task was dropped: one comment, and Lem's assignee goes.

    lem issue drop SLUG

A stub until the step `task` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem issue drop`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem issue drop`."""
    raise not_built("issue drop", "task")


COMMAND = click.Command(
    "drop",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The task was dropped: one comment, and Lem's assignee goes.",
)
