"""`lem board`: the board of a workspace or of one task, or any page of Lem to read, opened as a
page companion of the session that asks, never as an overlay over it (the owner, 2026-11-18:
"Command like this and possibly others that opens html overlay should be opened in companion";
`board.py` on `main`).

The board is the machine's board server's page: a run makes sure the server runs, puts the
workspace's main checkout on the machine's list (a state folder of example tasks stays out of it
unless `lem serve add` adds it), and gives the address of the workspace's board,
`http://127.0.0.1:PORT/HOST/WORKSPACE/`, or of one task, `.../tasks/SLUG`, and through the
tailnet door when it is open. `--no-open` prints the address and opens nothing.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from lem.board import ensure, workspaces
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.store import places

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.board.facts import Shown

DEMO_TEXT = b"The tasks in this folder are examples. lem board --demo made this file.\n"
PAGES = (".html", ".htm")
TITLE = "Lem board · "


class Opened(msgspec.Struct, frozen=True, kw_only=True, omit_defaults=True):
    """What `lem board` prints: the address, the companion's name, the address through the
    tailnet door, the page shown, and the session the companion opened beside."""

    url: str
    name: str
    tailnet_url: str | None = None
    page: str | None = None
    beside: str | None = None


def task_checked(space: places.Workspace, slug: str) -> None:
    """Refuse a task that the workspace does not have, naming those it has."""
    if (places.task_folder(space.state, slug) / "task.json").is_file():
        return
    found = sorted(path.parent.name for path in space.state.glob("tasks/*/task.json"))
    known = ", ".join(found) or "none yet"
    raise Refusal(
        "no-task",
        f"no task {slug!r} in {space.checkout}",
        f"name one of its tasks: {known}",
    )


def demo_marked(space: places.Workspace) -> None:
    """Mark the state folder as holding example tasks, for good: every board of it says so."""
    (space.state / workspaces.DEMO).write_bytes(DEMO_TEXT)


def page_of(named: str) -> Path:
    """The HTML file `--page` names; refused for anything else."""
    page = Path(named).resolve()
    if not page.is_file() or page.suffix.lower() not in PAGES:
        raise Refusal(
            "no-page", f"--page {page} is not an HTML file", "give the page to open"
        )
    return page


def served(environ: Mapping[str, str], space: places.Workspace) -> Shown:
    """The server that serves this machine, started when none runs; refused under
    `LEM_SERVE=off`, and for a server of another install, which this one leaves."""
    if environ.get("LEM_SERVE") == ensure.NO_START:
        raise Refusal(
            "no-server",
            "LEM_SERVE=off is set: lem board asks no server and starts none",
            "unset LEM_SERVE",
        )
    shown = ensure.ensure(environ, space.checkout)
    if shown.another_install:
        raise Refusal("other-install", f"{shown.said}", "use that install's lem board")
    if shown.url is None or shown.host is None:
        raise Refusal(
            "no-server", f"no board server runs: {shown.said}", "run it again"
        )
    return shown


def board_of(home: Path, host: str, checkout: Path) -> str:
    """The path of the listed main checkout's board, `HOST/NAME/`; refused when it is not on
    the list."""
    path = str(checkout.resolve())
    named = workspaces.named(workspaces.listed(home), host)
    found = next((name for name, at in named if at == path), None)
    if found is None:
        raise Refusal(
            "not-listed",
            f"the board server does not show {checkout}",
            f"lem serve add {checkout}",
        )
    return f"{host}/{found}/"


def address(
    environ: Mapping[str, str], space: places.Workspace, slug: str | None
) -> Opened:
    """The address of the workspace's board, or of its task `slug`, on a server that runs."""
    shown = served(environ, space)
    board = board_of(paths.home(environ), shown.host or "", space.checkout)
    tail = f"{board}tasks/{slug}" if slug else board
    door = None if shown.tailnet is None else shown.tailnet + tail
    return Opened(
        url=f"{shown.url}{tail}", name=TITLE + space.checkout.name, tailnet_url=door
    )
