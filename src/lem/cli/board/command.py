"""`lem board`: open the board of all tasks, or of one task.

    lem board [--task SLUG] [--follow] [--no-open] [--demo] [--page FILE [--name NAME]]

A stub until the step `board-service` builds it: it refuses `not-built`.
"""

import click
import msgspec

from lem.cli.stub import not_built


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem board`."""

    task: str | None = None
    follow: bool = False
    no_open: bool = False
    demo: bool = False
    page: str | None = None
    name: str | None = None


def run(call: Call) -> None:
    """Refuse until the step `board-service` builds `lem board`."""
    raise not_built("board", "board-service")


COMMAND = click.Command(
    "board",
    params=[
        click.Option(["--task"], help="open the board of this task"),
        click.Option(
            ["--follow"], is_flag=True, help="switch to the board after it opens"
        ),
        click.Option(
            ["--no-open"],
            is_flag=True,
            help="make sure the server runs, print the board's address, open nothing",
        ),
        click.Option(
            ["--demo"],
            is_flag=True,
            help="the state folder holds example tasks, and the boards say so",
        ),
        click.Option(["--page"], help="open this HTML file as a page companion"),
        click.Option(
            ["--name"],
            help="with --page: the companion's name (default: the file's name)",
        ),
    ],
    callback=lambda **given: run(msgspec.convert(given, Call)),
    help="Open the board of all tasks, or of one task.",
)
