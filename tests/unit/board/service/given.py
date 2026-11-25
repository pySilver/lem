"""The board's app over one workspace, through Starlette's test client: the main listener, and the
door on a port of its own when a case opens it. No server, no socket, no network."""

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from starlette.testclient import TestClient

from fakes.records import MOMENT
from lem.board import app, install, workspaces
from lem.board.facts import Facts
from lem.board.serving import Serving
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.door import Door

MAIN = 4999
DOOR = 4998
MAC = "studio.example.ts.net"
OWNER = "owner@example.com"
HOST = "studio"


@dataclass
class Board:
    """A board over one workspace: Lem's home folder, the workspace, the app, and each stop."""

    home: Path
    checkout: Path
    state: Path
    app: object
    stops: list[str] = field(default_factory=list)

    def main(self, client: tuple[str, int] = ("127.0.0.1", 50000)) -> TestClient:
        """A client of the main listener, from `client`."""
        return TestClient(self.app, base_url=f"http://127.0.0.1:{MAIN}", client=client)

    def door(self) -> TestClient:
        """A client of the door's listener, as `tailscale serve` passes a request on."""
        return TestClient(
            self.app, base_url=f"http://127.0.0.1:{DOOR}", client=("127.0.0.1", 50001)
        )


def workspace_at(folder: Path) -> Path:
    """A main checkout where Lem is set up."""
    (folder / ".git").mkdir(parents=True)
    (folder / ".lem").mkdir()
    return folder


def made(tmp_path: Path, door: Door | None) -> Board:
    """The board of a workspace `shop`, with the door open when `door` is given."""
    home = tmp_path / "lem-home"
    checkout = workspace_at(tmp_path / "shop")
    workspaces.noted(home, checkout)
    facts = Facts(
        pid=os.getpid(),
        port=MAIN,
        url=f"http://127.0.0.1:{MAIN}/",
        host=HOST,
        aliases=("old-name",),
        install=install.install_of(),
        home=str(home),
        door=None if door is None else door.port,
        tailnet=None if door is None else door.url(),
        started=MOMENT,
    )
    board = Board(home, checkout, places.state_of(checkout), None)
    serving = Serving(
        home=home,
        environ=os.environ,
        listen="127.0.0.1",
        stop=lambda: board.stops.append("stop"),
        door=door,
    )
    board.app = app.made(facts, serving)
    return board
