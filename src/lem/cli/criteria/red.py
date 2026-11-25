"""`lem criteria red`: whether each criterion's tests fail on the base.

    lem criteria red SLUG

A stub until the step `land-checks` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria red`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `land-checks` builds `lem criteria red`."""
    raise not_built("criteria red", "land-checks")


COMMAND = click.Command(
    "red",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Whether each criterion's tests fail on the base.",
)
