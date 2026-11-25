"""The peer table and the one-hop rules, with no tailnet connections."""

import asyncio
from typing import TYPE_CHECKING

import httpx
import pytest

from lem.addons.peers import commands, look, registry, requests, rows, table, tailnet
from lem.kernel import folders
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

PEER = "beta"
PORT = 19037
BASE = f"https://{PEER}.test.invalid:{PORT}"
SPACE = tailnet.Status(
    suffix="test.invalid",
    own=tailnet.Machine(dns="alpha.test.invalid."),
    peers={PEER: tailnet.Machine(dns="beta.test.invalid.")},
)


async def address(host: str, port: int) -> str:
    """The stand-in receives only the chosen test machine."""
    assert (host, port) == (PEER, PORT)
    return BASE


def test_dns_names_and_ports() -> None:
    assert tailnet.parse("Beta.Test.Invalid.:19037", SPACE.suffix, 1) == (PEER, PORT)
    assert tailnet.parse(PEER, SPACE.suffix, PORT) == (PEER, PORT)
    for bad in (
        "beta.other.invalid",
        "-beta",
        "beta/foo",
        "beta:0",
        "beta:65536",
        "beta:²",
    ):
        with pytest.raises(Refusal):
            tailnet.parse(bad, SPACE.suffix, PORT)
    for bad in ("alpha", "push", "unknown"):
        with pytest.raises(Refusal):
            tailnet.member(bad, SPACE)
    assert tailnet.address(SPACE.suffix, PEER, PORT) == BASE


def test_header_allowlist_and_redirect_namespace() -> None:
    sent = requests.outgoing(
        {
            "cookie": "secret=owner; lem_board=wide",
            "authorization": "key",
            "origin": "test",
            "accept": "text/html",
            "last-event-id": "5",
        },
        (rows.Row(name="shop", host="alpha", path="/work/Łódź"),),
    )
    assert sent["Cookie"] == "lem_board=wide"
    assert sent["Lem-Hop"] == "1"
    assert sent["Accept"] == "text/html" and sent["Last-Event-ID"] == "5"
    assert "authorization" not in sent and "origin" not in sent
    assert rows.from_header(sent["Lem-Spaces"])[0].path == "/work/Łódź"
    assert requests.returned("Set-Cookie", "unrelated=bad", PEER, BASE) is None
    assert (
        requests.returned("Set-Cookie", "lem_board=yes", PEER, BASE) == "lem_board=yes"
    )
    assert (
        requests.location("/assets/a.css?style=wide", PEER, BASE)
        == "/beta/assets/a.css?style=wide"
    )
    assert requests.location(BASE + "/beta/shop/", PEER, BASE) == "/beta/shop/"
    assert requests.location("/", PEER, BASE) == "/"
    for foreign in (
        "https://else.invalid/a",
        "//else.invalid/a",
        "/beta/%2e%2e/api",
        "/%2Fhost",
    ):
        assert requests.location(foreign, PEER, BASE) is None


def test_table_changes_preserve_other_settings_and_check_before_write(
    tmp_path: Path,
) -> None:
    home = folders.home_marked(tmp_path / "home")
    machine = home / "machine.toml"
    machine.write_text("# comment\n[serve]\nport = 19039\n")
    assert table.change(home, PEER, PORT) == {PEER: PORT}
    assert table.change(home, "gamma", 19038) == {PEER: PORT, "gamma": 19038}
    assert table.change(home, PEER, None) == {"gamma": 19038}
    assert "# comment" in machine.read_text() and "port = 19039" in machine.read_text()
    bad = "# comment\n[peers]\nbeta = -1\ngamma = 19038\n"
    machine.write_text(bad)
    with pytest.raises(Refusal, match="peers"):
        table.read(home)
    for port in (PORT, None):
        with pytest.raises(Refusal, match="peers"):
            table.change(home, PEER, port)
        assert machine.read_text() == bad
    assert registry.Registry(home=home, own="alpha").reload() == {}


