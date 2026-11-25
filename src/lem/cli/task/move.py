"""`lem task move`: move a task to a status, by the table of statuses.

    lem task move SLUG STATUS [--line L]... [--start-over WHY]

The plain form of the fast track, as the step `slice-land` built it; the step `task` owns it.
"""

from typing import Literal

import click
import msgspec

from lem.app.tasks import move
from lem.cli import place
from lem.cli.stub import not_built
from lem.cli.words import choice

type Status = Literal[
    "queued",
    "shaping",
    "building",
    "planned",
    "ready",
    "landing",
    "open",
    "landed",
    "answered",
    "dropped",
]


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task move`."""

    slug: str
    status: Status
    lines: tuple[str, ...] = ()
    start_over: str | None = None


def run(call: Call) -> move.Moved:
    """Move the task; a drop and a start over are the step `task`'s."""
    if call.start_over or call.status == "dropped":
        raise not_built("task move SLUG dropped|--start-over", "task")
    return move.moved(place.folder(), call.slug, call.status, call.lines)


COMMAND = click.Command(
    "move",
    params=[
        click.Argument(["slug"]),
        click.Argument(["status"], type=choice(Status)),
        click.Option(
            ["--line", "lines"],
            multiple=True,
            help="a line of the state, once for each",
        ),
        click.Option(
            ["--start-over"], help="why the landing starts over with nothing carried"
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Move a task to a status, by the table of statuses.",
)
