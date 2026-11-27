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


def test_join_help_shows_when_to_add_the_port() -> None:
    from fakes.command import lem

    seen = lem("serve", "join", "--help")
    words = " ".join(seen.stdout.split())
    assert seen.code == 0
    assert "Usage: lem serve join [OPTIONS] HOST[:PORT]" in words
    assert "Add :PORT if the other machine's door uses a different port." in words
    assert "its own door port (4537 by default)" in words


@pytest.mark.parametrize("location", ("path", "local", "app", "override"))
def test_local_status_prefers_the_cli_and_runs_the_bundled_app(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, location: str
) -> None:
    from lem.adapters import tailscale_cli
    from lem.addons.peers import local
    from unit.board.service import tailscale_stand_in as stand_in

    path = tmp_path / "path"
    local_bin = tmp_path / "usr/local/bin"
    app = stand_in.made(
        tmp_path / "Tailscale.app/Contents/MacOS",
        "Tailscale",
        MagicDNSSuffix="app.invalid",
    )
    monkeypatch.delenv("TAILSCALE_BE_CLI", raising=False)
    monkeypatch.delenv("LEM_TAILSCALE", raising=False)
    monkeypatch.setenv("PATH", str(path))
    monkeypatch.setattr(
        tailscale_cli, "PLACES", (str(local_bin / "tailscale"), str(app))
    )
    if location in {"path", "override"}:
        stand_in.made(path, MagicDNSSuffix="path.invalid")
    if location != "app":
        stand_in.made(local_bin, MagicDNSSuffix="local.invalid")
    if location == "override":
        override = stand_in.made(
            tmp_path / "override", MagicDNSSuffix="override.invalid"
        )
        monkeypatch.setenv("LEM_TAILSCALE", str(override))
    assert local.status().suffix == f"{location}.invalid"


def test_report_keeps_healthy_peers_and_join_refuses_a_renamed_peer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lem.addons.peers import report

    def answer(request: httpx.Request) -> httpx.Response:
        host = request.url.host.partition(".")[0]
        if request.url.path == "/api/server":
            name = "renamed" if host == PEER else host
            return httpx.Response(
                200, json={"host": name, "install": {"version": "test"}}
            )
        assert (host, request.url.path) == ("gamma", "/api/workspaces")
        return httpx.Response(200, json=[{"name": "shop", "url": "/gamma/shop/"}])

    client = httpx.AsyncClient
    wire = httpx.MockTransport(answer)
    monkeypatch.setattr(report.local, "status", lambda: SPACE)
    monkeypatch.setattr(
        report.httpx, "AsyncClient", lambda **given: client(transport=wire)
    )

    async def run() -> None:
        async with client(transport=wire) as probe:
            with pytest.raises(Refusal, match="answers as renamed"):
                await commands.join(f"{PEER}:{PORT}", SPACE, probe, tmp_path)
        assert not table.read(tmp_path)
        changed, healthy = await report.report({PEER: PORT, "gamma": PORT})
        assert (changed.name, changed.reachable, changed.said) == (
            PEER,
            False,
            "beta answers as renamed",
        )
        assert (healthy.name, healthy.reachable, healthy.workspaces) == (
            "gamma",
            True,
            ("shop",),
        )

    asyncio.run(run())


def test_switcher_accepts_only_dns_labels_from_the_peer_header() -> None:
    supplied = rows.header(
        tuple(
            rows.Row(name="shop", host=host)
            for host in ("beta", "two words", "-beta", "beta.test.invalid")
        )
    )
    assert supplied is not None
    assert tuple(row.url for row in rows.from_header(supplied)) == ("/beta/shop/",)


def test_registry_reuses_one_successful_tailnet_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lem.addons.peers import address as peer_address
    from lem.addons.peers import local

    calls: list[None] = []
    now = 0.0
    offline = False

    def status() -> tailnet.Status:
        calls.append(None)
        if offline:
            raise Refusal("tailnet", "Tailscale is unavailable", "connect to Tailscale")
        return SPACE

    monkeypatch.setattr(local, "status", status)
    monkeypatch.setattr(peer_address, "monotonic", lambda: now)

    async def run() -> None:
        nonlocal now, offline
        board = registry.Registry(home=tmp_path, own="alpha")
        fresh = await asyncio.gather(
            board.address(PEER, PORT), board.address(PEER, PORT)
        )
        assert fresh == [BASE, BASE]
        assert await board.address(PEER, PORT + 1) == BASE.replace(
            str(PORT), str(PORT + 1)
        )
        assert len(calls) == 1
        now += look.LIST_FRESH
        offline = True
        with pytest.raises(Refusal, match="unavailable"):
            await board.address(PEER, PORT)
        offline = False
        with pytest.raises(Refusal, match="no other board"):
            await board.address("missing", PORT)
        assert await board.address(PEER, PORT) == BASE
        assert await board.address(PEER, PORT) == BASE
        assert len(calls) == 3

    asyncio.run(run())
