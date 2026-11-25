"""`lem criteria approved`: whether a task's criteria are approved.

    lem criteria approved SLUG

The newest approval, with its criteria, or null and why: a task with none has its plan's
criteria as their one source.
"""

import click
import msgspec

from lem.app.criteria import marks
from lem.cli import place


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria approved`."""

    slug: str


def run(call: Call) -> marks.Approved:
    """The newest approval of the task's criteria, or None."""
    return marks.approved(place.folder(), call.slug)


COMMAND = click.Command(
    "approved",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Whether a task's criteria are approved.",
)
