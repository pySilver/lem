"""`lem land base`: bring the task's branch onto the base it lands on.

    lem land base SLUG

A stub until the step `land-base` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land base`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `land-base` builds `lem land base`."""
    raise not_built("land base", "land-base")


COMMAND = click.Command(
    "base",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Bring the task's branch onto the base it lands on.",
)
