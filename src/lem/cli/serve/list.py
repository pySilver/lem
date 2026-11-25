"""`lem serve list`: the workspaces as the server shows them.

    lem serve list

Each workspace of the machine's list whose checkout still has Lem set up, with its name in the
board's addresses, its address, and how many tasks wait for the owner, build and are in their
checks (`GET /api/workspaces` gives the same).
"""

import os

import click
import msgspec

from lem.board import machine, tailnet
from lem.board.counts import Counts, Rows
from lem.kernel import paths


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve list`."""


def run(call: Call) -> Rows:
    """The workspaces, each with its counts."""
    host, _ = machine.names_of(tailnet.name_of(os.environ))
    return Counts().rows(paths.home(os.environ), host)


COMMAND = click.Command(
    "list",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="The workspaces as the server shows them.",
)
