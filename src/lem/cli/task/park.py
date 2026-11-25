"""`lem task park`: put a task aside on the owner's word, with his reason.

    lem task park SLUG --why WHY

The hold `parked` of the design's part 3, only over a task no agent works on; `lem task resume
SLUG` brings the task back with the hold the park put aside (`app/tasks/park.py`).
"""

import click
import msgspec

from lem.app.tasks import park
from lem.cli import place


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task park`."""

    slug: str
    why: str


def run(call: Call) -> park.Resumed:
    """Park the task on the owner's word."""
    return park.parked(place.folder(), call.slug, call.why)


COMMAND = click.Command(
    "park",
    params=[
        click.Argument(["slug"]),
        click.Option(["--why"], required=True, help="the owner's reason, in his words"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Put a task aside on the owner's word, with his reason.",
)
