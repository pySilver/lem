"""`lem criteria record`: the record of a task's criteria and their tests.

    lem criteria record SLUG

The plain form of the fast track, as the step `slice-land` built it; the step `criteria` owns it.
"""

from typing import TYPE_CHECKING

import click
import msgspec

from lem.app.criteria import record
from lem.cli import place

if TYPE_CHECKING:
    from lem.app.criteria.sheet import Sheet


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria record`."""

    slug: str


def run(call: Call) -> Sheet:
    """Read the task's `criteria.md` into its record."""
    return record.recorded(place.folder(), call.slug)


COMMAND = click.Command(
    "record",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The record of a task's criteria and their tests.",
)
