"""The board's notifications: what a subscription may name, what is new on a list, the machine's
key and its tokens, a device turned on and off from the board's own page, a push recorded with no
request, a device its service no longer knows, and the watcher's push of a gained row."""

import base64
import json
import stat
import time
from typing import TYPE_CHECKING

import msgspec
import pytest
from py_vapid import Vapid02

from fakes.records import MOMENT, record
from lem.adapters import notify_push_devices as devices
from lem.adapters import notify_push_key as keys
from lem.adapters import notify_push_send as send
from lem.adapters.notify_push import PushNotifier
from lem.adapters.notify_push_endpoint import device_of, refusal
from lem.app.owner.forge import Look as ForgeLook
from lem.app.owner.looking import Looked
from lem.board.push import news, waits
from lem.board.push.watch import Watcher
from lem.model.owner.looks import Look, Session
from lem.records.holds import BreakerHold, OwnerHold
from lem.records.owner import Presence
from lem.store import tasks

if TYPE_CHECKING:
    from unit.board.service.given import Board

APPLE = "https://web.push.apple.com/QGuQyavXutnMH"
FCM = "https://fcm.googleapis.com/fcm/send/abc"
OWN_PAGE = {"Origin": "http://127.0.0.1:4999", "Sec-Fetch-Site": "same-origin"}
IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1"
)


@pytest.mark.parametrize(
    "endpoint",
    [
        APPLE,
        FCM,
        "https://updates.push.services.mozilla.com/wpush/v2/x",
        "https://wns2-par02p.notify.windows.com/w/?token=x",
    ],
)
def test_an_endpoint_at_a_push_service_a_browser_uses_is_taken(endpoint: str) -> None:
    assert refusal(endpoint) is None


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://web.push.apple.com/x",
        "https://web.push.apple.com:8443/x",
        "https://user:pw@web.push.apple.com/x",
        "https://evil.example/x",
        "https://push.apple.com.evil.example/x",
        "https://.push.apple.com/x",
        "https://10.0.0.1/x",
        "https://[::1]/x",
        "https://web.push.apple.com:99999/x",
        "",
        42,
        "https://web.push.apple.com/" + "x" * 2100,
    ],
)
def test_only_https_at_a_push_service_a_browser_uses(endpoint: object) -> None:
    assert refusal(endpoint) is not None


def test_a_device_is_named_by_its_kind_and_browser() -> None:
    assert device_of(IPHONE) == "iPhone · Safari"
    assert (
        device_of("Mozilla/5.0 (X11; Linux x86_64) Firefox/120.0") == "Linux · Firefox"
    )
    assert device_of("") == "a device · a browser"


def test_the_first_look_sends_nothing_and_a_gained_row_is_news_once() -> None:
    first, memory = news.gained(None, ["merge:a"], 0.0)
    assert first == ()
    fresh, memory = news.gained(memory, ["merge:a", "breaker:b:1"], 10.0)
    assert fresh == ("breaker:b:1",)
    again, _ = news.gained(memory, ["merge:a", "breaker:b:1"], 20.0)
    assert again == ()


def test_a_row_that_leaves_and_comes_back_soon_is_not_news_and_later_it_is() -> None:
    _, memory = news.gained(None, ["merge:a"], 0.0)
    _, memory = news.gained(memory, [], 10.0)
    soon, memory = news.gained(memory, ["merge:a"], 10.0 + news.FLAP - 1)
    assert soon == ()
    _, memory = news.gained(memory, [], 400.0)
    later, _ = news.gained(memory, ["merge:a"], 400.0 + news.FLAP + 1)
    assert later == ("merge:a",)


def test_the_machines_key_is_made_once_kept_to_its_owner_and_given_as_its_public_point(
    board: Board,
) -> None:
    first = board.main().get("/api/push/key").json()["key"]
    path = board.home / keys.KEY
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert board.main().get("/api/push/key").json()["key"] == first
    assert keys.public_of(keys.key_of(board.home)) == first
    assert len(first) == 87
    assert board.main().head("/api/push/key").status_code == 200


def test_the_token_names_the_push_services_origin_ends_within_a_day_and_is_used_again(
    board: Board,
) -> None:
    key = keys.key_of(board.home)
    tokens = keys.Tokens(key)
    now = time.time()
    header = tokens.header(APPLE + "/device", now)
    assert header.startswith("vapid t=")
    jwt = header.split("t=", 1)[1].split(",", 1)[0]
    body = jwt.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    assert claims["aud"] == "https://web.push.apple.com"
    assert now < claims["exp"] <= now + 86_400
    assert claims["sub"] == keys.SUBJECT
    assert Vapid02.verify(header)
    assert tokens.header(APPLE + "/other", now + 60) == header
    assert tokens.header(APPLE + "/other", now + keys.TOKEN_REUSE + 1) != header
    assert tokens.header(FCM, now + 60) != header


def subscribed(
    board: Board, endpoint: str = APPLE, **more: object
) -> dict[str, object]:
    body = {"endpoint": endpoint, "keys": {"p256dh": "k", "auth": "a"}, **more}
    headers = {**OWN_PAGE, "User-Agent": IPHONE}
    answer = board.main().post("/api/push/subscribe", json=body, headers=headers)
    return {"status": answer.status_code, **answer.json()}


