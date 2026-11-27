"""The owner's click on "Open the session" of a joined machine's task: two board apps of Lem in one
process, `book` where he works and `mini` where the task runs, each with a stand-in for its
agterm (`contract/agterm_standin.py`). The book relays the task's page, reads the session on the
mini, and attaches it in its own agterm with its companions; a second click selects that row."""

import asyncio
import json
import os
from typing import TYPE_CHECKING

import httpx

from contract.agterm_standin import Standin, install
from fakes.records import MOMENT, record
from fakes.repo import RealRepo
from lem.addons.peers import registry, table
from lem.app.sessions import log
from lem.app.sessions.acts import Open
from lem.board import app, facts, serving
from lem.board import workspaces as board_workspaces
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from starlette.applications import Starlette

PORT = 19047
BOOK = f"http://127.0.0.1:{PORT}"
SLUG = "refund-line-on-receipt"
SESSION = "6F1C2A30-0000-4000-8000-000000000007"
TALK = "6F1C2A30-0000-4000-8000-000000000009"
SENT = {"origin": BOOK, "sec-fetch-site": "same-origin"}
JUMP = f"/mini/shop/agterm/{SESSION}"


def shop(folder: Path) -> Path:
    """The mini's checkout: one task whose session Lem opened, on a board of example tasks
    whose sessions live from Lem's acts alone."""
    repo = RealRepo.init(
        folder / "repo", {".lem/settings.toml": b'[branch]\nbase = "main"\n'}
    )
    checkout = repo.checkout.rename(folder / "shop")
    state = places.state_of(checkout)
    tasks.create(state, record(SLUG, status="building"))
    opened = Open(at=MOMENT, session=SESSION, name=SLUG, phase="build", why="new")
    log.append(places.task_folder(state, SLUG), opened)
    (state / "demo").touch()
    return checkout


def board(home: Path, host: str, environ: dict[str, str]) -> Starlette:
    """A board app of `host`, whose agterm is the stand-in of `environ`."""
    return app.made(
        facts.Facts(
            pid=os.getpid(),
            port=PORT,
            url=f"{BOOK}/",
            host=host,
            home=str(home),
            install=facts.Install(version="0.99.0", package=__file__),
            started=MOMENT,
        ),
        serving.Serving(
            home=home, environ=environ, listen="127.0.0.1", stop=lambda: None
        ),
    )


def macs(tmp_path: Path) -> tuple[Starlette, Standin, Standin]:
    """The book's board, which joined the mini, and the stand-in of each Mac's agterm."""
    mini_agterm = install(
        tmp_path / "mini-agterm",
        [
            {"id": SESSION, "name": SLUG, "workspace": "W-MINI"},
            {"id": TALK, "name": "talk", "workspace": "W-MINI", "parent": SESSION},
        ],
    )
    book_agterm = install(
        tmp_path / "book-agterm", [{"id": "L-1", "name": "main", "workspace": "W-BOOK"}]
    )
    book_agterm.change(hosts={"mini": str(mini_agterm.folder)})
    mini_home = tmp_path / "mini-home"
    board_workspaces.changed(mini_home, str(shop(tmp_path)), add=True)
    mini = board(mini_home, "mini", mini_agterm.environ(HOME=str(tmp_path)))
    book_home = tmp_path / "book-home"
    table.change(book_home, "mini", PORT)
    book = board(book_home, "book", book_agterm.environ(HOME=str(tmp_path)))

    async def address(host: str, port: int) -> str:
        # The transport stands in for the tailnet: the mini answers as its own listener does.
        assert (host, port) == ("mini", PORT)
        return BOOK

    book.state.peer_registry = registry.Registry(
        home=book_home,
        own="book",
        address=address,
        transport=httpx.ASGITransport(app=mini),
    )
    return book, book_agterm, mini_agterm


def guarded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An agtermctl first on the process's own PATH that only records: no step may reach the
    owner's agterm through the environment of the process."""
    guard = install(tmp_path / "guard")
    monkeypatch.setenv("PATH", f"{guard.folder / 'bin'}:/usr/bin:/bin")
    monkeypatch.setenv("AGTERM_STANDIN", str(guard.folder))
    return guard.folder


def zmx(agterm: Standin) -> list[list[str]]:
    """The calls of the book's agterm that reached the mini or attached its session."""
    return [call for call in agterm.calls() if call[0] == "zmx"]


def test_the_jump_attaches_the_minis_session_then_selects_its_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    guard = guarded(tmp_path, monkeypatch)
    book, book_agterm, mini_agterm = macs(tmp_path)

    async def run() -> list[httpx.Response]:
        transport = httpx.ASGITransport(app=book)
        async with httpx.AsyncClient(transport=transport, base_url=BOOK) as client:
            page = await client.get(f"/mini/shop/tasks/{SLUG}")
            first = await client.post(JUMP, headers=SENT)
            again = await client.post(JUMP, headers=SENT)
            mini_agterm.change(restore="rerun")
            refused = await client.post(JUMP, headers=SENT)
        return [page, first, again, refused]

    page, first, again, refused = asyncio.run(run())
    assert page.status_code == 200, page.text
    assert 'data-agterm-url-value="/mini/shop/agterm"' in page.text
    assert f'data-agterm-session-param="{SESSION}"' in page.text
    assert first.json() == {
        "done": True,
        "said": "Opened the session of mini on this Mac.",
    }
    assert again.json() == {"done": True, "said": "Switched to the session."}
    assert zmx(book_agterm) == [
        ["zmx", "tree", "mini", "--json"],
        ["zmx", "attach", "mini", SESSION, "--companions", "--json"],
    ]
    rows = {row["id"]: row for row in book_agterm.sessions()}
    assert rows["R-1"]["remoteSessionID"] == SESSION and rows["R-1"]["active"]
    assert rows["R-1-C1"]["remoteSessionID"] == TALK
    assert refused.status_code == 422
    assert "the agterm on mini does not run Live sessions" in refused.json()["said"]
    assert ["restore", "mode", "--json"] in mini_agterm.calls()
    assert not (guard / "calls.jsonl").exists()
    assert (
        json.loads((mini_agterm.folder / "tree.json").read_text())["sessions"][0]["id"]
        == SESSION
    )
