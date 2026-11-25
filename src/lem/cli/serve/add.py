"""`lem serve add`: put a repository into the list of workspaces.

    lem serve add DIR

The main checkout of the repository DIR is in goes on the machine's list, which the board server
shows at its next look; a checkout where Lem is not set up is refused.
"""

import os
from pathlib import Path

import click
import msgspec

from lem.board import editing
from lem.kernel import folders


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve add`."""

    folder: str


def run(call: Call) -> editing.Changed:
    """Put the repository on the list."""
    home = folders.home_for_writing(os.environ)
    return editing.added(home, Path(call.folder))


COMMAND = click.Command(
    "add",
    params=[
        click.Argument(["folder"]),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Put a repository into the list of workspaces.",
)