def test_board_rows_use_local_addresses_and_keep_unreachable_rows() -> None:
    beta = look.Peer(PEER, PORT)
    beta.seen = look.Seen(
        reachable=True,
        answered=10,
        rows=(
            rows.located(
                rows.Row(name="shop", url="https://else.invalid", waits=2), PEER
            ),
        ),
    )
    assert beta.shown()[0].url == "/beta/shop/"
    beta.failed("not reachable")
    gray = beta.shown()[0]
    assert gray.reachable is False and gray.answered == 10 and gray.waits is None
    own = rows.Row(name="app", host="alpha", waits=1)
    assert rows.with_own(
        (gray, rows.Row(name="old", host="alpha")), (own,), "alpha"
    ) == (own, gray)
    assert rows.with_own((), (own,), "alpha") == (own,)


def test_malformed_or_deep_json_does_not_escape_as_an_exception() -> None:
    deep = "[" * 2000 + "0" + "]" * 2000
    assert rows.from_header(deep) == ()
    assert rows.from_header("a" * (rows.SPACES_CAP + 1)) == ()
    with pytest.raises(ValueError, match="no board JSON"):
        look.decode(deep.encode(), tuple[rows.Row, ...])


def test_join_records_a_sleeping_peer_but_refuses_the_wrong_identity(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        home = tmp_path / "home"
        asked: list[str] = []

        def replies(request: httpx.Request) -> httpx.Response:
            asked.append(request.url.path)
            assert request.headers["Lem-Hop"] == "1"
            raise httpx.ConnectTimeout("sleep", request=request)

        async with httpx.AsyncClient(transport=httpx.MockTransport(replies)) as client:
            found = await commands.join(f"{PEER}:{PORT}", SPACE, client, home)
        assert not found.reachable and table.read(home) == {PEER: PORT}
        assert asked == ["/api/server"]
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda incoming: httpx.Response(
                    200, json={"host": "gamma", "install": {"version": "test"}}
                )
            )
        ) as client:
            with pytest.raises(Refusal, match="answers as gamma"):
                await commands.join(f"{PEER}:19038", SPACE, client, home)
        assert table.read(home) == {PEER: PORT}

    asyncio.run(run())


def test_registry_keeps_fresh_rows_and_reloads_port_changes(tmp_path: Path) -> None:
    async def run() -> None:
        home = tmp_path / "home"
        table.change(home, "alpha", PORT)
        table.change(home, PEER, PORT)
        queries: list[str] = []

        def listed(request: httpx.Request) -> httpx.Response:
            queries.append(request.url.path)
            return httpx.Response(
                200, json=[{"name": "shop", "url": "/beta/shop/", "waits": 3}]
            )

        known = registry.Registry(
            home=home,
            own="alpha",
            address=address,
            transport=httpx.MockTransport(listed),
        )
        own = rows.Row(name="app", host="alpha", waits=1)
        combined = await known.spaces((own,))
        assert [(row.host, row.name) for row in combined] == [
            ("beta", "shop"),
            ("alpha", "app"),
        ]
        assert await known.spaces((own,)) == combined
        assert queries == ["/api/workspaces"]
        before = known.known[PEER]
        table.change(home, PEER, 19038)
        after = known.reload()[PEER]
        assert before is not after and after.port == 19038
        table.change(home, PEER, None)
        assert not known.reload()

    asyncio.run(run())


def test_concurrent_peer_edits_keep_both_hosts(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    home = folders.home_marked(tmp_path / "home")
    with ThreadPoolExecutor(max_workers=2) as pool:
        alpha = pool.submit(table.change, home, "beta", PORT)
        beta = pool.submit(table.change, home, "gamma", 19038)
        assert "beta" in alpha.result()
        assert "gamma" in beta.result()
    assert table.read(home) == {"beta": PORT, "gamma": 19038}


def test_cli_leaves_a_peer_without_looking_for_tailnet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import os

    from fakes.command import lem
    from lem.kernel import paths

    home = paths.home(os.environ)
    table.change(home, PEER, PORT)
    monkeypatch.setenv("PATH", str(tmp_path))
    seen = lem("serve", "leave", PEER)
    assert seen.code == 0
    assert seen.result() == {"left": PEER, "peers": []}
    assert lem("serve", "peers").result() == {"peers": []}
