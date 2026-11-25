"""`lem criteria read`: the persona read of the criteria: start, done or silent.

    lem criteria read SLUG start|done|silent --by lem|lead

A stub until the step `criteria` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type Moment = Literal["start", "done", "silent"]
type By = Literal["lem", "lead"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria read`."""

    slug: str
    moment: Moment
    by: By


def run(call: Call) -> None:
    """Refuse until the step `criteria` builds `lem criteria read`."""
    raise not_built("criteria read", "criteria")


COMMAND = click.Command(
    "read",
    params=[
        click.Argument(["slug"]),
        click.Argument(["moment"], type=choice(Moment)),
        click.Option(
            ["--by"], required=True, type=choice(By), help="who runs the read"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The persona read of the criteria: start, done or silent.",
)
