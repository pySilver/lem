"""The walking skeleton of the board, through Starlette's test client: the kanban of a workspace
from its task records, a task's question card, the server's own addresses, the stream's
refresh after a record changes, and the rules of `lem serve` that read no network."""

import os
import pwd
import re
import threading
from collections.abc import AsyncGenerator
from contextlib import aclosing
from dataclasses import dataclass
from functools import partial
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, cast

import anyio
import msgspec
import pytest
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from fakes.records import MOMENT, record
from lem.addons.peers import routes as peers
from lem.app.asking import form, saved
from lem.board import (
    app,
    ensure,
    heard,
    install,
    machine,
    serve_file,
    shield,
    start,
    stopping,
    stream,
    watched,
    workspaces,
)
from lem.board.client import Reply
from lem.board.facts import HEADER, MARK, Facts, Install
from lem.board.serving import Serving
from lem.kernel import folders, release
from lem.kernel.errors import Refusal
from lem.records.holds import OwnerHold
from lem.store import places, tasks

if TYPE_CHECKING:
    from collections.abc import Callable

    from starlette.applications import Starlette

SECTION = re.compile(
    r'<section class="col [^"]*" id="col-([a-z]+)"(.*?)</section>', re.DOTALL
)


@dataclass
class Board:
    """A board over one workspace: the client, Lem's home folder, the workspace's state
    folder, the kanban's address, and each call of the server's stop."""

    client: TestClient
    home: Path
    state: Path
    address: str
    stops: list[str]
    facts: Facts


def workspace_at(folder: Path) -> Path:
    """A main checkout where Lem is set up: `.git` and `.lem`, and nothing else."""
    (folder / ".git").mkdir(parents=True)
    (folder / ".lem").mkdir()
    return folder


@pytest.fixture
def board(tmp_path: Path) -> Board:
    home = tmp_path / "lem-home"
    checkout = workspace_at(tmp_path / "My Repo")
    space = workspaces.noted(home, checkout)
    assert space is not None
    host = machine.machine_name()
    facts = Facts(
        pid=os.getpid(),
        port=4999,
        url="http://127.0.0.1:4999/",
        host=host,
        install=install.install_of(),
        home=str(home),
        started=MOMENT,
    )
    stops: list[str] = []
    serving = Serving(
        home=home,
        environ=os.environ,
        listen="127.0.0.1",
        stop=lambda: stops.append("stop"),
    )
    made = app.made(facts, serving)
    client = TestClient(
        made, base_url="http://127.0.0.1:4999", client=("127.0.0.1", 50000)
    )
    state = places.state_of(checkout)
    return Board(client, home, state, f"/{host}/my-repo/", stops, facts)


def columns(page: str) -> dict[str, str]:
    """Each column of the kanban by its key, with its markup."""
    return dict(SECTION.findall(page))


def test_the_kanban_shows_each_task_in_the_column_of_its_status_from_the_records(
    board: Board,
) -> None:
    held = OwnerHold(on="criteria", line="approve the criteria", since=MOMENT)
    tasks.create(board.state, record("fix-the-login"))
    tasks.create(board.state, record("add-a-flag", status="building", hold=held))
    tasks.create(board.state, record("tidy-the-docs", status="landing"))
    tasks.create(board.state, record("old-thing", status="landed"))
    page = board.client.get(board.address)
    assert page.status_code == 200
    found = columns(page.text)
    assert list(found) == ["you", "build", "checks", "done"]
    assert 'id="card-add-a-flag"' in found["you"]
    assert "s-building a-you" in found["you"]
    assert 'id="card-fix-the-login"' in found["build"]
    assert 'id="card-tidy-the-docs"' in found["checks"]
    assert 'id="card-old-thing"' in found["done"]
    assert "Nothing waits for you" not in found["you"]


def test_an_empty_workspace_shows_each_column_with_its_line(board: Board) -> None:
    page = board.client.get(board.address).text
    for line in ("Nothing waits for you", "No task builds", "Nothing landed yet"):
        assert line in page


