"""A board over one workspace for the owner's acts: the app of the server through Starlette's test
client, a workspace with Lem set up, and the ports of every act bound to fakes (`wiring.bound`
replaced), with Lem's home folder in the case's own folder."""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest
from starlette.testclient import TestClient

from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.ports import fake_ports
from fakes.records import MOMENT
from lem.app import wiring
from lem.board import app, install, machine, workspaces
from lem.board.facts import Facts
from lem.kernel import folders
from lem.store import places
from unit.sessions.terminal import LookingTerminal, with_caller

if TYPE_CHECKING:
    from pathlib import Path

    import httpx

PORT = 4999
ORIGIN = f"http://127.0.0.1:{PORT}"
PHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)"


@dataclass
class Board:
    """The client of the board, the workspace's checkout and state, the address of its
    workspace, the terminal every act's ports hold, and whether the app is the door's."""

    client: TestClient
    checkout: Path
    state: Path
    base: str
    terminal: LookingTerminal
    home: Path

    def post(self, path: str, fields: dict[str, str], **headers: str) -> httpx.Response:
        """A form of the board's own page, posted to `path` under the workspace."""
        sent = {"origin": ORIGIN, "sec-fetch-site": "same-origin", **headers}
        return self.client.post(
            f"{self.base}{path}", data=fields, headers=sent, follow_redirects=False
        )


def made_app(home: Path, *, door: bool) -> TestClient:
    """The board server's app for Lem's home folder `home`; the door's app says so."""
    facts = Facts(
        pid=os.getpid(),
        port=PORT,
        url=f"{ORIGIN}/",
        host=machine.machine_name(),
        install=install.install_of(),
        home=str(home),
        started=MOMENT,
    )
    served = app.made(facts, home=home, listen="127.0.0.1", stop=lambda: None)
    served.state.door = door
    return TestClient(served, base_url=ORIGIN, client=("127.0.0.1", 50000))


def board_of(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, door: bool) -> Board:
    """A board over a workspace in `tmp_path`, its acts on fakes."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    home = folders.home_for_writing({"XDG_CONFIG_HOME": str(tmp_path / "config")})
    checkout = tmp_path / "shop"
    (checkout / ".git").mkdir(parents=True)
    (checkout / ".lem").mkdir()
    state = places.state_of(checkout)
    workspaces.noted(home, checkout)
    terminal = with_caller()
    git = ModelGit(checkout=checkout)
    ports = fake_ports(git, LocalForge(remote=git), terminal)
    monkeypatch.setattr(wiring, "bound", lambda place: ports)
    host = machine.machine_name()
    client = made_app(home, door=door)
    return Board(client, checkout, state, f"/{host}/shop", terminal, home)


@pytest.fixture
def board(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Board:
    """A board on this Mac's main listener."""
    return board_of(tmp_path, monkeypatch, door=False)


@pytest.fixture
def door(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Board:
    """A board through the tailnet door, whose own check ran before the route."""
    return board_of(tmp_path, monkeypatch, door=True)
