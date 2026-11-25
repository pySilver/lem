"""The board service's port, listener and stream boundaries."""

import os
import re
from contextlib import aclosing, contextmanager
from http.client import HTTPConnection
from pathlib import Path
from typing import TYPE_CHECKING, cast
from urllib.parse import urlsplit

import anyio
import httpx
import msgspec
import pytest
from starlette.requests import Request

from fakes.records import MOMENT, record
from lem.board import (
    doorway,
    ensure,
    install,
    listening,
    machine,
    opening,
    serve_file,
    server,
    stream,
    watched,
)
from lem.board.facts import Facts
from lem.kernel import folders
from lem.kernel.errors import Refusal
from lem.settings.machine import DOOR_PORT, PORT
from lem.store import tasks
from unit.board.service import tailscale_stand_in as stand_in

if TYPE_CHECKING:
    from collections.abc import Iterator

    from starlette.types import ASGIApp, Message, Scope

    from unit.board.service.given import Board

OLD = 5101
NEXT = 5102
SLUG = "fix-the-login"


def stored(home: Path, port: int) -> Facts:
    """A stand-in for the facts of an old listener, without a socket or process."""
    return Facts(
        pid=os.getpid(),
        port=port,
        url=f"http://127.0.0.1:{port}/",
        host="studio",
        install=install.install_of(),
        home=str(home),
        started=MOMENT,
    )


@pytest.mark.parametrize("old", [PORT, DOOR_PORT, OLD])
def test_a_scratch_home_skips_a_recorded_port_it_did_not_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    old: int,
) -> None:
    home = tmp_path / "config" / "lem"
    environ = {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(home.parent)}
    recorded_home = home if old in {PORT, DOOR_PORT} else tmp_path / "other-home"
    serve_file.write(home, stored(recorded_home, old))
    (home / machine.MACHINE).write_text(f"[serve]\nport = {NEXT}\n")
    connections: list[int] = []

    def connected(port: int) -> None:
        connections.append(port)

    monkeypatch.setattr(ensure.client, "connected", connected)
    monkeypatch.setattr(
        ensure.start, "started", lambda port, home, _: stored(home, port)
    )
    assert ensure.ensure(environ, tmp_path).started
    assert connections == [NEXT, NEXT]


@pytest.mark.parametrize(
    ("version", "keep", "busy"),
    [
        ("2.0.0", True, False),
        ("3.0.0", True, False),
        ("1.0.0", False, False),
        ("1.0.0", True, True),
    ],
)
def test_a_port_move_respects_the_other_install_and_checks_the_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    version: str,
    *,
    keep: bool,
    busy: bool,
) -> None:
    home = tmp_path / "config" / "lem"
    environ = {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(home.parent)}
    mine = msgspec.structs.replace(install.install_of(), version="2.0.0")
    theirs = msgspec.structs.replace(mine, version=version, package="/other/lem")
    old = msgspec.structs.replace(stored(home, OLD), install=theirs)
    serve_file.write(home, old)
    (home / machine.MACHINE).write_text(f"[serve]\nport = {NEXT}\n")
    effects: list[tuple[str, int]] = []

    @contextmanager
    def opened(port: int) -> Iterator[HTTPConnection | None]:
        yield HTTPConnection("unused") if port == OLD else None

    def looked(
        connection: HTTPConnection | None, port: int, home: Path
    ) -> Facts | None:
        effects.append(("look", port))
        if port == NEXT and busy:
            raise Refusal("port-held", "the port is held", "choose another port")
        return old if connection is not None else None

    def started(port: int, home: Path, environ: object) -> Facts:
        effects.append(("start", port))
        return stored(home, port)

    monkeypatch.setattr(ensure.client, "opened", opened)
    monkeypatch.setattr(ensure.client, "looked", looked)
    monkeypatch.setattr(ensure.install, "install_of", lambda: mine)
    monkeypatch.setattr(
        ensure, "stopped", lambda _, port, facts: effects.append(("stop", port))
    )
    monkeypatch.setattr(ensure.start, "started", started)
    if busy:
        with pytest.raises(Refusal, match="the port is held"):
            ensure.held(home, environ, tmp_path)
        assert effects == [("look", NEXT)]
    else:
        shown = ensure.held(home, environ, tmp_path)
        assert shown.started is not keep
        assert shown.url == (old.url if keep else stored(home, NEXT).url)
        assert effects == [("look", NEXT), ("look", OLD)] + (
            [] if keep else [("stop", OLD), ("start", NEXT)]
        )


