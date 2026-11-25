"""`lem land next`: the due step of the landing, and why.

    lem land next SLUG

A stub until the step `land-merge` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land next`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `land-merge` builds `lem land next`."""
    raise not_built("land next", "land-merge")


COMMAND = click.Command(
    "next",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The due step of the landing, and why.",
)
