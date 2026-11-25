"""`lem criteria approved`: whether a task's criteria are approved.

    lem criteria approved SLUG

A stub until the step `criteria` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria approved`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `criteria` builds `lem criteria approved`."""
    raise not_built("criteria approved", "criteria")


COMMAND = click.Command(
    "approved",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Whether a task's criteria are approved.",
)
