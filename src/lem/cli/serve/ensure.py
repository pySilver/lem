"""`lem serve ensure`: make sure one board server runs, from this code.

    lem serve ensure

A server of the same install stays while its code and settings are those of the files now; one
of another install stays unless this one's release is higher, and one of the release before
this one always stays, with every file of the home folder. `LEM_SERVE=off` starts nothing, ends
nothing and writes nothing. Run in a workspace, it puts that workspace on the list of this
build's server.
"""

import os
from typing import TYPE_CHECKING

import click
import msgspec

from lem.board import ensure
from lem.cli import place

if TYPE_CHECKING:
    from lem.board.facts import Shown


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve ensure`."""


def run(call: Call) -> Shown:
    """Make sure the server runs, and say which serves."""
    return ensure.ensure(os.environ, place.folder())


COMMAND = click.Command(
    "ensure",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Make sure one board server runs, from this code.",
)