def test_a_device_on_the_boards_own_page_turns_them_on_and_off(board: Board) -> None:
    on = subscribed(board)
    assert on == {"status": 200, "on": True, "device": "iPhone · Safari", "devices": 1}
    assert subscribed(board)["devices"] == 1
    shown = board.main().get("/api/server").json()["push"]["devices"]
    assert shown[0]["device"] == "iPhone · Safari"
    assert APPLE not in json.dumps(shown)
    off = board.main().post(
        "/api/push/unsubscribe", json={"endpoint": APPLE}, headers=OWN_PAGE
    )
    assert off.json() == {"on": False, "removed": True, "devices": 0}


def test_another_origin_an_address_that_is_no_push_service_and_no_json_are_refused(
    board: Board,
) -> None:
    body = {"endpoint": APPLE}
    other = board.main().post(
        "/api/push/subscribe", json=body, headers={"Origin": "https://evil.example"}
    )
    assert other.status_code == 403
    assert subscribed(board, "https://evil.example/push")["status"] == 422
    deep = "[" * 100_000 + "]" * 100_000
    nested = board.main().post(
        "/api/push/subscribe", content=deep[:4000], headers=OWN_PAGE
    )
    assert nested.status_code == 400
    empty = board.main().post("/api/push/subscribe", headers=OWN_PAGE)
    assert empty.status_code == 400
    assert devices.read(board.home).devices == ()


def test_at_most_twenty_devices_get_them(board: Board) -> None:
    for number in range(20):
        assert subscribed(board, f"{FCM}{number}")["status"] == 200
    assert subscribed(board, f"{FCM}x")["status"] == 422


def test_a_test_push_to_the_device_that_asks_is_recorded_with_no_request(
    board: Board,
) -> None:
    subscribed(board)
    answer = board.main().post(
        "/api/push/test", json={"endpoint": APPLE}, headers=OWN_PAGE
    )
    assert answer.json()["status"] == 201
    [line] = (board.home / send.RECORD).read_text().splitlines()
    pushed = json.loads(line)
    assert pushed["endpoint"] == APPLE
    assert pushed["topic"] == send.TOPIC
    assert pushed["authorization"].startswith("vapid t=")
    latest = board.main().get("/api/push/latest").json()
    assert latest["tag"] == "lem-test"
    unknown = board.main().post(
        "/api/push/test", json={"endpoint": FCM}, headers=OWN_PAGE
    )
    assert unknown.status_code == 422


def test_what_the_worker_shows_before_any_push_is_the_fixed_line(board: Board) -> None:
    assert board.main().get("/api/push/latest").json()["body"] == (
        "Something waits for you in Lem"
    )
    assert board.main().head("/api/push/latest").status_code == 200


def test_a_device_its_service_no_longer_knows_goes_and_the_token_is_used_again(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    subscribed(board)
    subscribed(board, FCM)
    headers: list[str] = []

    def gone(home: object, endpoint: str, header: str) -> send.Reply:
        headers.append(header)
        status = 410 if endpoint == FCM else 201
        return send.Reply(device="", status=status, gone=status == 410)

    monkeypatch.setattr(send, "recorded", gone)
    notifier = PushNotifier(board.home, {})
    replies = notifier.tested(None)
    assert [reply.gone for reply in replies] == [False, True]
    assert [one.endpoint for one in devices.read(board.home).devices] == [APPLE]
    notifier.tested(APPLE)
    assert headers[0] == headers[2]
    last = json.loads(msgspec.json.encode(devices.read(board.home).last))
    assert [reply["status"] for reply in last["results"]] == [201]


def test_a_row_gained_while_the_owner_is_away_is_sent_and_a_demo_sends_nothing(
    board: Board,
) -> None:
    subscribed(board)
    watcher = Watcher(home=board.home, notifier=PushNotifier(board.home, {}))
    assert watcher.look(0.0) == 0
    held = OwnerHold(on="criteria", line="approve the criteria", since=MOMENT)
    tasks.create(board.state, record("add-a-flag", status="building", hold=held))
    assert watcher.look(10.0) == 1
    said = devices.read(board.home).latest
    assert said is not None
    assert said.url.endswith("/shop/tasks/add-a-flag")
    assert "Add a flag · shop" in said.body
    assert watcher.look(20.0) == 0
    (board.state / "demo").write_text("examples")
    tasks.create(board.state, record("tidy-the-docs", status="building", hold=held))
    assert watcher.look(30.0) == 0


def test_no_push_goes_for_a_held_task_while_its_session_works_and_one_when_its_turn_ended() -> (
    None
):
    breaker = BreakerHold(number=1, since=MOMENT)
    held = record("add-a-flag", status="building", hold=breaker)
    working = Session(live=True, since=MOMENT, working=True)
    idle = Session(live=True, since=MOMENT)
    seen: waits.Seen = {}

    def looked(session: Session) -> Looked:
        look = Look(record=held, session=session, worktree=True)
        return Looked(looks=(look,), presence=Presence(), forge=ForgeLook())

    assert waits.news_in(seen, "shop", looked(working), 0.0) == []
    assert waits.news_in(seen, "shop", looked(working), 10.0) == []
    [(_, _, row)] = waits.news_in(seen, "shop", looked(idle), 20.0)
    assert row.kind == "breaker"
