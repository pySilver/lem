"""The tailnet door's check of every request, and the main listener's check of a page's act."""

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from starlette.requests import Request

from lem.board import door as doors
from lem.board import listener

if TYPE_CHECKING:
    from collections.abc import Iterator

    import pytest

    from unit.board.service.given import Board

DOOR = 4998
MAC = "studio.example.ts.net"
OWNER = "owner@example.com"
OWN = f"{MAC}:{DOOR}"


def seen(**headers: str) -> doors.Seen:
    return doors.seen_of(
        (name.replace("_", "-"), word) for name, word in headers.items()
    )


def refusal(method: str = "GET", **headers: str) -> str | None:
    return doors.door_refusal(seen(**headers), method, OWNER, MAC, DOOR)


def test_the_owners_login_for_the_macs_own_name_is_let_in() -> None:
    assert refusal(host=OWN, tailscale_user_login=OWNER) is None
    assert refusal(host=MAC, tailscale_user_login="OWNER@example.com") is None
    assert (
        refusal(host=OWN, tailscale_user_login="=?utf-8?q?owner=40example=2Ecom?=")
        is None
    )


def test_another_host_name_is_refused() -> None:
    said = refusal(host="evil.example", tailscale_user_login=OWNER)
    assert said == "This address is not the board's name on the tailnet."
    assert refusal(host=f"{MAC}:1", tailscale_user_login=OWNER) is not None


def test_another_login_and_no_login_are_refused() -> None:
    assert (
        refusal(host=OWN, tailscale_user_login="peer@example.com")
        == doors.NOT_THE_OWNER
    )
    assert "carries none" in (refusal(host=OWN) or "")
    two = doors.seen_of(
        (
            ("host", OWN),
            ("tailscale-user-login", OWNER),
            ("tailscale-user-login", OWNER),
        )
    )
    assert doors.door_refusal(two, "GET", OWNER, MAC, DOOR) == doors.NOT_THE_OWNER


def test_a_request_through_funnel_is_refused_whatever_its_login() -> None:
    said = refusal(host=OWN, tailscale_user_login=OWNER, tailscale_funnel_request="?1")
    assert said == "This board is not served through Tailscale Funnel."


def test_a_post_from_another_site_is_refused_and_one_from_the_board_is_let_in() -> None:
    login = {"host": OWN, "tailscale_user_login": OWNER}
    assert (
        refusal("POST", origin=f"https://{OWN}", sec_fetch_site="same-origin", **login)
        is None
    )
    assert refusal("POST", **login) is None
    assert "another site" in (
        refusal("POST", sec_fetch_site="cross-site", **login) or ""
    )
    assert "another origin" in (
        refusal("POST", origin="https://evil.example", **login) or ""
    )


def test_a_login_that_is_not_the_owners_reads_his_login_again_at_most_once_in_the_wait(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logins: Iterator[str] = iter(["peer@example.com", "third@example.com"])
    asked: list[str] = []

    def reread(before: str) -> str:
        asked.append(before)
        return next(logins)

    clock = iter([100.0, 110.0, 120.0])
    monkeypatch.setattr(doors.time, "monotonic", lambda: next(clock))
    door = doors.Door(name=MAC, port=DOOR, owner=OWNER, reread=reread, read_at=0.0)
    peer = seen(host=OWN, tailscale_user_login="peer@example.com")
    assert door.refusal(peer, "GET") is None
    assert door.owner == "peer@example.com"
    assert door.refusal(seen(host=OWN, tailscale_user_login=OWNER), "GET") is not None
    assert asked == [OWNER]


def test_the_door_lets_the_owner_in_and_refuses_another_at_its_own_port(
    opened: Board,
) -> None:
    door = opened.door()
    headers = {"Host": OWN, "Tailscale-User-Login": OWNER}
    assert door.get("/api/workspaces", headers=headers).status_code == 200
    stranger = {"Host": OWN, "Tailscale-User-Login": "peer@example.com"}
    assert door.get("/api/workspaces", headers=stranger).status_code == 403
    assert door.get("/api/workspaces").status_code == 403
    assert opened.main().get("/api/workspaces").status_code == 200


def test_the_door_does_not_stop_the_server(opened: Board) -> None:
    headers = {"Host": OWN, "Tailscale-User-Login": OWNER}
    answer = opened.door().post("/api/server/stop", headers=headers)
    assert answer.status_code == 405
    assert opened.stops == []


def act(client: str = "127.0.0.1", port: int = 4999, **headers: str) -> str | None:
    """The main listener's check of an act of a request from `client` to `port`."""
    pairs = [
        (name.replace("_", "-").encode(), word.encode())
        for name, word in headers.items()
    ]
    state = SimpleNamespace(facts=SimpleNamespace(door=DOOR))
    scope: dict[str, Any] = {
        "type": "http",
        "headers": pairs,
        "client": (client, 50000),
        "server": ("127.0.0.1", port),
        "app": SimpleNamespace(state=state),
    }
    return listener.act_refusal(Request(scope))


def test_the_boards_own_page_on_this_mac_is_let_in() -> None:
    own = {"host": "127.0.0.1:4999", "origin": "http://127.0.0.1:4999"}
    assert act(**own) is None
    assert act(sec_fetch_site="same-origin", **own) is None
    assert act(host="localhost:4999", origin="http://localhost:4999") is None
    assert act(port=DOOR) is None


def test_another_machine_another_site_and_a_name_that_points_here_are_refused() -> None:
    own = {"host": "127.0.0.1:4999", "origin": "http://127.0.0.1:4999"}
    assert "Only a page on this Mac" in (act(client="10.0.0.9", **own) or "")
    assert act(host="evil.example:4999", origin="http://evil.example:4999") is not None
    assert act(host="127.0.0.1:4999", origin="http://evil.example") is not None
    assert act(host="127.0.0.1:4999") is not None
    assert act(sec_fetch_site="cross-site", **own) is not None
