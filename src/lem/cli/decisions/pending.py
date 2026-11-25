"""`lem decisions pending`: the decisions that wait for the owner's read.

    lem decisions pending [SLUG]

A stub until the step `criteria` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem decisions pending`."""

    slug: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `criteria` builds `lem decisions pending`."""
    raise not_built("decisions pending", "criteria")


COMMAND = click.Command(
    "pending",
    params=[
        click.Argument(["slug"], required=False),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The decisions that wait for the owner's read.",
)
