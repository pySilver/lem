"""`lem board`: open the board of all tasks, or of one task.

    lem board [--task SLUG] [--follow] [--no-open] [--demo] [--page FILE [--name NAME]]

Built so far: `lem board --no-open`, which makes sure the server runs, puts the workspace on its
list and prints the address of the workspace's board. With `LEM_SERVE=off` it asks no server and
writes nothing; a server of another install is left as it is, and the command says which.
Opening it as a companion, a task's board, the example tasks and a page refuse `not-built` until
the step `board-service` builds them.
"""

import os

import click
import msgspec

from lem.board import ensure, workspaces
from lem.cli import place
from lem.cli.stub import DESIGN, NOT_BUILT
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.store import places


class Address(msgspec.Struct, frozen=True, kw_only=True):
    """The address of a workspace's board."""

    url: str


class Call(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    """The words of `lem board`."""

    task: str | None = None
    follow: bool = False
    no_open: bool = False
    demo: bool = False
    page: str | None = None
    name: str | None = None


def built(call: Call) -> None:
    """Refuse what is not built: every call but `--no-open` alone."""
    unbuilt = (call.task, call.follow, call.demo, call.page, call.name)
    if any(unbuilt) or not call.no_open:
        raise Refusal(
            NOT_BUILT,
            "`lem board` opens no page yet: only lem board --no-open is built",
            f"the step `board-service` builds it ({DESIGN}, part 9)",
        )


def run(call: Call) -> Address:
    """Make sure the server runs, and give the address of this workspace's board."""
    built(call)
    if os.environ.get("LEM_SERVE") == ensure.NO_START:
        raise Refusal(
            "no-server",
            "LEM_SERVE=off is set: lem board asks no server and starts none",
            "unset LEM_SERVE",
        )
    space = places.workspace(place.folder())
    shown = ensure.ensure(os.environ, space.checkout)
    if shown.another_install:
        raise Refusal("other-install", f"{shown.said}", "use that install's lem board")
    if shown.url is None or shown.host is None:
        raise Refusal(
            "no-server", f"no board server runs: {shown.said}", "run it again"
        )
    home = paths.home(os.environ)
    name = workspaces.name_of(home, shown.host, space.checkout)
    return Address(url=f"{shown.url}{shown.host}/{name}/")


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
