"""`lem proposals add`: add a run's proposals to the record of its day.

    lem proposals add --kind night|retro [--date DAY] --file FILE

A stub until the step `addons-flow` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type Kind = Literal["night", "retro"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem proposals add`."""

    kind: Kind
    date: str | None = None
    path: str


def run(call: Call) -> None:
    """Refuse until the step `addons-flow` builds `lem proposals add`."""
    raise not_built("proposals add", "addons-flow")


COMMAND = click.Command(
    "add",
    params=[
        click.Option(
            ["--kind"],
            required=True,
            type=choice(Kind),
            help="the run: the night or the retro",
        ),
        click.Option(["--date"], help="the run's day (default: today, in UTC)"),
        click.Option(
            ["--file", "path"], required=True, help="the run as JSON, or - for stdin"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Add a run's proposals to the record of its day.",
)
