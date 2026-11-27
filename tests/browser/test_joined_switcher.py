"""Read the current machine in the sidebar at phone and desktop widths."""

import os
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import pytest
from playwright.sync_api import expect

from browser.board_ui import in_screen, visit
from browser.chromium import DESKTOP, PHONE
from fixtures.board.moments import HOST, NOW, WORKSPACE
from lem.addons.peers import registry, routes, table

if TYPE_CHECKING:
    from browser.conftest import OpenWindow
    from browser.server import Board

PEER = "desk"


@pytest.fixture
def joined_board(
    board: Board, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Board:
    home = tmp_path / "lem-home"
    table.change(home, PEER, 19037)

    async def address(host: str, port: int) -> str:
        return f"https://{host}.test.invalid:{port}"

    def answer(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/workspaces"
        return httpx.Response(200, json=[{"name": WORKSPACE}])

    peers = registry.Registry(
        home=home, own=HOST, address=address, transport=httpx.MockTransport(answer)
    )
    monkeypatch.setattr(routes, "peers", lambda request: peers)
    return board


@pytest.mark.parametrize("screen", (PHONE, DESKTOP), ids=("phone", "desktop"))
@pytest.mark.parametrize("theme", ("light", "dark"))
def test_the_switcher_names_the_current_machine(
    joined_board: Board, window: OpenWindow, screen: tuple[int, int], theme: str
) -> None:
    phone = screen == PHONE
    page = window(screen, phone=phone, dark=theme == "dark", scale=2).pages[0]
    page.clock.set_fixed_time(NOW)
    visit(page, f"{joined_board.url}/")
    expect(page.locator("html")).to_have_attribute("data-palette", theme)
    expect(page).to_have_title(
        f"DEMO · Tasks · Lem · {HOST}/{WORKSPACE} · 2 build · 5 for you"
    )
    if phone:
        page.get_by_role("button", name="Open the menu").click()

    summary = page.locator("#ws-switcher summary")
    host = summary.get_by_text(HOST, exact=True)
    expect(summary.get_by_text(WORKSPACE, exact=True)).to_be_visible()
    expect(host).to_be_in_viewport(ratio=1)
    expect(host).to_have_css("font-size", "13px")
    in_screen(host, screen)

    brand = page.locator("#side .brand")
    machine = brand.get_by_text(HOST, exact=True)
    expect(brand.get_by_text("Lem", exact=True)).to_be_visible()
    expect(brand.get_by_text(WORKSPACE, exact=True)).to_be_visible()
    expect(machine).to_be_in_viewport(ratio=1)
    expect(machine).to_have_css(
        "color", host.evaluate("host => getComputedStyle(host).color")
    )
    in_screen(machine, screen)

    if phone and (screens := os.environ.get("JOIN_WORDS_SCREENSHOTS")):
        page.screenshot(
            path=Path(screens) / f"join-words-phone-{theme}.png", animations="disabled"
        )

    summary.click()
    menu = page.locator("#ws-switcher .ws-menu")
    for machine in (HOST, PEER):
        entry = menu.locator(f'a[href="/{machine}/{WORKSPACE}/"]')
        expect(entry.get_by_text(machine, exact=True)).to_be_visible()
        expect(entry.get_by_text(WORKSPACE, exact=True)).to_be_visible()