@pytest.mark.parametrize("missing", [True, False])
def test_tasks_and_its_stream_work_without_a_page_provider(
    board: Board, *, missing: bool
) -> None:
    server = cast("Starlette", board.client.app)
    if missing:
        del server.state.page_inputs
    else:
        server.state.page_inputs = None
    del server.state.act_revision
    del server.state.environ
    tasks.create(board.state, record("fix-the-login", status="building"))
    page = board.client.get(board.address)
    assert page.status_code == 200
    assert 'id="card-fix-the-login"' in page.text
    version = re.search(r'data-stream-since-value="([^"]+)"', page.text)
    assert version is not None
    path = f"{board.address}stream"
    assert f'data-stream-url-value="{path}"' in page.text
    tasks.create(board.state, record("add-a-flag"))
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "app": server,
            "headers": [],
            "path_params": {"host": board.facts.host, "workspace": "my-repo"},
            "query_string": f"rendered={version[1]}".encode(),
        }
    )

    async def check() -> None:
        response = await stream.endpoint(request)
        assert isinstance(response, stream.EventSourceResponse)
        events = response.body_iterator
        assert isinstance(events, AsyncGenerator)
        async with aclosing(events):
            with anyio.fail_after(2):
                event = await anext(events)
        assert isinstance(event, stream.ServerSentEvent)
        assert event.data == stream.REFRESH and event.id != version[1]

    anyio.run(check)
    assert board.client.get(f"{board.address}waits").status_code == 503


def test_a_task_whose_words_hold_markup_is_printed_as_text(board: Board) -> None:
    words = '<script>alert("x")</script> & <b>bold</b>'
    tasks.create(board.state, record("fix-the-login", ask=words))
    page = board.client.get(board.address).text
    assert "<script>alert" not in page
    assert "<b>bold</b>" not in page
    assert "&lt;script&gt;alert(&#34;x&#34;)&lt;/script&gt; &amp; &lt;b&gt;bold" in page


def test_the_page_names_its_stream_and_the_version_it_shows(board: Board) -> None:
    tasks.create(board.state, record("fix-the-login"))
    page = board.client.get(board.address).text
    assert f'data-stream-url-value="{board.address}stream"' in page
    assert (
        f'data-stream-since-value="{watched.look(board.state, board.home).version}"'
        in page
    )


def test_the_page_links_the_assets_of_today_and_the_server_sends_them(
    board: Board,
) -> None:
    page = board.client.get(board.address).text
    for asset in ("lem.css", "lem.js", "board.css", "vendor/board-app.js"):
        assert f"/assets/{asset}" in page
        assert board.client.get(f"/assets/{asset}").status_code == 200, asset


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/elsewhere/my-repo/"),
        ("GET", "/{host}/no-such-repo/"),
        ("GET", "/{host}/no-such-repo/stream"),
    ],
)
def test_a_host_or_workspace_the_board_does_not_have_is_404(
    board: Board, method: str, path: str
) -> None:
    host = machine.machine_name()
    assert board.client.request(method, path.format(host=host)).status_code == 404


@pytest.fixture
def question_card(board: Board) -> tuple[str, bytes]:
    slug = "fix-the-login"
    tasks.create(board.state, record(slug, status="shaping"))
    folder = places.task_folder(board.state, slug)
    card = form.metadata({"prompt": "Keep the login?", "options": ["Keep"]}, "p1", "s1")
    html = b"<!doctype html><title>Keep the login?</title>"
    saved.keep(folder, card, html)
    return f"{board.address}tasks/{slug}/cards/p1", html


def test_the_card_redirects_and_serves_its_saved_page(
    board: Board, question_card: tuple[str, bytes]
) -> None:
    address, html = question_card
    for method in ("GET", "HEAD"):
        redirect = board.client.request(
            method, f"{address}?in=waits", follow_redirects=False
        )
        assert redirect.status_code == 302
        assert redirect.headers["location"] == f"{address}/?in=waits"

    page = board.client.get(f"{address}/")
    headers = board.client.head(f"{address}/")
    assert page.status_code == headers.status_code == 200
    assert page.content == html
    assert headers.content == b""
    for response in (page, headers):
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert response.headers["content-length"] == str(len(html))
        assert response.headers["etag"] == f'"{sha256(html).hexdigest()}"'
        assert "frame-ancestors 'self'" in response.headers["content-security-policy"]


