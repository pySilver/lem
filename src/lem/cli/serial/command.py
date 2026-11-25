"""`lem serial`: run one command under the repository's one serial lock.

    lem serial -- COMMAND...

The command's own output is the output, and its exit status is the exit, with no envelope, as a
test runner's caller expects (`project.cmd_serial` on `main`); a refusal before the command
starts prints its envelope with exit 1. The step `land-checks` owns it.
"""

from typing import NoReturn

import click
import msgspec

from lem.app.landing import checks_serial
from lem.cli import place


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serial`."""

    command: tuple[str, ...]


def run(call: Call) -> NoReturn:
    """Run the command under the lock, and exit as it did."""
    code = checks_serial.ran(place.folder(), call.command)
    raise click.exceptions.Exit(code)


COMMAND = click.Command(
    "serial",
    params=[
        click.Argument(["command"], nargs=-1, required=True),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Run one command under the repository's one serial lock.",
)
