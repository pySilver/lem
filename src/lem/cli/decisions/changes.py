"""`lem decisions changes`: the changes of a task's criteria in the build.

    lem decisions changes SLUG

A stub until the step `criteria` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem decisions changes`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `criteria` builds `lem decisions changes`."""
    raise not_built("decisions changes", "criteria")


COMMAND = click.Command(
    "changes",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The changes of a task's criteria in the build.",
)
