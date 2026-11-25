"""`lem land merged`: the steps after the forge merged the pull request.

    lem land merged SLUG

A stub until the step `land-merge` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land merged`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `land-merge` builds `lem land merged`."""
    raise not_built("land merged", "land-merge")


COMMAND = click.Command(
    "merged",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The steps after the forge merged the pull request.",
)