def test_the_card_answer_checks_the_origin_digest_and_choice(
    board: Board, question_card: tuple[str, bytes]
) -> None:
    address, html = question_card
    endpoint = f"{address}/answer"
    before = tasks.read(board.state, "fix-the-login")
    digest = sha256(html).hexdigest()
    answer = {
        "status": "answered",
        "digest": digest,
        "answers": {"answer": {"selected": ["Keep"]}},
    }
    refused = board.client.post(endpoint, json=answer)
    assert refused.status_code == 403
    assert "own page" in refused.json()["said"]

    origin = {"Origin": board.facts.url.rstrip("/")}
    stale = board.client.post(
        endpoint, headers=origin, json={**answer, "digest": "stale"}
    )
    assert stale.status_code == 409
    assert "differs from the page the owner read" in stale.json()["said"]

    wrong = {**answer, "answers": {"answer": {"selected": ["Replace"]}}}
    unknown = board.client.post(endpoint, headers=origin, json=wrong)
    assert unknown.status_code == 422
    assert "choice the card did not show" in unknown.json()["said"]
    assert tasks.read(board.state, "fix-the-login") == before


@pytest.mark.parametrize("path", ["tasks/fix-the-login/merge", "tasks"])
def test_a_board_act_requires_the_boards_own_origin(board: Board, path: str) -> None:
    answer = board.client.post(f"{board.address}{path}")
    assert answer.status_code == 403
    assert "board's own page" in answer.text


def test_api_server_says_who_serves_with_its_own_header(board: Board) -> None:
    answer = board.client.get("/api/server")
    assert answer.headers["Lem-Server"] == "lem"
    facts = msgspec.json.decode(answer.content, type=Facts)
    assert (facts.pid, facts.home) == (os.getpid(), str(board.home))


def test_the_stop_is_taken_from_a_program_here_and_refused_from_a_page_or_elsewhere(
    board: Board,
) -> None:
    page = board.client.post("/api/server/stop", headers={"Origin": "http://x"})
    assert page.status_code == 403
    fetch = board.client.post("/api/server/stop", headers={"Sec-Fetch-Site": "none"})
    assert fetch.status_code == 403
    far = TestClient(board.client.app, base_url="http://127.0.0.1")
    assert far.post("/api/server/stop").status_code == 403
    assert board.stops == []
    assert board.client.post("/api/server/stop").status_code == 200
    assert board.stops == ["stop"]


@pytest.mark.parametrize(
    "host", ["evil.example", "127.0.0.1:1", "localhost:80", "evil.example:4999"]
)
def test_a_request_that_names_another_host_or_port_reads_nothing_and_says_where_to_go(
    board: Board, host: str
) -> None:
    answer = board.client.get(board.address, headers={"Host": host})
    assert answer.status_code == 403
    assert answer.text == (
        "This address is not the board's own on this Mac: open it as "
        "http://127.0.0.1:4999/."
    )


@pytest.mark.parametrize("host", ["127.0.0.1", "127.0.0.1:4999", "LOCALHOST:4999"])
def test_a_request_that_names_the_listener_by_its_own_name_is_read(
    board: Board, host: str
) -> None:
    assert board.client.get(board.address, headers={"Host": host}).status_code == 200


def test_a_request_with_two_hosts_or_none_reads_nothing() -> None:
    assert shield.host_refusal(["127.0.0.1", "127.0.0.1"], 4999, "127.0.0.1")
    assert shield.host_refusal([], 4999, "127.0.0.1")
    assert shield.host_refusal(["[::1]:4999"], 4999, "127.0.0.1") is None
    assert shield.host_refusal(["10.0.0.2:4999"], 4999, "10.0.0.2") is None


async def first_event(
    state: Path, home: Path, *, rendered: str | None, missed: bool
) -> object:
    """The stream's first message, while a record is written a moment after it opens."""
    events = stream.refreshed(
        partial(watched.look, state, home), rendered=rendered, missed=missed
    )

    async def write() -> None:
        await anyio.sleep(0.3)
        tasks.create(state, record("add-a-flag"))

    try:
        async with anyio.create_task_group() as group:
            group.start_soon(write)
            with anyio.fail_after(20):
                return await anext(events)
    finally:
        await events.aclose()


def test_the_stream_sends_a_refresh_after_a_record_changes(board: Board) -> None:
    tasks.create(board.state, record("fix-the-login"))
    shown = watched.look(board.state, board.home).version
    event = anyio.run(
        lambda: first_event(board.state, board.home, rendered=shown, missed=False)
    )
    assert isinstance(event, stream.ServerSentEvent)
    assert event.data == stream.REFRESH
    assert event.id == watched.look(board.state, board.home).version
    assert event.id != shown


def test_an_open_that_may_have_missed_a_change_gets_a_refresh_at_once(
    board: Board,
) -> None:
    shown = watched.look(board.state, board.home).version
    event = anyio.run(
        lambda: first_event(board.state, board.home, rendered=None, missed=True)
    )
    assert isinstance(event, stream.ServerSentEvent)
    assert event.id == shown


