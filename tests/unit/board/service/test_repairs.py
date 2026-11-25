"""The board service's port, listener and stream boundaries."""

import os
import re
import subprocess
from contextlib import aclosing, contextmanager
from functools import partial
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
    stopping,
    stream,
    watched,
)
from lem.board.facts import Facts
from lem.kernel import folders
from lem.kernel.errors import Refusal
from lem.settings.machine import DOOR_PORT, PORT
from lem.settings.places import Scope as SettingsScope
from lem.settings.write import Asked, set_setting
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

    def connected(port: int, _: str) -> None:
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
    def opened(port: int, *_: object) -> Iterator[HTTPConnection | None]:
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


@pytest.mark.parametrize(
    ("key", "word"),
    [
        ("serve.port", str(NEXT)),
        ("serve.tailscale_port", str(OLD)),
    ],
)
def test_a_settings_edit_refuses_equal_active_ports_before_it_writes(
    tmp_path: Path, key: str, word: str
) -> None:
    home = tmp_path / "config" / "lem"
    folders.home_marked(home)
    settings = home / machine.MACHINE
    before = f"[serve]\nport = {OLD}\ntailscale_port = {NEXT}\ntailscale = true\n"
    settings.write_text(before)
    environ = {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(home.parent)}
    with pytest.raises(Refusal) as refused:
        set_setting(
            Asked(
                key=key,
                word=word,
                scope=SettingsScope.machine,
                folder=tmp_path,
                environ=environ,
            )
        )
    assert refused.value.code == "door-port"
    assert settings.read_text() == before


@pytest.mark.parametrize("destination", [OLD, NEXT])
def test_equal_ports_are_refused_under_the_serve_lock_before_any_stop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, destination: int
) -> None:
    home = tmp_path / "config" / "lem"
    old = stored(home, OLD)
    serve_file.write(home, old)
    settings = home / machine.MACHINE
    settings.write_text(f"[serve]\nport = {destination}\n")
    environ = {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(home.parent)}
    effects: list[str] = []

    @contextmanager
    def changed_under_lock(_: Path) -> Iterator[None]:
        settings.write_text(
            f"[serve]\nport = {destination}\ntailscale_port = {destination}\ntailscale = true\n"
        )
        yield

    @contextmanager
    def opened(port: int, *_: object) -> Iterator[HTTPConnection | None]:
        yield HTTPConnection("unused") if port == OLD else None

    monkeypatch.setattr(ensure.lock, "serve_lock", changed_under_lock)
    monkeypatch.setattr(ensure.client, "opened", opened)
    monkeypatch.setattr(
        ensure.client, "looked", lambda connection, *_: old if connection else None
    )
    monkeypatch.setattr(ensure, "stopped", lambda *_: effects.append("stop"))

    def started(port: int, home: Path, environ: object) -> Facts:
        effects.append("start")
        opening.door_of(home, {}, port)
        return stored(home, port)

    monkeypatch.setattr(ensure.start, "started", started)
    with pytest.raises(Refusal) as refused:
        ensure.ensure(environ, tmp_path)
    assert refused.value.code == "door-port"
    assert effects == []


@pytest.mark.parametrize("busy", [False, True])
def test_a_move_ignores_an_unrelated_reply_only_at_the_old_address(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, busy: bool
) -> None:
    home = tmp_path / "config" / "lem"
    serve_file.write(home, stored(home, OLD))
    (home / machine.MACHINE).write_text(f"[serve]\nport = {NEXT}\n")
    environ = {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(home.parent)}
    effects: list[int] = []

    def connected(port: int, *_: object) -> HTTPConnection | None:
        return HTTPConnection("unused", port) if port == OLD or busy else None

    def started(port: int, home: Path, _: object) -> Facts:
        effects.append(port)
        return stored(home, port)

    monkeypatch.setattr(ensure.client, "connected", connected)
    monkeypatch.setattr(
        ensure.client,
        "asked",
        lambda *_: ensure.client.Reply(status=404, marker="", server="", body=b""),
    )
    monkeypatch.setattr(ensure.start, "started", started)
    if busy:
        with pytest.raises(Refusal) as refused:
            ensure.held(home, environ, tmp_path)
        assert refused.value.code == "port-held"
        assert effects == []
    else:
        assert ensure.held(home, environ, tmp_path).started
        assert effects == [NEXT]


def test_an_ipv6_board_binds_and_names_its_url(board: Board) -> None:
    with listening.bound("::1", 0) as sock:
        address = sock.getsockname()
        assert address[0] == "::1"
        assert address[1] not in {PORT, DOOR_PORT}
        facts = opening.facts_of(sock, "::1", board.home, None)
    url = urlsplit(facts.url)
    assert (url.hostname, url.port) == ("::1", address[1])


