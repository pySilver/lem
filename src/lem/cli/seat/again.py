"""`lem seat again`: the owner's go: the seat the settings name is tried again.

    lem seat again SLUG

It clears the block a seat's error left, and ends each stand-in of that seat
(`app/sessions/seats_again.py`).
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.sessions import here, seats_again
from lem.cli import place
from lem.kernel import clock

if TYPE_CHECKING:
    from lem.records.task import Task


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem seat again`."""

    slug: str


def run(call: Call) -> Task:
    """Try the seat the settings name again."""
    bound = here.bound(place.folder())
    return seats_again.again(bound, call.slug, clock.now()).task


COMMAND = click.Command(
    "again",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The owner's go: the seat the settings name is tried again.",
)
