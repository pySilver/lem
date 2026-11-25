"""`lem session open`: open the task's session for its phase.

    lem session open SLUG [--why WHY] [--session ID]

A stub until the step `slice-session` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type Why = Literal[
    "new",
    "handoff",
    "dead",
    "merged",
    "conflict",
    "refused",
    "queue",
    "night",
    "owner",
    "stopped",
]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session open`."""

    slug: str
    why: Why = "owner"
    session: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `slice-session` builds `lem session open`."""
    raise not_built("session open", "slice-session")


COMMAND = click.Command(
    "open",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--why"],
            type=choice(Why),
            default="owner",
            help="why it opens, for the record",
        ),
        click.Option(
            ["--session"], help="with --why stopped: the session the restart replaces"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Open the task's session for its phase.",
)
