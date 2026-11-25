"""The server's own addresses, through the test client: who it is, its stop, the workspaces as
data, the board as an app, a task's raw page and pictures, and the addresses that go to the page
they mean. Each GET answers HEAD with its headers alone."""

from typing import TYPE_CHECKING

import pytest

from fakes.records import MOMENT, record
from lem.board.facts import HEADER, MARK
from lem.records.holds import OwnerHold
from lem.store import tasks

if TYPE_CHECKING:
    from unit.board.service.given import Board

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
OWN_PAGE = {"Origin": "http://127.0.0.1:4999"}


def test_api_server_names_the_server_of_this_home_folder_with_its_own_header(
    board: Board,
) -> None:
    answer = board.main().get("/api/server")
    assert answer.headers[HEADER] == MARK
    told = answer.json()
    assert (told["home"], told["host"], told["aliases"]) == (
        str(board.home),
        "studio",
        ["old-name"],
    )
    assert told["push"] == {}
    head = board.main().head("/api/server")
    assert (head.status_code, head.content) == (200, b"")


def test_the_stop_is_taken_from_a_program_here_and_refused_from_a_page_or_elsewhere(
    board: Board,
) -> None:
    assert board.main().post("/api/server/stop", headers=OWN_PAGE).status_code == 403
    assert board.main(("10.0.0.9", 50000)).post("/api/server/stop").status_code == 403
    assert board.stops == []
    assert board.main().post("/api/server/stop").status_code == 200
    assert board.stops == ["stop"]


def test_api_workspaces_counts_the_tasks_that_wait_and_build(board: Board) -> None:
    tasks.create(board.state, record("fix-the-login", status="building"))
    tasks.create(board.state, record("add-a-flag", status="landing"))
    [row] = board.main().get("/api/workspaces").json()
    assert row["name"] == "shop"
    assert row["url"] == "/studio/shop/"
    assert row["path"] == str(board.checkout)
    assert (row["building"], row["checks"], row["running"]) == (1, 1, 2)
    assert isinstance(row["waits"], int)
    assert board.main().head("/api/workspaces").status_code == 200


def test_the_board_as_an_app_and_its_worker_at_the_root(board: Board) -> None:
    manifest = board.main().get("/manifest.webmanifest")
    assert manifest.headers["content-type"] == "application/manifest+json"
    assert manifest.json()["start_url"] == "/"
    icons = [icon["src"] for icon in manifest.json()["icons"]]
    for icon in icons:
        assert board.main().get(icon).status_code == 200
    worker = board.main().get("/sw.js")
    assert worker.headers["service-worker-allowed"] == "/"
    assert "/api/push/latest" in worker.text
    assert board.main().head("/sw.js").status_code == 200
    assert board.main().head("/manifest.webmanifest").status_code == 200


def test_a_tasks_html_page_comes_only_from_the_raw_route_under_a_sandbox(
    board: Board,
) -> None:
    tasks.create(board.state, record("fix-the-login"))
    folder = board.state / "tasks" / "fix-the-login"
    (folder / "talk.html").write_text("<p>the talk</p>")
    (folder / "notes.md").write_text("# notes")
    (folder / ".lock").write_text("")
    base = "/studio/shop/tasks/fix-the-login/raw/"
    page = board.main().get(f"{base}talk.html")
    assert page.status_code == 200
    assert page.headers["content-security-policy"].startswith("sandbox")
    for path in (
        "notes.md",
        ".lock",
        "task.json",
        "../../../shop/.git",
        "nothing.html",
    ):
        assert board.main().get(f"{base}{path}").status_code == 404, path
    assert board.main().head(f"{base}talk.html").status_code == 200
    unknown = board.main().get("/studio/shop/tasks/no-such-task/raw/talk.html")
    assert unknown.status_code == 404


def test_a_tasks_picture_comes_from_its_media_route_and_nothing_else_does(
    board: Board,
) -> None:
    tasks.create(board.state, record("fix-the-login"))
    media = board.state / "tasks" / "fix-the-login" / "media"
    media.mkdir()
    (media / "shot.png").write_bytes(PNG)
    (media / "shot.svg").write_text("<svg onload='x()'/>")
    (media / "fake.png").write_text("not a picture")
    (board.state / "tasks" / "fix-the-login" / "outside.png").write_bytes(PNG)
    base = "/studio/shop/tasks/fix-the-login/media/"
    shot = board.main().get(f"{base}shot.png")
    assert (shot.status_code, shot.headers["content-type"]) == (200, "image/png")
    assert "sandbox" in shot.headers["content-security-policy"]
    for path in ("shot.svg", "fake.png", "../outside.png", ".hidden.png"):
        assert board.main().get(f"{base}{path}").status_code == 404, path
    assert board.main().head(f"{base}shot.png").status_code == 200


@pytest.mark.parametrize(
    ("asked", "goes"),
    [
        ("/old-name/shop/waits?q=1", "/studio/shop/waits?q=1"),
        ("/old-name/", "/studio/"),
        ("/studio/shop", "/studio/shop/"),
        ("/shop/tasks/fix-the-login", "/studio/shop/tasks/fix-the-login"),
        ("/shop/backlog?filter=x", "/studio/shop/backlog?filter=x"),
        ("/shop/no-such-view?x=1", "/studio/shop/"),
        ("/shop", "/studio/shop/"),
    ],
)
def test_the_machines_other_name_and_an_address_with_no_machines_name_go_to_the_same_page(
    board: Board, asked: str, goes: str
) -> None:
    answer = board.main().get(asked, follow_redirects=False)
    assert (answer.status_code, answer.headers["location"]) == (302, goes)
    assert board.main().head(asked, follow_redirects=False).status_code == 302


@pytest.mark.parametrize("asked", ["/nowhere/", "/studio/nowhere", "/nowhere"])
def test_an_address_no_page_means_is_404(board: Board, asked: str) -> None:
    assert board.main().get(asked, follow_redirects=False).status_code == 404


def test_the_main_listener_reads_nothing_for_a_host_that_is_none_of_its_own_names(
    board: Board,
) -> None:
    refused = board.main().get("/api/server", headers={"Host": "evil.example:4999"})
    assert refused.status_code == 403
    assert "open it as http://127.0.0.1:4999/" in refused.text
    for host in ("127.0.0.1", "localhost:4999", "[::1]:4999"):
        assert (
            board.main().get("/api/server", headers={"Host": host}).status_code == 200
        )


def test_a_task_held_for_the_owner_is_one_thing_that_waits(board: Board) -> None:
    held = OwnerHold(on="criteria", line="approve the criteria", since=MOMENT)
    tasks.create(board.state, record("add-a-flag", status="building", hold=held))
    [row] = board.main().get("/api/workspaces").json()
    assert row["waits"] == 1
