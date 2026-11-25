"""`lem session wake`: a message to the task's live session, or a new session.

    lem session wake SLUG --why WHY [--head SHA] [--session ID]

A stub until the step `sessions` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type Why = Literal["merged", "conflict", "refused", "queue", "owner", "inbox", "status"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem session wake`."""

    slug: str
    why: Why
    head: str | None = None
    session: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `sessions` builds `lem session wake`."""
    raise not_built("session wake", "sessions")


COMMAND = click.Command(
    "wake",
    params=[
        click.Argument(["slug"]),
        click.Option(["--why"], required=True, type=choice(Why), help="why it wakes"),
        click.Option(["--head"], help="the pull request's head the wake is for"),
        click.Option(
            ["--session"], help="with --why status: the session the line is for"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="A message to the task's live session, or a new session.",
)
