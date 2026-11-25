"""`lem criteria show`: a task's criteria, with their state.

    lem criteria show SLUG

A stub until the step `criteria` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria show`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `criteria` builds `lem criteria show`."""
    raise not_built("criteria show", "criteria")


COMMAND = click.Command(
    "show",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="A task's criteria, with their state.",
)
