"""Navigate cards and waits with the board's keys and live refreshes."""

import re
from typing import TYPE_CHECKING

from msgspec.structs import replace
from playwright.sync_api import expect

from browser.board_ui import (
    CART,
    GIFT,
    RECEIPT,
    ROUNDING,
    STOCK,
    WAIT,
    box,
    posts,
    visit,
)
from browser.chromium import PHONE
from fixtures.board import beside, make
from fixtures.board.moments import NOW
from lem.app.sessions import log
from lem.ports.terminal import Pane
from lem.records.holds import OwnerHold
from lem.records.task import Task
from lem.store import places, tasks

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page

    from browser.conftest import OpenWindow
    from browser.server import Board
    from lem.records.task import Status


def card(page: Page, slug: str) -> Locator:
    return page.locator(f"#card-{slug}")


def marked(page: Page, slug: str, *, focus: bool = True) -> None:
    expect(page.locator("#kanban [data-js-cur]")).to_have_id(f"card-{slug}")
    if focus:
        expect(card(page, slug).locator(".tc-link")).to_be_focused()


def panel(page: Page, slug: str) -> None:
    expect(page.locator("#panel")).to_have_attribute("data-task", slug)


def first_in(page: Page, group: str) -> str:
    slug = page.locator(f"#col-{group} .tc").first.get_attribute("data-task")
    assert slug
    return slug


def move(board: Board, slug: str, status: Status) -> None:
    before = board.record(slug)
    tasks.update(
        board.state,
        slug,
        lambda older: replace(
            older, task=replace(older.task, status=status, since=NOW, hold=None)
        ),
        before.revision,
    )


def seed(board: Board, slug: str, ask: str, *, waits: bool = False) -> None:
    hold = (
        OwnerHold(on="interview", since=NOW, line="The interview waits for the owner")
        if waits
        else None
    )
    task = Task(
        slug=slug,
        ask=ask,
        opened=NOW,
        since=NOW,
        status="shaping" if waits else "building",
        hold=hold,
    )
    tasks.create(board.state, make.record(task, None, ()))
    if waits:
        opened = beside.opened(slug, 0, "shape", "new")
        board.terminal.panes[opened.session] = Pane(id=opened.session, name=slug)
        log.append(places.task_folder(board.state, slug), opened)


def test_task_keys_keep_the_mark_and_focus_together(
    board: Board, window: OpenWindow
) -> None:
    page = window().pages[0]
    visit(page, f"{board.url}/", "#kanban")
    keys = page.locator("#kanban-keys")
    expect(keys).to_have_text(
        "J K ↑ ↓ move · H L ← → column · Enter open · Esc close", use_inner_text=True
    )
    expect(page.locator("#kanban")).to_have_attribute("data-controller", "cursor")
    _, y, _, height = box(keys)
    assert abs(y - box(page.locator("#stage"))[1] - box(page.locator("#stage"))[3]) <= 2
    assert abs(y + height - box(page.locator("#status"))[1]) <= 2
    expect(page.locator("#kanban [data-js-cur]")).to_have_count(0)
    for key, slug in (
        ("j", GIFT),
        ("j", STOCK),
        ("k", GIFT),
        ("ArrowDown", STOCK),
        ("ArrowUp", GIFT),
    ):
        page.keyboard.press(key)
        marked(page, slug)

    phone = window(PHONE, phone=True).pages[0]
    visit(phone, f"{board.url}/", "#kanban")
    expect(phone.locator("#kanban-keys")).to_be_hidden()


def test_horizontal_keys_pass_folded_and_empty_columns(
    board: Board, window: OpenWindow
) -> None:
    page = window().pages[0]
    visit(page, f"{board.url}/", "#kanban")
    for key in ("j", "l", "j"):
        page.keyboard.press(key)
    marked(page, CART)
    fold = page.locator("#col-checks .col-head button")
    fold.click()
    expect(page.locator("#col-checks")).to_have_class(re.compile(r"\bfolded\b"))
    for key in ("l", "h", "ArrowRight", "ArrowLeft"):
        page.keyboard.press(key)
        marked(page, CART if key in {"h", "ArrowLeft"} else "order-date-on-invoice")

    fold.click()
    move(board, "coupon-has-a-slug", "landed")
    expect(page.locator("#col-checks article.tc")).to_have_count(0, timeout=WAIT)
    nearest = page.locator("#col-done article.tc").evaluate_all("""cards => {
      const mid = n => { const b = n.getBoundingClientRect(); return b.top + b.height / 2 }
      const center = mid(document.querySelector('#card-cart-total-after-coupon'))
      return cards.sort((a, b) => Math.abs(mid(a) - center) - Math.abs(mid(b) - center))[0].dataset.task
    }""")
    page.keyboard.press("l")
    marked(page, nearest)
    page.keyboard.press("h")
    marked(page, CART)


def test_enter_escape_arrows_and_clicks_in_the_task_panel(
    board: Board, window: OpenWindow
) -> None:
    page = window().pages[0]
    visit(page, f"{board.url}/", "#kanban")
    page.keyboard.press("j")
    page.keyboard.press("j")
    for blur in (False, True):
        if blur:
            page.evaluate("document.activeElement.blur()")
        page.keyboard.press("Enter")
        panel(page, STOCK)
        page.keyboard.press("Escape")
        expect(page.locator("#panel")).to_have_count(0)
        marked(page, STOCK)

    card(page, ROUNDING).locator(".tc-link").click()
    panel(page, ROUNDING)
    page.keyboard.press("ArrowDown")
    marked(page, ROUNDING, focus=False)
    page.keyboard.press("j")
    marked(page, CART)
    panel(page, ROUNDING)
    page.keyboard.press("Enter")
    panel(page, CART)
    page.keyboard.press("Escape")
    marked(page, CART)

    card(page, ROUNDING).locator(".tc-link").click()
    panel(page, ROUNDING)
    page.keyboard.press("j")
    page.keyboard.press("Escape")
    marked(page, CART)
    page.keyboard.press("Enter")
    panel(page, CART)
    page.keyboard.press("Escape")
    page.locator(f".wi[data-task='{ROUNDING}']").click()
    panel(page, ROUNDING)
    page.keyboard.press("Escape")
    marked(page, ROUNDING)
    page.keyboard.press("Enter")
    panel(page, ROUNDING)


