"""The board gives the owner's visible page one notice per installed release."""

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import TYPE_CHECKING

import pytest

from lem.board import update, update_record, workspaces
from lem.board.door import Door
from lem.kernel import logs, release
from lem.kernel.errors import Fault
from unit.board.service.given import DOOR, HOST, MAC, MAIN, OWNER, made, workspace_at

if TYPE_CHECKING:
    from pathlib import Path

ADDRESS = "/api/server/update"
MAIN_PAGE = {"Origin": f"http://127.0.0.1:{MAIN}"}
OLDER = "0.4.0"


def test_the_first_start_ever_has_no_notice_and_records_its_release(
    tmp_path: Path,
) -> None:
    board = made(tmp_path, None)
    assert not (board.home / update_record.STATE).exists()
    with board.main() as client:
        assert client.get(ADDRESS).status_code == 204
        assert client.post(ADDRESS, headers=MAIN_PAGE).status_code == 204
    assert update_record.read(board.home) == update_record.State(
        last_version=release.running()
    )


def test_a_start_after_a_stop_with_a_newer_release_shows_both_releases(
    tmp_path: Path,
) -> None:
    board = made(tmp_path, None)
    update.started(board.home, OLDER)
    with board.main() as client:
        assert client.get(ADDRESS).status_code == 200
        assert client.head(ADDRESS).status_code == 200
        assert client.post(ADDRESS).status_code == 403
        reply = client.post(ADDRESS, headers=MAIN_PAGE)
        assert reply.status_code == 200
        assert reply.json() == {
            "version": release.running(),
            "previous_version": OLDER,
        }
        assert client.get(ADDRESS).status_code == 204
        assert client.post(ADDRESS, headers=MAIN_PAGE).status_code == 204


def test_a_start_of_the_same_release_shows_no_notice(tmp_path: Path) -> None:
    board = made(tmp_path, None)
    update.started(board.home, release.running())
    with board.main() as client:
        assert client.get(ADDRESS).status_code == 204
        assert client.post(ADDRESS, headers=MAIN_PAGE).status_code == 204


def test_the_swap_path_shows_one_notice_not_two(tmp_path: Path) -> None:
    board = made(tmp_path, None)
    update.started(board.home, OLDER)
    update.swapped(board.home, OLDER)
    with board.main() as client:
        assert client.post(ADDRESS, headers=MAIN_PAGE).json() == {
            "version": release.running(),
            "previous_version": OLDER,
        }
        assert client.post(ADDRESS, headers=MAIN_PAGE).status_code == 204

    update.swapped(board.home, OLDER)
    restarted = made(tmp_path / "restarted", None)
    restarted.app.state.home = board.home
    with restarted.main() as client:
        assert client.get(ADDRESS).status_code == 204
        assert client.post(ADDRESS, headers=MAIN_PAGE).status_code == 204


def test_a_swap_from_a_release_that_wrote_no_record_shows_the_notice(
    tmp_path: Path,
) -> None:
    board = made(tmp_path, None)
    update.swapped(board.home, OLDER)
    with board.main() as client:
        reply = client.post(ADDRESS, headers=MAIN_PAGE)
    assert reply.json()["previous_version"] == OLDER


def test_the_door_and_main_listener_share_one_notice(tmp_path: Path) -> None:
    door = Door(name=MAC, port=DOOR, owner=OWNER, reread=lambda before: before)
    board = made(tmp_path, door)
    update.started(board.home, OLDER)
    with board.door() as phone:
        own = {"Host": f"{MAC}:{DOOR}", "Tailscale-User-Login": OWNER}
        assert (
            phone.post(
                ADDRESS, headers={**own, "Origin": "https://other.example"}
            ).status_code
            == 403
        )
        assert (
            phone.post(
                ADDRESS, headers={**own, "Origin": door.url().rstrip("/")}
            ).status_code
            == 200
        )
    with board.main() as client:
        assert client.post(ADDRESS, headers=MAIN_PAGE).status_code == 204


def test_two_pages_that_read_at_once_get_one_notice(tmp_path: Path) -> None:
    board = made(tmp_path, None)
    version = release.running()
    update.started(board.home, OLDER)
    update.started(board.home, version)
    with ThreadPoolExecutor(max_workers=2) as pages:
        replies = list(pages.map(partial(update.seen, board.home), (version, version)))
    assert (
        replies.count(update_record.Notice(version=version, previous_version=OLDER))
        == 1
    )
    assert replies.count(None) == 1


def test_a_downgrade_makes_no_notice_and_a_seen_release_stays_seen(
    tmp_path: Path,
) -> None:
    board = made(tmp_path, None)
    update.started(board.home, "1.0.0")
    update.started(board.home, "2.0.0")
    assert update.seen(board.home, "1.0.0") is None
    assert update.seen(board.home, "2.0.0") == update_record.Notice(
        version="2.0.0", previous_version="1.0.0"
    )
    update.started(board.home, "1.0.0")
    assert update_record.read(board.home).pending is None
    update.started(board.home, "2.0.0")
    assert update.seen(board.home, "2.0.0") is None
    update.started(board.home, "3.0.0")
    assert update.seen(board.home, "3.0.0") == update_record.Notice(
        version="3.0.0", previous_version="2.0.0"
    )


def test_a_record_that_does_not_read_is_a_fault_the_page_shows(tmp_path: Path) -> None:
    board = made(tmp_path, None)
    with board.main() as client:
        (board.home / update_record.STATE).write_bytes(b"{")
        for reply in (client.get(ADDRESS), client.post(ADDRESS, headers=MAIN_PAGE)):
            assert reply.status_code == 500
            assert (
                f"update record {board.home / update_record.STATE} does not read"
                in reply.text
            )
    for recorded in (update.started, update.swapped):
        with pytest.raises(Fault, match="does not read"):
            recorded(board.home, OLDER)


def test_a_server_starts_on_a_record_that_does_not_read_and_logs_the_fault(
    tmp_path: Path,
) -> None:
    board = made(tmp_path, None)
    record = board.home / update_record.STATE
    record.write_bytes(b"{")
    for start in (1, 2):
        with board.main() as client:
            assert client.get(f"/{HOST}/shop/").status_code == 200
            reply = client.get(ADDRESS)
        assert reply.status_code == 500
        assert f"update record {record} does not read" in reply.text
        log = (board.home / logs.LOG).read_text(encoding="utf-8")
        assert "Traceback (most recent call last)" in log
        assert log.count(f"update record {record} does not read") == start
    assert record.read_bytes() == b"{"


def test_a_home_the_server_cannot_write_is_a_fault_the_page_shows(
    tmp_path: Path,
) -> None:
    board = made(tmp_path, None)
    update.started(board.home, OLDER)
    with board.main() as client:
        board.home.chmod(0o500)
        try:
            reply = client.post(ADDRESS, headers=MAIN_PAGE)
            asked = client.get(ADDRESS)
        finally:
            board.home.chmod(0o700)
    assert reply.status_code == 500
    assert (
        f"could not write its update record {board.home / update_record.STATE}"
        in reply.text
    )
    assert asked.status_code == 200


def test_the_board_page_and_the_workspaces_page_hold_the_note(tmp_path: Path) -> None:
    board = made(tmp_path, None)
    workspaces.noted(board.home, workspace_at(tmp_path / "desk"))
    with board.main() as client:
        listed = client.get("/")
        page = client.get(f"/{HOST}/shop/")
    assert "Workspaces · Lem" in listed.text
    for shown in (listed, page):
        assert shown.status_code == 200
        assert (
            'id="board-update" data-turbo-permanent data-controller="update"'
            in shown.text
        )
