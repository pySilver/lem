"""Serve the afternoon through Lem's own Starlette routes on a test-owned loopback socket."""

import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from socket import AF_INET, SOCK_STREAM, socket
from threading import Event, Thread
from typing import TYPE_CHECKING

import uvicorn

from fakes.forge import LocalForge
from fakes.git import ModelGit
from fakes.ports import fake_ports
from fakes.repo import git_env, run_git
from fakes.terminal import FakeTerminal
from fixtures.board import beside
from fixtures.board.moments import HOST, NOW
from lem.adapters import git_cli
from lem.app import wiring
from lem.board import app, install, workspaces
from lem.board.duties.memory import MEMORY
from lem.board.facts import Facts
from lem.board.serving import Serving
from lem.kernel import clock
from lem.ports.terminal import Pane
from lem.store import places, tasks

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    import pytest
    from starlette.applications import Starlette

    from lem.ports.terminal import Opening
    from lem.records.record import Record

LOCAL = "127.0.0.1"
OWNER_PORTS = frozenset({4536, 4537})


@dataclass
class Terminal(FakeTerminal):
    """The test can hold a session open request while the board refreshes."""

    selections: list[str] = field(default_factory=list)
    requested: Event = field(default_factory=Event)
    proceed: Event = field(default_factory=Event)
    pause: bool = False

    def select(self, session: str) -> None:
        super().select(session)
        self.selections.append(session)

    def open(self, opening: Opening) -> str:
        self.requested.set()
        if self.pause and not self.proceed.wait(20):
            raise AssertionError("the browser case did not release the session open")
        return super().open(opening)


@dataclass(frozen=True)
class Board:
    """The workspace and the real address of its running board."""

    checkout: Path
    terminal: Terminal
    url: str
    forge: LocalForge

    @property
    def state(self) -> Path:
        return places.state_of(self.checkout)

    def task(self, slug: str, tail: str = "") -> str:
        return f"{self.url}/tasks/{slug}{tail}"

    def record(self, slug: str) -> Record:
        return tasks.read(self.state, slug)


def afternoon(folder: Path) -> Path:
    """Put the demo's files in a real repository for the acts that need Git."""
    checkout = beside.lay(folder)
    beside.write(
        checkout / ".lem/settings.toml", '[branch]\nbase = "main"\nland = "owner"\n'
    )
    beside.write(checkout / ".gitignore", ".lem/state/\n.lem/worktrees/\n")
    beside.write(
        checkout / "invoice/footer.py", "def footer(order):\n    return order.address\n"
    )
    beside.write(checkout / "AGENTS.md", "# The shop\n")
    beside.write(
        checkout / "tests/test_export.py", "def test_monthly():\n    assert True\n"
    )
    run_git(checkout, "init", "--quiet", "--initial-branch=main")
    run_git(checkout, "add", "--all")
    run_git(checkout, "commit", "--quiet", "--message", "the demo afternoon")
    return checkout


def terminal_for(checkout: Path) -> Terminal:
    terminal = Terminal()
    for slug, acts in beside.ACTS:
        for act in acts:
            if isinstance(act, beside.Open):
                terminal.panes[act.session] = Pane(
                    id=act.session,
                    name=slug,
                    cwd=str(checkout),
                    workspace=act.workspace,
                )
    return terminal


def application(
    checkout: Path,
    home: Path,
    port: int,
    terminal: Terminal,
    patch: pytest.MonkeyPatch,
    forge: LocalForge,
) -> Starlette:
    workspaces.changed(home, str(checkout), add=True)
    env = git_env()
    fake = ModelGit(checkout)
    ports = fake_ports(fake, forge, terminal)
    patch.setattr(
        wiring, "bound", lambda place: replace(ports, git=git_cli.bind(place))
    )
    patch.setattr(clock, "now", lambda: NOW)
    facts = Facts(
        pid=os.getpid(),
        port=port,
        url=f"http://{LOCAL}:{port}/",
        host=HOST,
        home=str(home),
        install=install.install_of(),
        started=NOW,
    )
    serving = Serving(home=home, environ=env, listen=LOCAL, stop=lambda: None)
    return app.made(facts, serving)


@contextmanager
def serve(folder: Path, patch: pytest.MonkeyPatch) -> Generator[Board]:
    """Hold a kernel-assigned port from bind through shutdown."""
    assert os.environ["LEM_SERVE"] == "off"
    home = folder / "lem-home"
    checkout = afternoon(folder)
    terminal = terminal_for(checkout)
    forge = LocalForge(ModelGit(checkout), name="acme/shop")
    with socket(AF_INET, SOCK_STREAM) as listener:
        listener.bind((LOCAL, 0))
        port = listener.getsockname()[1]
        assert port not in OWNER_PORTS
        listener.listen()
        served = application(checkout, home, port, terminal, patch, forge)
        server = uvicorn.Server(
            uvicorn.Config(
                served, log_config=None, access_log=False, timeout_graceful_shutdown=5
            ),
        )
        thread = Thread(target=server.run, kwargs={"sockets": [listener]})
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while (
                not server.started and thread.is_alive() and time.monotonic() < deadline
            ):
                time.sleep(0.02)
            assert server.started, "the scratch board did not start"
            yield Board(
                checkout,
                terminal,
                f"http://{LOCAL}:{port}/{HOST}/{checkout.name}",
                forge,
            )
        finally:
            terminal.proceed.set()
            server.should_exit = True
            thread.join(timeout=10)
            assert not thread.is_alive(), "the scratch board did not stop"
            for worker in MEMORY.of(checkout).merging.values():
                worker.join(timeout=10)
                assert not worker.is_alive(), "the scratch merge worker did not stop"
