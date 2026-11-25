"""`lem serve remove`: take a repository out of the list of workspaces.

    lem serve remove DIR

The main checkout of the repository DIR is in leaves the machine's list; a repository that is
gone is taken out by the path it had, and one not on the list is refused.
"""

import os
from pathlib import Path

import click
import msgspec

from lem.board import editing
from lem.kernel import folders


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve remove`."""

    folder: str


def run(call: Call) -> editing.Changed:
    """Take the repository off the list."""
    home = folders.home_for_writing(os.environ)
    return editing.removed(home, Path(call.folder))


COMMAND = click.Command(
    "remove",
    params=[
        click.Argument(["folder"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Take a repository out of the list of workspaces.",
)
