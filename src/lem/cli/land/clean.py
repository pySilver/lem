"""`lem land clean`: remove the landed task's worktree and branch.

    lem land clean SLUG

A stub until the step `land-merge` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem land clean`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `land-merge` builds `lem land clean`."""
    raise not_built("land clean", "land-merge")


COMMAND = click.Command(
    "clean",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Remove the landed task's worktree and branch.",
)
