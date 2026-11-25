"""`lem task may-start`: whether a task may start now, and the commands of its start.

    lem task may-start SLUG

Refused, with the way on, while it is queued behind a task not landed or answered, behind a
dropped one, parked, with its landing, or ended (`model/task/queue.py`).
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.tasks import start
from lem.cli import place

if TYPE_CHECKING:
    from lem.model.task.queue import May


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task may-start`."""

    slug: str


def run(call: Call) -> May:
    """Whether the task may start now, and the tasks that load the machine."""
    return start.may(place.folder(), call.slug)


COMMAND = click.Command(
    "may-start",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Whether a task may start now, and the commands of its start.",
)
