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
from browser.chromium import DESKTOP, PHONE, dimensions
from browser.test_sheets import CONFIRM, GATE, SHORT_PHONE, button, scroll_end, sheet
from fixtures.board.moments import NOW

if TYPE_CHECKING:
    from playwright.sync_api import Page

    from browser.conftest import OpenWindow
    from browser.server import Board

ROOT = Path(__file__).resolve().parents[2]
PUBLISHED = ("board", "task", "backlog", "phone")


def set_scene(page: Page, name: str) -> None:
    if name == "story":
        outcome = page.locator("#building")
        chart = outcome.locator(".chart[data-drawn=done] .chart-svg svg")
        expect(chart).to_be_visible()
        outcome.get_by_text("After:", exact=True).evaluate("""after => {
          const tab = after.closest('.tabbody')
          tab.scrollTop += after.getBoundingClientRect().top - tab.getBoundingClientRect().top - 14
        }""")
        expect(chart).to_be_in_viewport()
    if name in {"phone-merge-off", "phone-merge-on"}:
        found = sheet(page)
        expect(button(found)).to_have_text(GATE)
        expect(button(found)).to_be_disabled()
        if name == "phone-merge-on":
            scroll_end(found)
            expect(button(found)).to_have_text("Approve")
            expect(button(found)).to_be_enabled()


def test_the_demo_afternoon_draws_the_documented_pictures(
    board: Board,
    window: OpenWindow,
    tmp_path: Path,
) -> None:
    task = board.task(RECEIPT)
    waits = f"{board.url}/waits"
    merge = board.task(RECEIPT, "/merge")
    screens = (
        ("board", f"{board.url}/", "#kanban", DESKTOP),
        ("task", task, "#merge-review", DESKTOP),
        ("backlog", f"{board.url}/backlog", "#backlog", DESKTOP),
        ("phone", f"{board.url}/", "#kanban", PHONE),
        ("waits", waits, "#waits-list", DESKTOP),
        ("phone-waits", waits, "#waits-list", PHONE),
        ("story", task, "#building", DESKTOP),
        ("phone-review", task, "#merge-review", PHONE),
        ("phone-merge-off", merge, CONFIRM, SHORT_PHONE),
        ("phone-merge-on", merge, CONFIRM, SHORT_PHONE),
    )
    themes = ("light", "dark")
    for theme, size in product(themes, (DESKTOP, PHONE, SHORT_PHONE)):
        context = window(size, phone=size != DESKTOP, dark=theme == "dark", scale=2)
        page = context.pages[0]
        page.clock.set_fixed_time(NOW)
        for name, url, marker, screen in screens:
            if size != screen:
                continue
            visit(page, url, marker)
            page.evaluate("document.fonts.ready")
            set_scene(page, name)
            assert page.evaluate(
                "theme => matchMedia('(prefers-color-scheme: ' + theme + ')').matches",
                theme,
            )
            target = tmp_path / f"{name}-{theme}.png"
            shot = page.screenshot(path=target, animations="disabled")
            assert dimensions(shot) == (size[0] * 2, size[1] * 2)
        context.close()
    if os.environ.get("UPDATE_LEM_SCREENS") == "1":
        for name, theme in product(PUBLISHED, themes):
            filename = f"{name}-{theme}.png"
            (ROOT / "assets" / "screens" / filename).write_bytes(
                (tmp_path / filename).read_bytes()
            )


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
