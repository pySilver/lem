"""`lem task keep-item`: the task's backlog item stays in the backlog.

    lem task keep-item SLUG --why WORDS

For a request that named an item for other work, or whose approved criteria do not cover the
item's whole run: the task holds the item no more, its branch keeps it, and its pull request
says why (`app/tasks/item_kept.py`).
"""

import click
import msgspec

from lem.app.tasks import item_kept
from lem.cli import place


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task keep-item`."""

    slug: str
    why: str


def run(call: Call) -> item_kept.Kept:
    """Leave the item to the backlog."""
    return item_kept.kept(place.folder(), call.slug, call.why)


COMMAND = click.Command(
    "keep-item",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--why"],
            required=True,
            help="what of the item this task leaves undone, in a few words",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Leave the task's backlog item in the backlog.",
)
