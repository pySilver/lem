"""`lem task start`: start a queued task on the owner's word.

    lem task start SLUG --words WORDS

His word lifts the queue, and its line keeps his words (`app/tasks/start.py`).
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.tasks import start
from lem.cli import place

if TYPE_CHECKING:
    from lem.model.task.table import Moved


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task start`."""

    slug: str
    words: str


def run(call: Call) -> Moved:
    """Start the queued task on the owner's word."""
    return start.start(place.folder(), call.slug, call.words)


COMMAND = click.Command(
    "start",
    params=[
        click.Argument(["slug"]),
        click.Option(["--words"], required=True, help="the owner's words, as typed"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Start a queued task on the owner's word.",
)
