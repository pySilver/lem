"""`lem owner away`: the owner is away, for every repository on this machine.

    lem owner away [--words WORDS]

A stub until the step `owner` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem owner away`."""

    words: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `owner` builds `lem owner away`."""
    raise not_built("owner away", "owner")


COMMAND = click.Command(
    "away",
    params=[
        click.Option(["--words"], help="the owner's words, as typed"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The owner is away, for every repository on this machine.",
)
