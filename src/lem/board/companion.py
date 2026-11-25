"""A page of Lem opened as a page companion of the session that asks, beside it and never over
it: the board, a task's board, or an HTML file (`board.show` on `main`). A command run outside
agterm is refused before anything starts."""

import os
from typing import TYPE_CHECKING

from lem.app import wiring
from lem.board.boards import Opened, page_of
from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.ports.place import Place

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.terminal import Terminal


def beside(folder: Path) -> tuple[Terminal, str]:
    """The terminal and the session the command runs in, which a companion opens beside;
    refused outside agterm."""
    home = paths.home(os.environ)
    terminal = wiring.bound(
        Place(checkout=folder, home=home, environ=os.environ)
    ).terminal
    here = terminal.here()
    if here is None:
        raise Refusal(
            "no-session",
            "not inside an agterm session, so no companion can open",
            "lem board --no-open prints the board's address; give the owner the address",
        )
    return terminal, here


def page_opened(folder: Path, named: str, name: str | None) -> Opened:
    """The HTML file `named`, opened as a page companion."""
    page = page_of(named)
    terminal, here = beside(folder)
    url = page.as_uri()
    terminal.show(here, url, "companion")
    title = name or page.stem
    return Opened(url=url, name=title, page=str(page), beside=here)