@pytest.mark.parametrize("action", ["ensure", "stop", "move"])
def test_the_management_calls_find_the_recorded_ipv6_listener(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, action: str
) -> None:
    home = tmp_path / "config" / "lem"
    ipv6 = msgspec.structs.replace(stored(home, OLD), url=f"http://[::1]:{OLD}/")
    serve_file.write(home, ipv6)
    port = NEXT if action == "move" else OLD
    (home / machine.MACHINE).write_text(f"[serve]\nport = {port}\n")
    environ = {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(home.parent)}
    asked: list[tuple[str, int]] = []
    stopped: list[tuple[str, int]] = []
    started: list[int] = []

    def connect(connection: HTTPConnection) -> None:
        address = (connection.host, connection.port)
        asked.append(address)
        if address != ("::1", OLD):
            raise ConnectionRefusedError

    def start(port: int, home: Path, _: object) -> Facts:
        started.append(port)
        return stored(home, port)

    def stop(connection: HTTPConnection, port: int, _: Facts) -> None:
        stopped.append((connection.host, port))

    monkeypatch.setattr(HTTPConnection, "connect", connect)
    monkeypatch.setattr(
        ensure.client,
        "asked",
        lambda *_: ensure.client.Reply(
            status=200, marker="lem", server="", body=msgspec.json.encode(ipv6)
        ),
    )
    monkeypatch.setattr(ensure.start, "started", start)
    monkeypatch.setattr(ensure, "stopped", stop)
    monkeypatch.setattr(stopping.halt, "stopped", stop)
    if action == "stop":
        assert stopping.stop(environ).stopped
    else:
        shown = ensure.ensure(environ, tmp_path)
        assert shown.url == (stored(home, NEXT).url if action == "move" else ipv6.url)
    assert ("::1", OLD) in asked
    assert stopped == ([] if action == "ensure" else [("::1", OLD)])
    assert started == ([NEXT] if action == "move" else [])


def test_an_artifact_saved_after_the_page_reads_it_owes_a_refresh_at_stream_open(
    board: Board,
) -> None:
    tasks.create(board.state, record(SLUG))
    report = board.state / "tasks" / SLUG / "report.md"
    report.write_text("the old report")
    shown = watched.look(board.state, board.home, SLUG).rendered
    assert report.read_text() == "the old report"
    report.write_text("the new report")

    async def first() -> None:
        with anyio.fail_after(2):
            async with aclosing(
                stream.refreshed(
                    partial(watched.look, board.state, board.home, SLUG),
                    rendered=shown,
                    missed=False,
                )
            ) as events:
                event = await anext(events)
        assert event.data == stream.REFRESH
        assert watched.look(board.state, board.home, SLUG).rendered != shown
        assert event.id == watched.look(board.state, board.home).version

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
                stream.refreshed(
                    partial(watched.look, board.state, board.home),
                    rendered=shown[1],
                    missed=False,
                )
            ) as events:
                event = await anext(events)
        assert event.data == stream.REFRESH
        assert event.id != shown[1]

    anyio.run(first)


@pytest.mark.parametrize("changed", [False, True])
def test_a_task_visit_compares_its_rendered_token_at_stream_open(
    board: Board, *, changed: bool
) -> None:
    tasks.create(board.state, record(SLUG))
    report = board.state / "tasks" / SLUG / "report.md"
    report.write_text("the first report")
    page = board.main().get("/studio/shop/").text
    workspace = re.search(r'data-stream-since-value="([^"]+)"', page)
    assert workspace is not None
    assert f'data-stream-task="" data-stream-rendered="{workspace[1]}"' in page
    rendered = watched.look(board.state, board.home, SLUG).rendered
    if changed:
        report.write_text("the report changed after the render")
    script = Path(__file__).with_name("stream_visit.mjs")
    controller = script.parents[4] / "tools/board-kit/controllers/stream.js"
    query = httpx.QueryParams(
        subprocess.check_output(
            ["node", str(script), str(controller), SLUG, workspace[1], rendered],
            text=True,
        ).strip()
    )
    assert query["task"] == SLUG
    assert (
        stream.owes(
            rendered=query.get("rendered"),
            missed="since" in query,
            told=watched.look(board.state, board.home, SLUG).rendered,
        )
        is changed
    )
    assert query["rendered"] == rendered


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


def test_a_merge_note_changes_its_workspace_page_and_stream_version(
    board: Board,
) -> None:
    from lem.board.acts.notes import NOTES, Note

    tasks.create(board.state, record(SLUG))
    client = board.main()
    key = (str(board.checkout), SLUG)
    other = board.checkout.parent / "other" / ".lem" / "state"
    revision = board.app.state.act_revision
    quiet = revision(other)
    before = revision(board.state)
    token, first = NOTES.started(
        key, Note(task=SLUG, act="merge", state="running", said="Merge pending")
    )
    try:
        assert first
        running = revision(board.state)
        assert running != before
        address = f"/studio/shop/tasks/{SLUG}?note={token}"
        page = client.get(address)
        assert page.status_code == 200 and "Merge pending" in page.text
        NOTES.change(token, "refused", "The base moved")
        refused = revision(board.state)
        assert refused != running
        frame = client.get(address, headers={"Turbo-Frame": "task"})
        assert frame.status_code == 200 and "The base moved" in frame.text
        assert revision(other) == quiet
    finally:
        NOTES.ended(key)
    assert revision(board.state) == before


def test_an_unknown_task_tab_keeps_the_real_tasks_navigation(board: Board) -> None:
    tasks.create(board.state, record(SLUG))
    url = f"/studio/shop/tasks/{SLUG}"
    page = board.main().get(f"{url}/unknown")
    assert page.status_code == 404
    assert "A task has no tab" in page.text and f"{url}/criteria" in page.text
