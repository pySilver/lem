"""`lem criteria digest`: the digest of a task's criteria, or of a file.

    lem criteria digest SLUG [--file FILE]

The mark of the `Size` line and the criteria's texts, each with its case, without their tests:
what an approval keeps and what the record of the personas' read names.
"""

from pathlib import Path

import click
import msgspec

from lem.app.criteria import marks
from lem.cli import place


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem criteria digest`."""

    slug: str
    path: str | None = None


def run(call: Call) -> marks.Mark:
    """The mark of the criteria of FILE, or of the task's criteria as they stand."""
    named = Path(call.path) if call.path else None
    return marks.marked(place.folder(), call.slug, named)


COMMAND = click.Command(
    "digest",
    params=[
        click.Argument(["slug"]),
        click.Option(["--file", "path"], help="the criteria to mark"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The digest of a task's criteria, or of a file.",
)
