"""The add-ons at the board's real page, API and lifespan boundaries."""

import time
from typing import TYPE_CHECKING

import httpx
import msgspec

from fakes.records import MOMENT, record
from lem.addons.inbox import messages, records, schedule
from lem.addons.peers import registry, rows, table
from lem.cli.serve import inbox
from lem.store import owner, tasks
from unit.board.pages.markup import Parsed

if TYPE_CHECKING:
    import pytest

    from unit.board.service.given import Board


def test_the_board_serves_the_same_peer_on_the_index_api_and_switcher(
    board: Board,
) -> None:
    class Joined:
        trouble = None
        known: dict[str, object] = {}

        def reload(self) -> dict[str, object]:
            return {}

        async def spaces(self, own: tuple[rows.Row, ...]) -> tuple[rows.Row, ...]:
            remote = rows.Row(name="shop", host="desk", url="/desk/shop/", waits=3)
            return (*own, remote)

    client = board.main()
    solo = Parsed(client.get("/studio/shop/").text).root.one(cls="brand")
    assert solo.one(cls="b-name").raw() == "Lem"
    assert solo.one(cls="b-repo").raw() == "shop"
    assert not solo.all(cls="b-host")

    board.app.state.peer_registry = Joined()
    assert {row["url"] for row in client.get("/api/workspaces").json()} == {
        "/studio/shop/",
        "/desk/shop/",
    }
    assert "desk/shop" in client.get("/").text
    page = client.get("/studio/shop/").text
    brand = Parsed(page).root.one(cls="brand")
    assert brand.one(cls="b-name").raw() == "Lem"
    assert brand.one(cls="b-host").raw() == "studio"
    assert brand.one(cls="b-repo").raw() == "shop"
    assert 'href="/desk/shop/"' in page
    assert " · Lem · studio/shop · " in page
    assert page.count('aria-current="true"') >= 1
    assert {
        row["host"]
        for row in client.get("/api/workspaces", headers={"Lem-Hop": "1"}).json()
    } == {"studio"}


def test_a_joined_board_names_its_machine_even_when_its_peer_has_no_workspaces(
    board: Board,
) -> None:
    async def address(host: str, port: int) -> str:
        return f"https://{host}.test.invalid:{port}"

    table.change(board.home, "desk", 19037)
    board.app.state.peer_registry = registry.Registry(
        home=board.home,
        own="studio",
        address=address,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=[])),
    )
    client = board.main()
    page = client.get("/studio/shop/").text
    assert " · Lem · studio/shop · " in page
    assert '<span class="ws-host">studio</span>' in page
    assert 'id="ws-switcher"' not in page


def test_the_inbox_turn_runs_in_the_servers_life_and_uses_the_door_for_each_real_workspace(
    opened: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: list[schedule.Target] = []

    def cycle(targets: schedule.Targets, report: schedule.Report) -> None:
        observed.extend(targets())
        report("shop", "The Inbox did not answer.")

    monkeypatch.setattr(schedule, "cycle", cycle)
    monkeypatch.setattr(schedule, "INTERVAL", 0.01)
    inbox.bind(opened.app)
    assert opened.app.state.inbox_turn.name == "the look at the Inbox"
    with opened.main() as client:
        deadline = time.monotonic() + 10
        while not observed and time.monotonic() < deadline:
            time.sleep(0.01)
        assert "The Inbox did not answer." in client.get("/studio/shop/").text
    target = observed[0]
    assert target.where.checkout == opened.checkout
    assert target.url == f"{opened.app.state.facts.tailnet.rstrip('/')}/studio/shop/"


def test_the_task_page_shows_the_inbox_thread_and_explains_a_missing_address(
    board: Board,
) -> None:
    tasks.create(board.state, record("fix-the-login"))
    owner.change(board.home, None, MOMENT, away=True)
    inbox.bind(board.app)
    wait = records.Wait(
        key="session:fix-the-login", task="fix-the-login", kind="session", since=MOMENT
    )
    sent = messages.Sent(
        message_id="first", thread_id="1", url="http://localhost/thread/1"
    )
    entry = records.Entry(wait=wait, key=wait.key, sent=sent)
    saved = records.Record(
        door=messages.Door(running=True, tailnet_url="https://phone.test.invalid"),
        entries=(entry,),
    )
    path = board.state / "inbox.json"
    path.write_bytes(msgspec.json.encode(saved))
    client = board.main()
    url = "/studio/shop/tasks/fix-the-login"
    assert 'href="https://phone.test.invalid/thread/1"' in client.get(url).text
    path.write_bytes(msgspec.json.encode(records.Record()))
    assert "The Inbox has no tailnet address." in client.get(url).text
    owner.change(board.home, None, MOMENT, away=False)
    assert 'id="fact-inbox"' not in client.get(url).text
