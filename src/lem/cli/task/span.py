"""`lem task span`: the start or the end of one span of a task's work.

    lem task span SLUG NAME start|end [--of N/M] [--job J] [--by B]

A stub until the step `task` builds it: it refuses `not-built`.
"""

from typing import Literal

import click
import msgspec

from lem.cli.stub import not_built
from lem.cli.words import choice

type Edge = Literal["start", "end"]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task span`."""

    slug: str
    name: str
    edge: Edge
    of: str | None = None
    job: str | None = None
    by: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `task` builds `lem task span`."""
    raise not_built("task span", "task")


COMMAND = click.Command(
    "span",
    params=[
        click.Argument(["slug"]),
        click.Argument(["name"]),
        click.Argument(["edge"], type=choice(Edge)),
        click.Option(
            ["--of"], help="with the span task: its number of the plan's tasks, N/M"
        ),
        click.Option(["--job"], help="the job the span is of"),
        click.Option(["--by"], help="who works in the span"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The start or the end of one span of a task's work.",
)
