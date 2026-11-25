"""`lem task move`: move a task to a status, by the table of statuses.

    lem task move SLUG STATUS [--line L]... [--start-over WHY]

A move by the table of statuses (`model/task/table.py`); `dropped` is the owner's drop, under
the landing's step lock (`app/tasks/drop.py`); `--start-over WHY` gives a task with its landing
back to `ready`, only where the landing's refusal names it.
"""

from typing import TYPE_CHECKING, Literal

import click
import msgspec

from lem.app.tasks import move
from lem.cli import place
from lem.cli.words import choice

if TYPE_CHECKING:
    from lem.model.task.table import Moved

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


def run(call: Call) -> Moved:
    """Move the task."""
    return move.moved(
        place.folder(), call.slug, call.status, call.lines, call.start_over
    )


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