def test_stop_uses_the_socket_peer_even_with_forwarded_addresses_enabled(
    board: Board,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FORWARDED_ALLOW_IPS", "*")
    config = server.config_of(board.app, verbose=False)
    config.load()

    async def asked() -> int:
        transport = httpx.ASGITransport(
            app=cast("ASGIApp", config.loaded_app),
            client=("192.0.2.10", 50000),
        )
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://127.0.0.1:4999",
        ) as client:
            return (
                await client.post(
                    "/api/server/stop",
                    headers={
                        "X-Forwarded-For": "127.0.0.1",
                    },
                )
            ).status_code

    assert anyio.run(asked) == 403
    assert board.stops == []


def test_a_door_with_the_main_port_is_refused_before_the_settings_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "config" / "lem"
    folders.home_marked(home)
    settings = home / machine.MACHINE
    before = f"[serve]\nport = {OLD}\ntailscale_port = {OLD}\ntailscale = false\n"
    settings.write_text(before)
    cli = stand_in.made(tmp_path / "ts")
    environ = {
        **stand_in.environ(cli),
        "HOME": str(tmp_path),
        "XDG_CONFIG_HOME": str(home.parent),
        "LEM_SERVE": "off",
    }
    called: list[str] = []
    monkeypatch.setattr(ensure, "ensure", lambda *_: called.append("ensure"))
    with pytest.raises(Refusal) as refused:
        doorway.opened(environ, tmp_path)
    assert refused.value.code == "door-port"
    assert settings.read_text() == before
    assert not called


def test_an_ipv6_board_binds_and_names_its_url(board: Board) -> None:
    with listening.bound("::1", 0) as sock:
        address = sock.getsockname()
        assert address[0] == "::1"
        assert address[1] not in {PORT, DOOR_PORT}
        facts = opening.facts_of(sock, "::1", board.home, None)
    url = urlsplit(facts.url)
    assert (url.hostname, url.port) == ("::1", address[1])


def test_an_artifact_saved_after_the_page_reads_it_owes_a_refresh_at_stream_open(
    board: Board,
) -> None:
    tasks.create(board.state, record(SLUG))
    report = board.state / "tasks" / SLUG / "report.md"
    report.write_text("the old report")
    shown = watched.look(board.state, board.home, SLUG)
    assert report.read_text() == "the old report"
    report.write_text("the new report")

    async def first() -> None:
        with anyio.fail_after(2):
            async with aclosing(
                stream.events(
                    board.state,
                    rendered=shown,
                    missed=False,
                    home=board.home,
                    task=SLUG,
                )
            ) as events:
                event = await anext(events)
        assert event.data == stream.REFRESH
        assert event.id == watched.look(board.state, board.home, SLUG) != shown

    anyio.run(first)


def test_a_file_changed_after_the_kanban_render_owes_a_refresh_at_stream_open(
    board: Board,
) -> None:
    page = board.main().get("/studio/shop/").text
    shown = re.search(r'data-stream-since-value="([^"]+)"', page)
    assert shown is not None
    (board.state / "demo").write_text("examples")

    async def first() -> None:
        with anyio.fail_after(2):
            async with aclosing(
                stream.events(
                    board.state,
                    rendered=shown[1],
                    missed=False,
                    home=board.home,
                )
            ) as events:
                event = await anext(events)
        assert event.data == stream.REFRESH
        assert event.id != shown[1]

    anyio.run(first)


def test_a_quiet_open_stream_sends_its_first_ping_on_time(
    board: Board,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = board.main().get("/studio/shop/").text
    version = re.search(r'data-stream-since-value="([^"]+)"', page)
    assert version is not None
    monkeypatch.setattr(stream, "PING_SECONDS", 1)
    scope: Scope = {
        "type": "http",
        "method": "GET",
        "headers": [],
        "query_string": f"rendered={version[1]}".encode(),
        "path_params": {"host": "studio", "workspace": "shop"},
        "app": board.app,
        "asgi": {"spec_version": "2.4"},
    }

    async def check() -> None:
        started = anyio.current_time()
        frames = []

        async def receive() -> Message:
            await anyio.sleep_forever()
            return {"type": "http.disconnect"}

        async with anyio.create_task_group() as group:

            async def send(message: Message) -> None:
                if message["type"] == "http.response.body":
                    frames.append((anyio.current_time() - started, message["body"]))
                    group.cancel_scope.cancel()

            response = await stream.endpoint(Request(scope))
            with anyio.fail_after(5):
                await response(scope, receive, send)
        [(elapsed, body)] = frames
        assert body.splitlines() == [b"event: ping", b"data: ping", b""]
        assert elapsed >= stream.PING_SECONDS

    anyio.run(check)

    ledger = (
        Path(__file__).resolve().parents[4] / "tests/ledger/fates/board-service.tsv"
    )
    assert (
        "duty:stream-heartbeat\tchanged\tunit.board.service.test_repairs.test_a_quiet_open_stream_sends_its_first_ping_on_time\t"
        in ledger.read_text()
    )
