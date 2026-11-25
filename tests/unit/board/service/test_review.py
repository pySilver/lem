"""Board service boundaries, with no live listener or Tailscale service."""

import sys
from contextlib import ExitStack
from pathlib import Path
from threading import get_ident
from typing import TYPE_CHECKING

import anyio
import httpx
import pytest
from starlette.requests import Request

from lem import __main__ as entry
from lem.board import claim, doorway, editing, ensure, halt, machine, server, watched
from lem.board.door import Door
from lem.board.push import acts
from lem.board.push import body as push_body
from lem.cli.serve import run
from lem.kernel import folders
from lem.kernel.errors import Refusal
from unit.board.service import tailscale_stand_in as stand_in
from unit.board.service.given import DOOR, MAC, MAIN, Board, made, workspace_at

if TYPE_CHECKING:
    from starlette.types import Message, Scope

FIRST = 5101
SECOND = 5102


def test_a_scratch_home_cannot_close_the_owners_door(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = folders.home_marked(tmp_path / "config" / "lem")
    settings = home / machine.MACHINE
    before = f"[serve]\nport = {FIRST}\n"
    settings.write_text(before)
    cli = stand_in.made(tmp_path / "ts")
    environ = {
        **stand_in.environ(cli),
        "HOME": str(tmp_path),
        "XDG_CONFIG_HOME": str(home.parent),
        "LEM_SERVE": "off",
    }
    calls = []
    monkeypatch.setattr(ensure, "ensure", lambda *_: calls.append("ensure"))
    with pytest.raises(Refusal) as refused:
        doorway.closed(environ, tmp_path)
    assert refused.value.code == "owner-port"
    assert settings.read_text() == before
    assert calls == []
    assert stand_in.calls(cli) == []


def test_foreground_claim_precedes_vacancy_and_ends_on_bind_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    calls = []

    def vacant(_home: Path, _environ: object, port: int, _host: str) -> int:
        calls.append(("vacancy", port))
        if port == FIRST:
            with pytest.raises(Refusal) as refused:
                run.run(run.Call(port=SECOND))
            assert refused.value.code == "running"
        return port

    def bind(port: int, *_: object, **__: object) -> None:
        calls.append(("bind", port))
        raise Refusal("port-held", "bind failed", "choose another port")

    monkeypatch.setattr(run.vacant, "vacant", vacant)
    monkeypatch.setattr(server, "run", bind)
    for port in (FIRST, SECOND):
        with pytest.raises(Refusal) as refused:
            run.run(run.Call(port=port))
        assert refused.value.code == "port-held"
    assert calls == [
        ("vacancy", FIRST),
        ("bind", FIRST),
        ("vacancy", SECOND),
        ("bind", SECOND),
    ]


def test_stop_waits_for_the_claim_after_the_listener_closes(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    waits = []
    monkeypatch.setattr(halt, "free", lambda *_: True)
    with ExitStack() as old:
        old.enter_context(claim.held(board.home))

        def finished(seconds: float) -> None:
            waits.append(seconds)
            old.close()

        monkeypatch.setattr(halt.time, "sleep", finished)
        halt.gone(MAIN, board.app.state.facts, "127.0.0.1")
    assert waits == [halt.POLL]


def test_the_door_reads_the_login_off_the_shared_event_loop(tmp_path: Path) -> None:
    new = "new-owner@example.com"
    threads = []

    def reread(_before: str) -> str:
        threads.append(get_ident())
        return new

    door = Door(name=MAC, port=DOOR, owner="old-owner@example.com", reread=reread)
    door.read_at = float("-inf")
    board = made(tmp_path, door)

    async def check() -> None:
        transport = httpx.ASGITransport(app=board.app)
        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.get(
                f"http://127.0.0.1:{DOOR}/api/workspaces",
                headers={"Host": MAC, "Tailscale-User-Login": new},
            )
        assert response.status_code == 200
        [worker] = threads
        assert worker != get_ident()

    anyio.run(check)


@pytest.mark.parametrize(
    ("words", "status"), [((), 0), (("--help",), 0), (("taks",), 2)]
)
def test_help_and_unknown_commands_do_not_start_the_board(
    words: tuple[str, ...], status: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    starts = []
    monkeypatch.setattr(entry.look, "started", lambda *_: starts.append("start"))
    monkeypatch.setattr(sys, "argv", ["lem", *words])
    monkeypatch.delenv("LEM_SERVE")
    with pytest.raises(SystemExit) as ended:
        entry.main()
    assert ended.value.code == status
    assert starts == []


def test_an_edit_to_the_checkout_backlog_changes_the_stream_digest(
    board: Board,
) -> None:
    backlog = board.checkout / "docs" / "backlog"
    backlog.mkdir(parents=True)
    item = backlog / "fix-the-login.md"
    item.write_text("# Fix the login\n")
    before = watched.look(board.state, board.home)
    item.write_text("# Fix the login on the phone\n")
    assert watched.look(board.state, board.home) != before


@pytest.mark.parametrize(("declared", "reads"), [(push_body.MOST + 1, 0), (None, 2)])
def test_push_stops_at_the_body_limit(
    board: Board, declared: int | None, reads: int
) -> None:
    own = f"127.0.0.1:{MAIN}".encode()
    headers = [(b"host", own), (b"origin", b"http://" + own)]
    if declared is not None:
        headers.append((b"content-length", str(declared).encode()))
    scope: Scope = {
        "type": "http",
        "method": "POST",
        "headers": headers,
        "server": ("127.0.0.1", MAIN),
        "client": ("127.0.0.1", 50000),
        "app": board.app,
    }
    seen = []
    chunks = iter([(b" " * push_body.MOST, True), (b" ", True), (b" ", False)])

    async def receive() -> Message:
        body, more = next(chunks)
        seen.append(body)
        return {"type": "http.request", "body": body, "more_body": more}

    async def check() -> None:
        with pytest.raises(Refusal) as refused:
            await acts.given(Request(scope, receive), acts.Asked)
        assert refused.value.code == "no-json"

    anyio.run(check)
    assert len(seen) == reads


def test_adding_a_workspace_checks_its_setup_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = workspace_at(tmp_path / "shop").resolve()
    lem = checkout / ".lem"
    checked = []
    is_dir = Path.is_dir

    def counted(path: Path, **given: bool) -> bool:
        if path == lem:
            checked.append(path)
        return is_dir(path, **given)

    monkeypatch.setattr(Path, "is_dir", counted)
    assert editing.added(tmp_path / "home", checkout).changed
    assert checked == [lem]
