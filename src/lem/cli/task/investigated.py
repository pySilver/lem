"""`lem task investigated`: the result of the investigation of a bug or a question.

    lem task investigated SLUG --result R --call small|full

A stub until the step `task` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type Found = Literal["bug", "none", "question", "unreproduced"]
type Track = Literal["small", "full"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task investigated`."""

    slug: str
    found: Found
    call: Track


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem task investigated`."""
    raise not_built("task investigated", "task")


COMMAND = click.Command(
    "investigated",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--result", "found"],
            required=True,
            type=choice(Found),
            help="what the investigation found",
        ),
        click.Option(
            ["--call"],
            required=True,
            type=choice(Track),
            help="the track the change takes",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The result of the investigation of a bug or a question.",
)
