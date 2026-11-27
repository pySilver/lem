"""The page of a joined machine's task, relayed by the board of the Mac where the owner reads it,
offers the jump to the task's session at a phone and a desktop width. The jump posts to this
board's own address under the machine's name; the case clicks nothing, so no agterm is asked."""

import os
import re
from typing import TYPE_CHECKING

import httpx
import pytest
from playwright.sync_api import expect

from browser.board_ui import in_screen, visit
from browser.chromium import DESKTOP, PHONE
from contract.agterm_standin import install
from fixtures.board import beside
from fixtures.board.moments import HOST, NOW, WORKSPACE
from lem.addons.peers import registry, table
from lem.board import app, facts, serving, workspaces
from lem.board import install as installed

if TYPE_CHECKING:
    from pathlib import Path

    from playwright.sync_api import Route

    from browser.conftest import OpenWindow
    from browser.server import Board

PEER = "desk"
PEER_PORT = 19057
TASK = "coupon-has-a-slug"
SESSION = beside.session(TASK, 30.5)
STREAM = re.compile(r"/stream(\?.*)?$")


@pytest.fixture
def joined_board(
    board: Board, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Board:
    """The board of this Mac, joined to `desk`, whose board shows the same workspace."""
    desk_home = tmp_path / "desk-home"
    workspaces.changed(desk_home, str(board.checkout), add=True)
    agterm = install(tmp_path / "desk-agterm")
    desk = app.made(
        facts.Facts(
            pid=os.getpid(),
            port=PEER_PORT,
            url=f"http://127.0.0.1:{PEER_PORT}/",
            host=PEER,
            home=str(desk_home),
            install=installed.install_of(),
            started=NOW,
        ),
        serving.Serving(
            home=desk_home,
            environ=agterm.environ(HOME=str(tmp_path)),
            listen="127.0.0.1",
            stop=lambda: None,
        ),
    )
    home = tmp_path / "lem-home"
    table.change(home, PEER, PEER_PORT)

    async def address(host: str, port: int) -> str:
        # The transport stands in for the tailnet: desk answers as its own listener does.
        assert (host, port) == (PEER, PEER_PORT)
        return f"http://127.0.0.1:{PEER_PORT}"

    peers = registry.Registry(
        home=home, own=HOST, address=address, transport=httpx.ASGITransport(app=desk)
    )
    monkeypatch.setattr(registry, "held", lambda request: peers)
    return board


@pytest.mark.parametrize("screen", (PHONE, DESKTOP), ids=("phone", "desktop"))
def test_a_joined_tasks_page_offers_the_jump_to_its_session(
    joined_board: Board, window: OpenWindow, screen: tuple[int, int]
) -> None:
    phone = screen == PHONE
    page = window(screen, phone=phone).pages[0]
    page.clock.set_fixed_time(NOW)
    # The in-process transport holds a relayed stream open until the server stops.
    page.route(STREAM, lambda route: route.abort())
    root = joined_board.url.removesuffix(f"/{HOST}/{WORKSPACE}")
    visit(page, f"{root}/{PEER}/{WORKSPACE}/tasks/{TASK}")
    expect(page.locator("body")).to_have_attribute(
        "data-agterm-url-value", f"/{PEER}/{WORKSPACE}/agterm"
    )
    jumps = page.locator(f'button[data-agterm-session-param="{SESSION}"]')
    expect(jumps.first).to_have_text("Open the session")
    jump = jumps.filter(visible=True).first
    jump.scroll_into_view_if_needed()
    expect(jump).to_be_visible()
    expect(jump).to_be_in_viewport(ratio=1)
    in_screen(jump, screen)


def test_the_jump_takes_no_second_click_while_its_act_runs(
    joined_board: Board, window: OpenWindow
) -> None:
    page = window(DESKTOP).pages[0]
    page.clock.set_fixed_time(NOW)
    page.route(STREAM, lambda route: route.abort())
    # The browser holds the act: it never reaches the board, so no agterm is asked.
    held: list[Route] = []

    def hold(route: Route) -> None:
        # Playwright takes a function of Python's own, not a bound method of a builtin list.
        held.append(route)

    page.route(f"**/{PEER}/{WORKSPACE}/agterm/**", hold)
    root = joined_board.url.removesuffix(f"/{HOST}/{WORKSPACE}")
    visit(page, f"{root}/{PEER}/{WORKSPACE}/tasks/{TASK}")
    jump = page.locator(f'button[data-agterm-session-param="{SESSION}"]')
    jump = jump.filter(visible=True).first
    jump.click()
    expect(jump).to_be_disabled()
    expect(jump).to_have_attribute("aria-disabled", "true")
    jump.click(force=True)
    notice = "Not attached: talk."
    held[0].fulfill(json={"done": True, "said": "Opened.", "notice": notice})
    expect(jump).to_be_enabled()
    expect(page.locator("[data-js-note]").filter(has_text=notice)).to_be_visible()
    assert len(held) == 1
