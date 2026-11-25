"""`lem serve run`: run the board server in the foreground.

    lem serve run [--host HOST] [--port N] [--verbose]

It serves until a stop, SIGTERM or Ctrl-C, on the port named, else the machine's `[serve] port`.
A home folder of Lem that is not the owner's (a test's, a trial's) never takes the owner's two
ports. Run in a workspace, it puts that workspace on the list the server shows.
"""

import importlib
import os
from typing import TYPE_CHECKING

import click
import msgspec

from lem.board import machine, workspaces
from lem.cli import place
from lem.kernel import paths

if TYPE_CHECKING:
    from lem.board.facts import Served

HOST = "127.0.0.1"


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve run`."""

    host: str | None = None
    port: int | None = None
    verbose: bool = False


def run(call: Call) -> Served:
    """Serve the board in this process until it stops, and say which server it was."""
    home = paths.home(os.environ)
    port = machine.port_of(home, os.environ, call.port)
    workspaces.noted(home, place.folder())
    server = importlib.import_module("lem.board.server")
    return server.run(port, call.host or HOST, verbose=call.verbose, home=home)


COMMAND = click.Command(
    "run",
    params=[
        click.Option(["--host"], help="the address to listen on (default: 127.0.0.1)"),
        click.Option(
            ["--port"],
            type=click.IntRange(1, machine.HIGHEST_PORT),
            help="the port to serve (default: [serve] port of machine.toml)",
        ),
        click.Option(["--verbose"], is_flag=True, help="log each request on stderr"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Run the board server in the foreground.",
)
