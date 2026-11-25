"""`lem criteria skip`: the skip of the persona read: asked, yes or no.

    lem criteria skip SLUG asked|yes|no

A stub until the step `criteria` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type Answer = Literal["asked", "yes", "no"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria skip`."""

    slug: str
    answer: Answer


def run(call: Call) -> None:
    """Refuse until the step `criteria` builds `lem criteria skip`."""
    raise not_built("criteria skip", "criteria")


COMMAND = click.Command(
    "skip",
    params=[
        click.Argument(["slug"]),
        click.Argument(["answer"], type=choice(Answer)),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The skip of the persona read: asked, yes or no.",
)