def test_text_fields_modifiers_and_an_empty_kanban_let_the_keys_pass(
    board: Board,
    window: OpenWindow,
) -> None:
    page = window().pages[0]
    visit(page, board.task(GIFT, "/park"), "#confirm")
    page.keyboard.press("j")
    before = page.locator("#kanban [data-js-cur]").get_attribute("id")
    field = page.locator('#confirm input[name="words"]')
    field.focus()
    page.keyboard.press("j")
    expect(field).to_have_value("j")
    field.blur()
    for key in ("Meta+j", "Control+j", "Alt+j", "Control+ArrowDown"):
        page.keyboard.press(key)
        expect(page.locator("#kanban [data-js-cur]")).to_have_id(before or "")
    visit(page, f"{board.url}/", "#kanban")
    expect(page.locator("#kanban [data-js-cur]")).to_have_count(0)
    unfolded = page.locator("#kanban .col:not(.folded) .col-head button")
    while unfolded.count():
        unfolded.first.click()
    expect(page.locator("#kanban .col:not(.folded)")).to_have_count(0)
    page.evaluate(
        "window.addEventListener('keydown', e => window.lastKeyPrevented = e.defaultPrevented)"
    )
    page.keyboard.press("ArrowDown")
    expect(page.locator("#kanban .tc:visible")).to_have_count(0)
    expect(page.locator("#kanban [data-js-cur]")).to_have_count(0)
    assert page.evaluate("window.lastKeyPrevented") is False


def test_refresh_keeps_a_card_mark_until_the_card_moves(
    board: Board, window: OpenWindow
) -> None:
    page = window().pages[0]
    visit(page, f"{board.url}/", "#kanban")
    for key in ("j", "l", "j"):
        page.keyboard.press(key)
    marked(page, CART)
    seed(board, "keys-new-task", "The new card of the browser case")
    expect(page.locator("#col-build #card-keys-new-task")).to_be_visible(timeout=WAIT)
    marked(page, CART)
    move(board, CART, "landing")
    expect(page.locator(f"#col-checks #card-{CART}")).to_be_visible(timeout=WAIT)
    expect(page.locator("#kanban [data-js-cur]")).to_have_count(0)
    page.keyboard.press("j")
    marked(page, first_in(page, "you"))


def wait_mark(page: Page, expected: Locator) -> None:
    identity = expected.get_attribute("id")
    assert identity
    expect(page.locator("#waits-list [data-js-cur]")).to_have_id(identity)
    expect(expected.locator(":scope > summary, .wr-verb").first).to_be_focused()


def test_waits_keys_move_and_open_without_approving_a_merge(
    board: Board, window: OpenWindow
) -> None:
    page = window().pages[0]
    visit(page, f"{board.url}/waits", "#waits-list")
    sent = posts(page)
    expect(page.locator("#waits-keys")).to_have_text(
        "J K ↑ ↓ move · Enter go or open", use_inner_text=True
    )
    expect(page.locator("#waits-list")).to_have_attribute("data-controller", "cursor")
    rows = page.locator("#waits-list > article, #waits-list > details")
    expect(page.locator("#waits-list [data-js-cur]")).to_have_count(0)
    for key, index in (("j", 0), ("j", 1), ("k", 0), ("ArrowDown", 1), ("ArrowUp", 0)):
        page.keyboard.press(key)
        wait_mark(page, rows.nth(index))

    stack = page.locator(f"#wait-stack-{RECEIPT}")
    stack.locator(":scope > summary").click()
    merge = stack.locator(f"#wait-merge-{RECEIPT}")
    for _ in range(rows.count() + stack.locator("article").count()):
        if merge.get_attribute("data-js-cur") is not None:
            break
        page.keyboard.press("j")
    wait_mark(page, merge)
    page.keyboard.press("Enter")
    panel(page, RECEIPT)
    assert not sent
    page.keyboard.press("Escape")
    expect(page.locator("#panel")).to_have_count(0)
    wait_mark(page, merge)


def test_wait_mark_survives_a_new_interview_and_clears_when_the_row_leaves(
    board: Board,
    window: OpenWindow,
) -> None:
    page = window().pages[0]
    visit(page, f"{board.url}/waits", "#waits-list")
    page.keyboard.press("j")
    selected = page.locator("#waits-list [data-js-cur]")
    previous = selected.get_attribute("id")
    slug = selected.get_attribute("data-task")
    assert previous and slug
    seed(
        board, "keys-new-interview", "The new interview of the browser case", waits=True
    )
    expect(
        page.locator("#waits-list article[data-task=keys-new-interview]")
    ).to_be_visible(timeout=WAIT)
    expect(selected).to_have_id(previous)
    move(board, slug, "landed")
    expect(page.locator(f"#{previous}")).to_have_count(0, timeout=WAIT)
    expect(selected).to_have_count(0)
    page.keyboard.press("j")
    wait_mark(page, page.locator("#waits-list > article, #waits-list > details").first)
