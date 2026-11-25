"""`lem owner back`: the owner is back, for every repository on this machine.

    lem owner back [--words WORDS]

A stub until the step `owner` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem owner back`."""

    words: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `owner` builds `lem owner back`."""
    raise not_built("owner back", "owner")


COMMAND = click.Command(
    "back",
    params=[
        click.Option(["--words"], help="the owner's words, as typed"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The owner is back, for every repository on this machine.",
)
