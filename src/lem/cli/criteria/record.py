"""`lem criteria record`: the record of a task's criteria and their tests.

    lem criteria record SLUG

What `lem criteria show` gives, kept in the task's record, which the checks and the pull
request read: the builder runs it once the test lines are in.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.criteria import show
from lem.cli import place

if TYPE_CHECKING:
    from lem.model.criteria.standing import Shown


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria record`."""

    slug: str


def run(call: Call) -> Shown:
    """Keep the task's criteria as they stand in its record."""
    return show.recorded(place.folder(), call.slug)


COMMAND = click.Command(
    "record",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The record of a task's criteria and their tests.",
)
