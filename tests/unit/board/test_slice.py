"""The walking skeleton of the board, through Starlette's test client: the kanban of a workspace
from its task records, an address not built yet, the server's own addresses, the stream's
refresh after a record changes, and the rules of `lem serve` that read no network."""

import os
import pwd
import re
from dataclasses import dataclass
from pathlib import Path

import anyio
import msgspec
import pytest
from starlette.testclient import TestClient

from fakes.records import MOMENT, record
from lem.board import app, install, machine, serve_file, stream, workspaces
from lem.board.duties import runner
from lem.board.facts import Facts, Install
from lem.kernel import release
from lem.kernel.errors import Refusal
from lem.records.holds import OwnerHold
from lem.store import places, tasks

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
    made = app.made(
        facts, home=home, listen="127.0.0.1", stop=lambda: stops.append("stop")
    )
    client = TestClient(made, base_url="http://127.0.0.1", client=("127.0.0.1", 50000))
    state = places.state_of(checkout)
    return Board(client, home, state, f"/{host}/my-repo/", stops)


def columns(page: str) -> dict[str, str]:
    """Each column of the kanban by its key, with its markup."""
    return dict(SECTION.findall(page))


def test_the_kanban_shows_each_task_in_the_column_of_its_status_from_the_records(
    board: Board,
) -> None:
    held = OwnerHold(on="criteria", line="approve the criteria", since=MOMENT)
    tasks.create(board.state, record("fix-the-login"))
    tasks.create(board.state, record("add-a-flag", status="building", hold=held))
    tasks.create(board.state, record("tidy-the-docs", status="open"))
    tasks.create(board.state, record("old-thing", status="landed"))
    page = board.client.get(board.address)
    assert page.status_code == 200
    found = columns(page.text)
    assert list(found) == ["you", "build", "checks", "done"]
    assert 'id="card-add-a-flag"' in found["you"]
    assert "building · owner" in found["you"]
    assert 'id="card-fix-the-login"' in found["build"]
    assert 'id="card-tidy-the-docs"' in found["checks"]
    assert 'id="card-old-thing"' in found["done"]
    assert "Nothing waits for you" not in found["you"]


def test_an_empty_workspace_shows_each_column_with_its_line(board: Board) -> None:
    page = board.client.get(board.address).text
    for line in ("Nothing waits for you", "No task builds", "Nothing landed yet"):
        assert line in page


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
    assert f'data-stream-since-value="{stream.version(board.state)}"' in page


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


@pytest.mark.parametrize(
    ("method", "path", "step"),
    [
        ("GET", "/", "board-pages"),
        ("GET", "/h/w/waits", "board-pages"),
        ("GET", "/h/w/tasks/fix-the-login", "board-pages"),
        ("GET", "/h/w/tasks/fix-the-login/merge", "board-pages"),
        ("POST", "/h/w/tasks/fix-the-login/merge", "board-acts"),
        ("POST", "/h/w/tasks", "board-acts"),
        ("GET", "/h/w/tasks/fix-the-login/cards/p1/", "ask"),
        ("POST", "/h/w/tasks/fix-the-login/cards/p1/answer", "ask"),
        ("GET", "/push/key", "board-service"),
        ("POST", "/push/subscribe", "board-service"),
        ("GET", "/api/workspaces", "board-service"),
    ],
)
def test_an_address_not_built_answers_501_with_the_step_that_builds_it(
    board: Board, method: str, path: str, step: str
) -> None:
    answer = board.client.request(method, path)
    assert answer.status_code == 501
    said = answer.json()
    assert said["step"] == step
    assert f"the step `{step}` builds it" in said["why"]


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


def test_a_request_that_names_another_host_reads_nothing(board: Board) -> None:
    answer = board.client.get(board.address, headers={"Host": "evil.example"})
    assert answer.status_code == 400


async def first_event(state: Path, *, rendered: str | None, missed: bool) -> object:
    """The stream's first message, while a record is written a moment after it opens."""
    events = stream.events(state, rendered=rendered, missed=missed)

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
    shown = stream.version(board.state)
    event = anyio.run(lambda: first_event(board.state, rendered=shown, missed=False))
    assert isinstance(event, stream.ServerSentEvent)
    assert event.data == stream.REFRESH
    assert event.id == stream.version(board.state)
    assert event.id != shown


def test_an_open_that_may_have_missed_a_change_gets_a_refresh_at_once(
    board: Board,
) -> None:
    shown = stream.version(board.state)
    event = anyio.run(lambda: first_event(board.state, rendered=None, missed=True))
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
    before = stream.version(tmp_path)
    made = tasks.create(tmp_path, record())
    first = stream.version(tmp_path)
    tasks.update(tmp_path, made.task.slug, lambda kept: kept, expect=made.revision)
    assert len({before, first, stream.version(tmp_path)}) == 3


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
    assert refused.value.code == "machine-settings"


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


def test_each_duty_path_is_a_module_whose_tick_runs_for_a_workspace(
    board: Board,
) -> None:
    runner.tick(board.home)
    assert len(runner.DUTIES) == 7
