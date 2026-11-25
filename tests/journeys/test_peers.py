"""Two disposable board apps share one address through the production peer routes."""

import asyncio
import json
import os
import threading
from http import HTTPStatus
from types import SimpleNamespace
from typing import TYPE_CHECKING

import httpx
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse
from starlette.routing import Route

from fakes.records import record
from lem.addons.peers import registry, requests, routes, rows, table
from lem.board import counts
from lem.board import workspaces as board_workspaces
from lem.board.pages import live, provider, source
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.types import Message

PORT = 19037
BETAS = (rows.Row(name="shop", host="beta", url="/beta/shop/", waits=4),)
ALPHAS = (rows.Row(name="app", host="alpha", url="/alpha/app/", waits=1),)


async def address(host: str, port: int) -> str:
    """Both apps run in process. A transport stands in for the tailnet."""
    assert (host, port) == ("beta", PORT)
    return "http://beta.invalid"


async def page(request: Request) -> Response:
    """Check the relay inputs and render the peer's actual kanban."""
    listed = await routes.spaces(request, BETAS)
    assert [(row.host, row.name) for row in listed] == [
        ("beta", "shop"),
        ("alpha", "app"),
    ]
    assert request.headers[requests.HOP] == "1"
    assert request.headers["Cookie"] == "lem_board=wide"
    return await run_in_threadpool(source.endpoint, request)


async def workspaces(request: Request) -> JSONResponse:
    """The peer's workspace API uses the same add-on as its page."""
    listed = await routes.spaces(request, request.app.state.peer_own_rows(request))
    return JSONResponse(
        [
            {"name": row.name, "host": row.host, "url": row.url, "waits": row.waits}
            for row in listed
        ]
    )


async def asset(request: Request) -> PlainTextResponse:
    return PlainTextResponse("beta asset")


async def redirect(request: Request) -> RedirectResponse:
    return RedirectResponse("/shop/", status_code=HTTPStatus.FOUND)


def board(
    home: Path, host: str, own: tuple[rows.Row, ...], *extras: Route
) -> Starlette:
    app = Starlette(
        routes=[*routes.ROUTES, Route("/api/workspaces", workspaces), *extras]
    )
    app.state.home = home
    app.state.facts = SimpleNamespace(host=host, door=None)
    app.state.peer_own_rows = lambda request: own
    app.state.peer_spaces = routes.spaces
    app.state.act_revision = live.revision
    app.state.page_inputs = provider.inputs
    app.state.environ = os.environ
    app.state.counts = counts.Counts()
    return app


def test_peer_pages_assets_union_and_loop_guard(tmp_path: Path) -> None:
    async def run() -> None:
        alpha_home = tmp_path / "alpha"
        beta_home = tmp_path / "beta"
        table.change(alpha_home, "beta", PORT)
        table.change(beta_home, "gamma", 19038)
        shop = tmp_path / "shop"
        (shop / ".git").mkdir(parents=True)
        tasks.create(shop / ".lem/state", record("repair-export"))
        (shop / ".lem/state/demo").touch()
        (beta_home / board_workspaces.WORKSPACES).write_text(json.dumps([str(shop)]))
        beta = board(
            beta_home,
            "beta",
            BETAS,
            Route("/{host}/{workspace}/", page),
            Route("/beta/assets/test.css", asset),
            Route("/beta/redirect", redirect),
        )
        alpha = board(alpha_home, "alpha", ALPHAS)
        loop_thread = threading.get_ident()

        def own_rows(request: Request) -> tuple[rows.Row, ...]:
            if "peer" in request.path_params:
                assert threading.get_ident() != loop_thread
            return ALPHAS

        alpha.state.peer_own_rows = own_rows
        alpha.state.peer_registry = registry.Registry(
            home=alpha_home,
            own="alpha",
            address=address,
            transport=httpx.ASGITransport(app=beta),
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=alpha), base_url="http://alpha.invalid"
        ) as client:
            listed = await client.get("/api/workspaces")
            assert [(row["host"], row["name"]) for row in listed.json()] == [
                ("beta", "shop"),
                ("alpha", "app"),
            ]
            seen = await client.get(
                "/beta/shop/", headers={"Cookie": "lem_board=wide; another=no"}
            )
            assert "text/html" in seen.headers["content-type"]
            assert 'id="card-repair-export"' in seen.text
            assert "data-agterm-url-value" not in seen.text
            assert 'href="/alpha/app/"' in seen.text
            assert 'href="/beta/shop/new"' not in seen.text
            asset_body = await client.get("/beta/assets/test.css")
            assert asset_body.text == "beta asset"
            assert (await client.head("/beta/assets/test.css")).content == b""
            assert (await client.get("/beta/redirect")).headers[
                "location"
            ] == "/beta/shop/"
            assert (await client.post("/beta/shop/")).status_code == 405
            assert (await client.post("/beta/shop/agterm/type")).status_code == 405
            assert (
                await client.get("/beta/shop/", headers={"Lem-Hop": "1"})
            ).status_code == 404
            hopped = await client.get("/api/workspaces", headers={"Lem-Hop": "1"})
            assert [row["host"] for row in hopped.json()] == ["alpha"]
            assert not hasattr(beta.state, "peer_registry")

    asyncio.run(run())


