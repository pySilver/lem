"""`lem criteria inputs`: the inputs of the check of the criteria.

    lem criteria inputs SLUG

A stub until the step `land-checks` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria inputs`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `land-checks` builds `lem criteria inputs`."""
    raise not_built("criteria inputs", "land-checks")


COMMAND = click.Command(
    "inputs",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The inputs of the check of the criteria.",
)
