"""Draw the board's charts and make the pictures of the demo afternoon.

Run
`UPDATE_LEM_SCREENS=1 .venv/bin/python -I -B tests --level browser tests/browser/test_showcase.py`
to write the eight pictures into assets/screens. The normal test writes to its temporary folder.
"""

import os
from itertools import product
from pathlib import Path
from typing import TYPE_CHECKING

from playwright.sync_api import expect

from browser.board_ui import RECEIPT, visit
from browser.chromium import DESKTOP, PHONE
from fixtures.board.moments import NOW

if TYPE_CHECKING:
    from browser.conftest import OpenWindow
    from browser.server import Board

ROOT = Path(__file__).resolve().parents[2]


def dimensions(shot: bytes) -> tuple[int, int]:
    assert shot[:8] == b"\x89PNG\r\n\x1a\n"
    return int.from_bytes(shot[16:20]), int.from_bytes(shot[20:24])


def test_the_demo_afternoon_draws_the_documented_pictures(
    board: Board,
    window: OpenWindow,
    tmp_path: Path,
) -> None:
    screens = (
        ("board", f"{board.url}/", "#kanban", DESKTOP),
        ("task", board.task(RECEIPT), "#merge-review", DESKTOP),
        ("backlog", f"{board.url}/backlog", "#backlog", DESKTOP),
        ("phone", f"{board.url}/", "#kanban", PHONE),
    )
    for dark, size in product((False, True), (DESKTOP, PHONE)):
        context = window(size, phone=size == PHONE, dark=dark, scale=2)
        page = context.pages[0]
        page.clock.set_fixed_time(NOW)
        for name, url, marker, screen in screens:
            if size != screen:
                continue
            visit(page, url, marker)
            page.evaluate("document.fonts.ready")
            theme = "dark" if dark else "light"
            assert page.evaluate(
                "theme => matchMedia('(prefers-color-scheme: ' + theme + ')').matches",
                theme,
            )
            target = tmp_path / f"{name}-{theme}.png"
            shot = page.screenshot(path=target, animations="disabled")
            assert dimensions(shot) == (size[0] * 2, size[1] * 2)
        context.close()
    if os.environ.get("UPDATE_LEM_SCREENS") == "1":
        for shot in sorted(tmp_path.glob("*.png")):
            (ROOT / "assets" / "screens" / shot.name).write_bytes(shot.read_bytes())


def test_the_task_chart_opens_zooms_pans_and_fits_with_the_button_and_zero(
    board: Board,
    window: OpenWindow,
) -> None:
    page = window().pages[0]
    visit(page, board.task(RECEIPT), "#panel")
    chart = page.locator(".chart[data-drawn=done]").first
    expect(chart.locator(".chart-svg svg")).to_be_visible(timeout=15000)
    opener = chart.locator(".chart-open")
    opener.click()
    large = page.locator("#chart-large")
    expect(large).to_be_visible()
    expect(large.locator(".cl-pane svg")).to_be_visible()
    percent = large.locator(".cl-pct")
    fitted = percent.inner_text()
    large.get_by_role("button", name="Larger").click()
    expect(percent).not_to_have_text(fitted)
    pane = large.locator(".cl-pane")
    old = pane.get_attribute("style")
    large.locator(".cl-stage").focus()
    page.keyboard.press("ArrowRight")
    assert pane.get_attribute("style") != old
    page.keyboard.press("0")
    expect(percent).to_have_text(fitted)
    large.get_by_role("button", name="Larger").click()
    expect(percent).not_to_have_text(fitted)
    large.get_by_role("button", name="Fit the window").click()
    expect(percent).to_have_text(fitted)
    large.get_by_role("button", name="Close the chart").click()
    expect(large).to_be_hidden()
    expect(opener).to_be_focused()