@pytest.mark.parametrize(
    ("rendered", "missed", "owed"),
    [
        (None, False, False),
        ("v1", False, False),
        ("v0", False, True),
        ("v1", True, True),
    ],
)
def test_an_open_owes_a_refresh_when_it_names_an_old_version_or_missed_one(
    rendered: str | None, *, missed: bool, owed: bool
) -> None:
    assert stream.owes(rendered=rendered, missed=missed, told="v1") is owed


def test_the_version_moves_at_each_write_of_a_record(tmp_path: Path) -> None:
    before = watched.look(tmp_path, tmp_path)
    made = tasks.create(tmp_path, record())
    first = watched.look(tmp_path, tmp_path)
    tasks.update(tmp_path, made.task.slug, lambda kept: kept, expect=made.revision)
    assert len({before, first, watched.look(tmp_path, tmp_path)}) == 3


MINE = Install(version="1.2.0", package="/opt/lem", stamp=5)


@pytest.mark.parametrize(
    ("theirs", "differ", "replaced"),
    [
        (MINE, False, False),
        (MINE, True, True),
        (msgspec.structs.replace(MINE, stamp=4), False, True),
        (
            msgspec.structs.replace(MINE, package="/other", version="1.2.0"),
            False,
            False,
        ),
        (
            msgspec.structs.replace(MINE, package="/other", version="1.3.0"),
            False,
            False,
        ),
        (msgspec.structs.replace(MINE, package="/other", version="1.1.9"), False, True),
        (msgspec.structs.replace(MINE, package="/other", version="1.2.0"), True, False),
    ],
    ids=[
        "same install",
        "same install, other settings",
        "same folder, older code",
        "other install, same release",
        "other install, higher release",
        "other install, lower release",
        "other install, other settings",
    ],
)
def test_the_replace_rule(theirs: Install, *, differ: bool, replaced: bool) -> None:
    assert install.replaces(MINE, theirs, settings_differ=differ) is replaced


def test_this_install_is_its_package_its_release_and_its_modules_newest_time() -> None:
    mine = install.install_of()
    assert mine.version == release.running()
    assert mine.package == str(Path(install.__file__).resolve().parents[1])
    assert mine.commit is None
    assert mine.stamp is not None
    assert mine.stamp > 0


@pytest.mark.parametrize("port", [machine.PORT, machine.DOOR_PORT])
def test_a_throwaway_home_never_takes_the_owners_ports(
    tmp_path: Path, port: int
) -> None:
    with pytest.raises(Refusal) as refused:
        machine.guarded(port, {"HOME": str(tmp_path)})
    assert refused.value.code == "owner-port"
    with pytest.raises(Refusal):
        machine.guarded(port, {"HOME": str(tmp_path), "XDG_CONFIG_HOME": "/tmp/x"})
    real = pwd.getpwuid(os.getuid()).pw_dir
    assert machine.guarded(port, {"HOME": real}) == port
    assert machine.guarded(port + 1000, {"HOME": str(tmp_path)}) == port + 1000


def test_the_port_is_the_given_one_else_the_machines_setting(tmp_path: Path) -> None:
    environ = {"HOME": str(tmp_path)}
    with pytest.raises(Refusal):
        machine.port_of(tmp_path, environ)
    (tmp_path / machine.MACHINE).write_text("[serve]\nport = 5123\n")
    assert machine.port_of(tmp_path, environ) == 5123
    assert machine.port_of(tmp_path, environ, 5200) == 5200
    (tmp_path / machine.MACHINE).write_text("[serve]\nport = 0\n")
    with pytest.raises(Refusal) as refused:
        machine.port_of(tmp_path, environ)
    # the machine's file is read and checked by the settings (`settings.load.machine_of`)
    assert refused.value.code == "settings"
    assert "serve.port" in refused.value.fix


def test_each_workspace_has_a_name_of_its_own_and_none_of_the_servers_words() -> None:
    paths = ("/a/My Repo", "/b/my-repo", "/c/api", "/d/mac")
    assert workspaces.named(paths, "mac") == (
        ("my-repo", "/a/My Repo"),
        ("my-repo-2", "/b/my-repo"),
        ("api-2", "/c/api"),
        ("mac-2", "/d/mac"),
    )


