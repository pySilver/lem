"""Who may act: on the main listener only the board's own page on this Mac, with the board's own
origin; through the door the door's own check; a request that carries no form of the board's
acts on nothing."""

from typing import TYPE_CHECKING

import pytest
from starlette.datastructures import Headers
from starlette.testclient import TestClient

from lem.board.acts import asker
from unit.board.acts.acts import SLUG, made, read
from unit.board.acts.conftest import ORIGIN, PHONE
from unit.board.acts.test_answer import ANSWER, HELP, KEY, breaker

if TYPE_CHECKING:
    from unit.board.acts.conftest import Board

FIELDS = {"key": KEY, "option": "help", "words": HELP}


@pytest.mark.parametrize(
    "headers",
    [
        {"origin": "https://evil.example"},
        {"origin": "null"},
        {},
        {"origin": ORIGIN, "sec-fetch-site": "cross-site"},
        {"origin": f"{ORIGIN}, {ORIGIN}"},
    ],
)
def test_a_form_from_another_origin_or_none_is_refused_and_records_nothing(
    board: Board, headers: dict[str, str]
) -> None:
    breaker(board)
    response = board.client.post(
        f"{board.base}{ANSWER}", data=FIELDS, headers=headers, follow_redirects=False
    )
    assert response.status_code == 403
    assert "board's own page" in response.text
    assert read(board).task.questions == ()


def test_a_page_of_another_machine_acts_on_nothing_through_the_main_address(
    board: Board,
) -> None:
    breaker(board)
    other = TestClient(
        board.client.app, base_url=ORIGIN, client=("192.168.1.20", 50000)
    )
    response = other.post(
        f"{board.base}{ANSWER}",
        data=FIELDS,
        headers={"origin": ORIGIN},
        follow_redirects=False,
    )
    assert response.status_code == 403
    assert "Only a page on this Mac" in response.text
    assert read(board).task.questions == ()


def test_a_request_with_no_form_of_the_board_acts_on_nothing(board: Board) -> None:
    breaker(board)
    sent = {"origin": ORIGIN, "sec-fetch-site": "same-origin"}
    as_json = board.client.post(
        f"{board.base}{ANSWER}", json=FIELDS, headers=sent, follow_redirects=False
    )
    huge = board.client.post(
        f"{board.base}{ANSWER}",
        data={**FIELDS, "words": "x" * 20000},
        headers=sent,
        follow_redirects=False,
    )
    assert (as_json.status_code, huge.status_code) == (400, 400)
    assert read(board).task.questions == ()


def test_a_workspace_or_a_host_not_on_the_list_is_not_found(board: Board) -> None:
    made(board)
    sent = {"origin": ORIGIN, "sec-fetch-site": "same-origin"}
    for base in (f"{board.base}-other", "/another-mac/shop"):
        response = board.client.post(
            f"{base}/tasks/{SLUG}/answer", data=FIELDS, headers=sent
        )
        assert response.status_code == 404


def test_the_device_is_a_phone_by_its_client_hint_or_its_browser_and_else_a_computer() -> (
    None
):
    assert asker.device_of(Headers({"user-agent": PHONE})) == "phone"
    assert asker.device_of(Headers({"sec-ch-ua-mobile": "?1"})) == "phone"
    assert asker.device_of(Headers({"user-agent": "Mozilla/5.0 (Macintosh)"})) == (
        "computer"
    )
