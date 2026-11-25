"""`lem serve stop`: end the board server that runs.

    lem serve stop

It ends the server of this install and home folder of Lem on the machine's port, and waits until
the port is free; a server of another install is left as it is, and a port that another program
or another home folder holds is refused, never stopped.
"""

import os
from typing import TYPE_CHECKING

import click
import msgspec

from lem.board import stopping

if TYPE_CHECKING:
    from lem.board.facts import Stopped


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve stop`."""


def run(call: Call) -> Stopped:
    """End the server, and say which ended."""
    return stopping.stop(os.environ)


COMMAND = click.Command(
    "stop",
    params=[],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="End the board server that runs.",
)
