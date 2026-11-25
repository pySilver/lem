"""`lem criteria record`: the record of a task's criteria and their tests.

    lem criteria record SLUG

A stub until the step `slice-land` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria record`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `slice-land` builds `lem criteria record`."""
    raise not_built("criteria record", "slice-land")


COMMAND = click.Command(
    "record",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The record of a task's criteria and their tests.",
)
