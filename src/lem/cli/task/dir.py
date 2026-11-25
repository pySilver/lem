"""`lem task dir`: the folder of a task.

    lem task dir SLUG

Refused for a task that is not there.
"""

import click
import msgspec

from lem.app.tasks import where
from lem.cli import place


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task dir`."""

    slug: str


def run(call: Call) -> where.Folder:
    """The folder of the task."""
    return where.folder_of(place.folder(), call.slug)


COMMAND = click.Command(
    "dir",
    params=[
        click.Argument(["slug"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The folder of a task.",
)