def test_a_workspace_is_put_on_the_list_once_and_a_folder_outside_one_is_not(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    checkout = workspace_at(tmp_path / "repo")
    assert workspaces.noted(home, tmp_path / "elsewhere") is None
    workspaces.noted(home, checkout)
    workspaces.noted(home, checkout)
    assert workspaces.listed(home) == (str(checkout.resolve()),)


def test_the_serve_file_is_removed_only_by_the_server_it_names(tmp_path: Path) -> None:
    facts = Facts(
        pid=41,
        port=1,
        url="u",
        host="h",
        install=MINE,
        home=str(tmp_path),
        started=MOMENT,
    )
    serve_file.write(tmp_path, facts)
    serve_file.remove(tmp_path, 42)
    assert (tmp_path / serve_file.SERVE).is_file()
    serve_file.remove(tmp_path, 41)
    assert not (tmp_path / serve_file.SERVE).exists()


def test_a_head_of_the_stream_answers_its_headers_and_ends(board: Board) -> None:
    answers: list[object] = []
    asked = threading.Thread(
        target=lambda: answers.append(board.client.head(f"{board.address}stream")),
        daemon=True,
    )
    asked.start()
    asked.join(10)
    assert len(answers) == 1, "HEAD of the stream did not end"
    answer = answers[0]
    assert getattr(answer, "status_code", None) == 200
    assert getattr(answer, "headers", {})["content-type"].startswith(
        "text/event-stream"
    )


def test_a_write_between_the_pages_two_reads_leaves_the_page_owing_a_refresh(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    tasks.create(board.state, record("fix-the-login"))
    reads: list[str] = []

    def after_first[**Args](
        name: str, real: Callable[Args, object]
    ) -> Callable[Args, object]:
        def read(*args: Args.args, **kwargs: Args.kwargs) -> object:
            found = real(*args, **kwargs)
            reads.append(name)
            if len(reads) == 1:
                tasks.create(board.state, record("add-a-flag"))
            return found

        return read

    monkeypatch.setattr(watched, "look", after_first("version", watched.look))
    monkeypatch.setattr(tasks, "every", after_first("records", tasks.every))
    page = board.client.get(board.address).text
    monkeypatch.undo()
    shown = re.search(r'data-stream-since-value="([0-9a-f]+)"', page)
    assert shown is not None
    on_page = 'id="card-add-a-flag"' in page
    owed = stream.owes(
        rendered=shown[1],
        missed=False,
        told=watched.look(board.state, board.home).version,
    )
    assert on_page or owed
    assert reads == ["version", "records"]


def test_the_peers_table_is_matched_before_the_addresses_of_this_machine(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def peer(request: object) -> PlainTextResponse:
        return PlainTextResponse("the peer's page")

    monkeypatch.setattr(peers, "ROUTES", (Route("/other-mac/{rest:path}", peer),))
    serving = Serving(
        home=board.home, environ=os.environ, listen="127.0.0.1", stop=lambda: None
    )
    made = app.made(board.facts, serving)
    client = TestClient(made, base_url="http://127.0.0.1")
    assert client.get("/other-mac/repo/").text == "the peer's page"
    assert client.get(board.address).status_code == 200


def test_the_start_log_starts_again_empty_past_its_cap(tmp_path: Path) -> None:
    log = tmp_path / start.LOG
    log.write_bytes(b"x" * (start.LOG_CAP + 1))
    start.trimmed(log)
    assert log.read_bytes() == b""
    log.write_bytes(b"kept\n")
    start.trimmed(log)
    assert log.read_bytes() == b"kept\n"
    start.trimmed(tmp_path / "none.log")


def test_ensure_reads_the_port_again_under_the_serve_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "config"
    home = config / "lem"
    folders.home_marked(home)
    settings = home / machine.MACHINE
    settings.write_text("[serve]\nport = 5101\n")
    environ = {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(config)}
    real_ask = ensure.client.ask

    def ask_then_change(port: int, home: Path) -> object:
        found = real_ask(port, home)
        settings.write_text("[serve]\nport = 5102\n")
        return found

    started: list[int] = []

    def recorded(port: int, home: Path, environ: object) -> Facts:
        started.append(port)
        return facts_of(port, home)

    monkeypatch.setattr(ensure.client, "ask", ask_then_change)
    monkeypatch.setattr(ensure.start, "started", recorded)
    shown = ensure.ensure(environ, tmp_path)
    assert started == [5102]
    assert shown.started is True


def facts_of(port: int, home: Path) -> Facts:
    return Facts(
        pid=os.getpid(),
        port=port,
        url=f"http://127.0.0.1:{port}/",
        host="mac",
        install=install.install_of(),
        home=str(home),
        started=MOMENT,
    )


class StandIn(ThreadingHTTPServer):
    """A board server of this build, in this test's process: what it was asked, by which
    client port, and whether it closes each connection after its answer."""

    def __init__(self, home: Path, *, closes: bool) -> None:
        super().__init__(("127.0.0.1", 0), Answering)
        self.facts = facts_of(self.server_address[1], home)
        self.closes = closes
        self.seen: list[tuple[str, int]] = []

    def ended(self) -> None:
        """Stop serving and close the port, as a server does at its stop."""
        self.shutdown()
        self.server_close()


class Answering(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    @property
    def stand_in(self) -> StandIn:
        return cast("StandIn", self.server)

    def answer(self, body: bytes) -> None:
        self.stand_in.seen.append((self.command, self.client_address[1]))
        self.send_response(200)
        self.send_header(HEADER, MARK)
        self.send_header("Content-Length", str(len(body)))
        if self.stand_in.closes:
            self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        self.answer(msgspec.json.encode(self.stand_in.facts))

    def do_POST(self) -> None:
        self.answer(b"the board server stops")
        threading.Thread(target=self.stand_in.ended, daemon=True).start()


def stand_in(tmp_path: Path, *, closes: bool) -> tuple[StandIn, dict[str, str]]:
    config = tmp_path / "config"
    home = config / "lem"
    folders.home_marked(home)
    server = StandIn(home, closes=closes)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    (home / machine.MACHINE).write_text(f"[serve]\nport = {port}\n")
    return server, {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(config)}


def test_the_stop_goes_on_the_connection_that_asked_who_serves(tmp_path: Path) -> None:
    server, environ = stand_in(tmp_path, closes=False)
    try:
        said = stopping.stop(environ)
    finally:
        server.shutdown()
        server.server_close()
    assert said.stopped is True
    asked = [port for method, port in server.seen if method == "GET"]
    posted = [port for method, port in server.seen if method == "POST"]
    assert len(posted) == 1
    assert posted[0] == asked[-1]


def test_no_stop_is_sent_when_the_server_closed_the_connection_it_answered_on(
    tmp_path: Path,
) -> None:
    server, environ = stand_in(tmp_path, closes=True)
    try:
        with pytest.raises(Refusal) as refused:
            stopping.stop(environ)
    finally:
        server.shutdown()
        server.server_close()
    assert refused.value.code == "stop-refused"
    assert [method for method, _ in server.seen] == ["GET", "GET"]


def reply(
    body: object, *, marker: str = MARK, server: str = "", status: int = 200
) -> Reply:
    return Reply(
        status=status, marker=marker, server=server, body=msgspec.json.encode(body)
    )


def test_an_answer_is_this_builds_server_only_with_its_mark_its_port_and_its_home(
    tmp_path: Path,
) -> None:
    facts = facts_of(5101, tmp_path)
    assert heard.judged(reply(facts), port=5101, home=tmp_path) == facts
    for wrong, port in (
        (reply(facts, marker="lemx"), 5101),
        (reply(facts, marker=""), 5101),
        (reply(facts, status=202), 5101),
        (reply(facts), 5102),
    ):
        with pytest.raises(Refusal) as refused:
            heard.judged(wrong, port=port, home=tmp_path)
        assert refused.value.code == "port-held"
    with pytest.raises(Refusal) as refused:
        heard.judged(reply(facts), port=5101, home=tmp_path / "other")
    assert refused.value.code == "other-home"


def test_an_answer_of_the_release_before_is_another_install_of_its_home(
    tmp_path: Path,
) -> None:
    before = {
        "pid": 77,
        "version": "version 0.3.1",
        "install": {"version": "0.3.1", "commit": None, "package": "/old", "stamp": 5},
        "config": str(tmp_path),
        "url": "http://127.0.0.1:4536/",
        "port": 4536,
    }
    said = reply(before, marker="", server="lem-serve Python/3.14.0")
    other = heard.judged(said, port=4536, home=tmp_path)
    assert isinstance(other, heard.Other)
    assert "release 0.3.1 from /old (pid 77)" in heard.which(other)
    with pytest.raises(Refusal) as refused:
        heard.judged(said, port=4536, home=tmp_path / "other")
    assert refused.value.code == "other-home"
