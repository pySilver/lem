"""`lem task split`: a feature in parts, from the criteria the owner approved.

    lem task split NAME --file CRITERIA

The file is the feature's approved criteria, word for word, with a `### SLUG: WORDS` heading for
each part and `### The whole feature`. `feature/NAME` is cut from origin's base and pushed, and
each part is a task of its own that waits for the part before it, unless its heading ends in
`(independent)`; NAME waits for all of them (`app/tasks/split.py`). A split run again makes only
what is missing.
"""

from pathlib import Path

import click
import msgspec

from lem.app.tasks import split
from lem.cli import place


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem task split`."""

    slug: str
    path: str


def run(call: Call) -> split.Split:
    """Split the feature into its parts."""
    return split.split(place.folder(), call.slug, Path(call.path))


COMMAND = click.Command(
    "split",
    params=[
        click.Argument(["slug"]),
        click.Option(
            ["--file", "path"],
            required=True,
            help=(
                "the feature's criteria the owner approved, with a heading for each part "
                "and one for the whole feature"
            ),
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Split a feature into its parts, from the criteria the owner approved.",
)
