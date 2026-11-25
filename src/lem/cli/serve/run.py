"""`lem serve run`: run the board server in the foreground.

    lem serve run [--host HOST] [--verbose]

A stub until the step `slice-board` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem serve run`."""

    host: str | None = None
    verbose: bool = False


def run(call: Call) -> None:
    """Refuse until the step `slice-board` builds `lem serve run`."""
    raise not_built("serve run", "slice-board")


COMMAND = click.Command(
    "run",
    params=[
        click.Option(["--host"], help="the address to listen on (default: 127.0.0.1)"),
        click.Option(["--verbose"], is_flag=True, help="log each request on stderr"),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Run the board server in the foreground.",
)
