"""`lem seat again`: the owner's go: the seat the settings name is tried again.

    lem seat again SLUG

A stub until the step `sessions` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem seat again`."""

    slug: str


def run(call: Call) -> None:
    """Refuse until the step `sessions` builds `lem seat again`."""
    raise not_built("seat again", "sessions")


COMMAND = click.Command(
    "again",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The owner's go: the seat the settings name is tried again.",
)
