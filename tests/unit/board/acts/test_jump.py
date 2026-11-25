"""The jump to a task's own session, on the owner's click on a page of this Mac: only the session
Lem opened last for a task of the workspace, never through the door, and only from the board's
own page."""

from typing import TYPE_CHECKING

from unit.board.acts.acts import made, opened
from unit.board.acts.conftest import ORIGIN

if TYPE_CHECKING:
    import httpx

    from unit.board.acts.conftest import Board


def jump(board: Board, session: str, **headers: str) -> httpx.Response:
    """The page's request for the jump to `session`."""
    sent = {"origin": ORIGIN, "sec-fetch-site": "same-origin", **headers}
    return board.client.post(f"{board.base}/agterm/{session}", headers=sent)


def test_the_board_jumps_only_to_a_tasks_own_session(board: Board) -> None:
    made(board, status="building", lead="builder")
    session = opened(board)
    found = jump(board, session.upper())
    assert (found.status_code, found.json()) == (
        200,
        {"done": True, "said": "Switched to the session."},
    )
    assert board.terminal.panes[session].selected
    other = jump(board, "S-MINE")
    assert other.status_code == 422
    assert other.json() == {
        "done": False,
        "said": "That is no session of this workspace's tasks.",
    }


def test_a_session_agterm_no_longer_has_says_it_did_not_switch(board: Board) -> None:
    made(board, status="building", lead="builder")
    session = opened(board)
    del board.terminal.panes[session]
    found = jump(board, session)
    assert found.status_code == 422
    assert found.json()["said"].startswith("agterm did not switch")


def test_no_jump_from_another_site(board: Board) -> None:
    made(board, status="building", lead="builder")
    session = opened(board)
    elsewhere = jump(board, session, origin="https://evil.example")
    assert elsewhere.status_code == 403
    assert not board.terminal.panes[session].selected


def test_no_jump_through_the_door(door: Board) -> None:
    through = door.client.post(f"{door.base}/agterm/S-1")
    assert through.status_code == 403
    assert "the phone has no agterm" in through.json()["said"]
