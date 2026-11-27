"""`lem board`: open the board of all tasks, or of one task, or a page of Lem, as a companion.

    lem board [--task SLUG] [--follow] [--no-open] [--demo] [--page FILE [--name NAME]]

It makes sure the board server runs, puts the workspace on its list, and opens the address of
the workspace's board, or of one task's, as a page companion of the session that asks;
`--no-open` prints the address and opens nothing. `--demo` marks the state folder as holding
example tasks, for good. `--page FILE` opens that HTML file the same way, and `--name` names its
companion. With `LEM_SERVE=off` it asks no server and starts none; a server of another install
is left as it is, and the command says which.
"""

import os

import click
import msgspec

from lem.board import boards, companion
from lem.cli import place
from lem.cli.board import page_copy
from lem.kernel.errors import Refusal
from lem.store import places


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem board`."""

    task: str | None = None
    follow: bool = False
    no_open: bool = False
    demo: bool = False
    page: str | None = None
    name: str | None = None


def checked(call: Call) -> None:
    """Refuse the words that do not go together."""
    if call.page is not None and (call.task or call.demo or call.no_open):
        raise Refusal(
            "board-words",
            "--page opens one file; --task, --demo and --no-open belong to the board",
            "give --page alone, or the board's words alone",
        )
    if call.follow:
        raise Refusal(
            "board-follow",
            "--follow selects the companion, and the terminal's port gives no companion's "
            "id to select yet",
            "open it without --follow, and select the companion by hand",
        )
    if call.name is not None and call.page is None:
        raise Refusal(
            "board-words",
            "--name goes with --page: the board names itself",
            "drop --name",
        )


def run(call: Call) -> boards.Opened:
    """Open the board, a task's board or a page, or give the board's address."""
    checked(call)
    folder = place.folder()
    if call.page is not None:
        return companion.page_opened(folder, page_copy.openable(call.page), call.name)
    space = places.workspace(folder)
    if call.task is not None:
        boards.task_checked(space, call.task)
    if call.demo:
        boards.demo_marked(space)
    if call.no_open:
        return boards.address(os.environ, space, call.task)
    terminal, here = companion.beside(folder)
    opened = boards.address(os.environ, space, call.task)
    terminal.show(here, opened.url, "companion")
    return msgspec.structs.replace(opened, beside=here)


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