class Events(httpx.AsyncByteStream):
    """One upstream SSE event, then a silent connection until the client leaves."""

    def __init__(self) -> None:
        self.closed = asyncio.Event()

    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield b"event: refresh\ndata: 2\n\n"
        await asyncio.Future()

    async def aclose(self) -> None:
        self.closed.set()


def test_relay_closes_a_silent_peer_stream_at_disconnect(tmp_path: Path) -> None:
    async def run() -> None:
        home = tmp_path / "alpha"
        table.change(home, "beta", PORT)
        alpha = board(home, "alpha", ALPHAS)
        events = Events()
        ready = asyncio.Event()

        def respond(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/api/workspaces":
                return httpx.Response(
                    200, json=[{"name": "shop", "url": "/beta/shop/"}]
                )
            assert request.url.path == "/beta/shop/stream"
            return httpx.Response(
                200, headers={"Content-Type": "text/event-stream"}, stream=events
            )

        alpha.state.peer_registry = registry.Registry(
            home=home,
            own="alpha",
            address=address,
            transport=httpx.MockTransport(respond),
        )

        async def receive() -> Message:
            await ready.wait()
            return {"type": "http.disconnect"}

        async def send(message: Message) -> None:
            if b"event: refresh" in message.get("body", b""):
                ready.set()

        await asyncio.wait_for(
            alpha(
                {
                    "type": "http",
                    "asgi": {"version": "3.0", "spec_version": "2.4"},
                    "method": "GET",
                    "path": "/beta/shop/stream",
                    "root_path": "",
                    "query_string": b"",
                    "headers": [],
                    "scheme": "http",
                },
                receive,
                send,
            ),
            timeout=3,
        )
        assert ready.is_set() and events.closed.is_set()

    asyncio.run(run())


def test_join_survives_no_answer_and_the_entry_retains_a_peers_last_rows(
    tmp_path: Path,
) -> None:
    from lem.addons.peers import commands, look, tailnet

    async def run() -> None:
        home = tmp_path / "alpha"
        beta = board(tmp_path / "beta", "beta", BETAS)
        sleeping = True
        wire: list[str] = []

        async def upstream(request: httpx.Request) -> httpx.Response:
            wire.append(request.url.path)
            assert request.headers["Lem-Hop"] == "1"
            if sleeping:
                raise httpx.ConnectTimeout("the peer did not answer", request=request)
            if request.url.path == "/api/server":
                return httpx.Response(
                    200, json={"host": "beta", "install": {"version": "scratch"}}
                )
            return await httpx.ASGITransport(app=beta).handle_async_request(request)

        transport = httpx.MockTransport(upstream)
        space = tailnet.Status(
            own=tailnet.Machine(dns="alpha.test.invalid"),
            suffix="test.invalid",
            peers={"beta": tailnet.Machine(dns="beta.test.invalid")},
        )
        async with httpx.AsyncClient(transport=transport) as client:
            joined = await commands.join(f"beta:{PORT}", space, client, home)
        assert not joined.reachable and wire == ["/api/server"]
        assert table.read(home) == {"beta": PORT}

        sleeping = False
        alpha = board(home, "alpha", ALPHAS)
        cached = registry.Registry(
            home=home, own="alpha", address=address, transport=transport
        )
        alpha.state.peer_registry = cached
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=alpha), base_url="http://alpha.invalid"
        ) as client:
            listed = (await client.get("/api/workspaces")).json()
            assert listed[0]["name"] == "shop"
            stored = cached.known["beta"].seen
            assert stored.reachable and stored.answered is not None
            sleeping = True
            response = await client.get("/beta/shop/")
            assert (
                response.status_code == 502 and "beta is not reachable" in response.text
            )
            gray = cached.known["beta"].shown()[0]
            assert gray.answered == stored.answered and gray.reachable is False
            assert gray.name == "shop" and gray.waits is None
            counts = wire.count("/api/workspaces")
            assert cached.known["beta"].tried > float("-inf")
            assert (await client.get("/api/workspaces")).json()[1]["name"] == "shop"
            assert wire.count("/api/workspaces") == counts
            assert look.WORKSPACES_PATH in wire

    asyncio.run(run())
