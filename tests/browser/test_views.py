"""Use the search, the waits stacks, the sidebar and the backlog in the live board."""

import re
from typing import TYPE_CHECKING

from playwright.sync_api import expect

from browser.board_ui import RECEIPT, WAIT, box, visit
from browser.chromium import PHONE
from browser.test_keys import panel, seed, wait_mark
from fixtures.board import beside, make
from fixtures.board.moments import NOW
from lem.records.holds import Parked
from lem.records.task import Task
from lem.store import tasks

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page

    from browser.conftest import OpenWindow
    from browser.server import Board

TITLE = "Board card search"
TASK = "board-card-search"
BACKLOG = "the-board-s-done-column-has-no-limit"
QUERY = "#search [data-search-target=query]"


def seeded_search(board: Board) -> None:
    seed(board, TASK, "Search over every card of the board")
    seed(board, "clear-a-reported-deadline", "Clear a reported deadline")
    parked = Task(
        slug="old-export-fix",
        ask="Old export fix",
        status="building",
        opened=NOW,
        since=NOW,
        hold=Parked(since=NOW, words="Wait for the export"),
    )
    tasks.create(board.state, make.record(parked, None, ()))
    backlog_item(board, BACKLOG, "The board's done column has no limit")


def backlog_item(board: Board, slug: str, title: str) -> None:
    beside.write(
        board.checkout / f"docs/backlog/{slug}.md",
        f"---\nworth: later\n---\n\n# {title}\n\nA case in the browser suite.\n",
    )


def query(page: Page, words: str) -> Locator:
    field = page.locator(QUERY)
    field.fill(words)
    return page.locator("#search-list [data-search-target=row]:not([data-js-out])")


def search_open(page: Page, by: str = "Meta+k") -> None:
    page.keyboard.press(by)
    expect(page.locator(QUERY)).to_be_focused()


def test_search_orders_filters_and_opens_the_selected_task(
    board: Board, window: OpenWindow
) -> None:
    seeded_search(board)
    page = window().pages[0]
    visit(page, f"{board.url}/activity")
    search_open(page)
    results = page.locator("#search-list [data-search-target=row]:not([data-js-out])")
    expect(results.first).to_have_attribute("data-js-cur", "")
    expect(results.first).to_have_id("sr-task-gift-note-in-export")
    matches = query(page, "crdsrch")
    expect(matches.first).to_have_id(f"sr-task-{TASK}")
    expect(matches.first).to_have_attribute("data-js-cur", "")
    matches = query(page, "card")
    expect(matches.first).to_contain_text(TITLE)
    expect(matches.nth(1)).to_contain_text("Clear a reported deadline")
    page.keyboard.press("ArrowDown")
    expect(matches.nth(1)).to_have_attribute("data-js-cur", "")
    page.keyboard.press("ArrowUp")
    expect(matches.first).to_have_attribute("data-js-cur", "")
    expect(query(page, "zzzzzzzzzz")).to_have_count(0)
    expect(page.get_by_text("No matches", exact=True)).to_be_visible()
    matches = query(page, "export")
    expect(matches.filter(has_text="Old export fix")).to_be_visible()
    expect(matches.filter(has_text=TITLE)).to_have_count(0)
    matches = query(page, "done col")
    expect(matches.first).to_contain_text("The board's done column has no limit")
    expect(matches.filter(has_text=TITLE)).to_have_count(0)
    query(page, "crdsrch")
    page.keyboard.press("Enter")
    expect(page.locator("#search")).to_be_hidden()
    panel(page, TASK)
    expect(page.locator("#stage")).to_have_class(re.compile(r"\bv-activity\b"))


def test_search_from_the_backlog_or_a_panel_restores_focus(
    board: Board, window: OpenWindow
) -> None:
    page = window().pages[0]
    visit(page, f"{board.url}/backlog")
    page.keyboard.press("/")
    field = page.locator("#bl-query")
    expect(field).to_be_focused()
    for key in ("Meta+k", "Control+k"):
        search_open(page, key)
        query(page, "export")
        page.keyboard.press("Escape")
        expect(field).to_be_focused()
        expect(page.locator(QUERY)).to_have_value("")
    page.locator("[data-search-open]:visible").first.click()
    expect(page.locator(QUERY)).to_be_focused()

    visit(page, board.task(RECEIPT))
    focus = page.locator("#ptab-overview")
    focus.focus()
    search_open(page)
    query(page, "export")
    page.keyboard.press("Escape")
    expect(focus).to_be_focused()
    expect(page.locator(QUERY)).to_have_value("")
    panel(page, RECEIPT)

    phone = window(PHONE, phone=True).pages[0]
    visit(phone, f"{board.url}/backlog")
    phone.locator("[data-search-open]:visible").first.tap()
    expect(phone.locator(QUERY)).to_be_focused()


def test_search_click_opens_a_backlog_item_and_a_refresh_preserves_the_query(
    board: Board,
    window: OpenWindow,
) -> None:
    seeded_search(board)
    page = window().pages[0]
    visit(page, f"{board.url}/activity")
    search_open(page)
    query(page, "done col").first.click()
    expect(page.locator("#search")).to_be_hidden()
    item = page.locator(f"#item-{BACKLOG}")
    expect(page.locator("#stage")).to_have_class(re.compile(r"\bv-backlog\b"))
    expect(item).to_have_attribute("open", "")
    expect(item).to_have_attribute("data-js-cur", "")
    expect(item.locator("summary")).to_be_in_viewport()

    search_open(page)
    query(page, "card")
    chosen = page.locator(f"#sr-task-{TASK}")
    expect(chosen).to_have_attribute("data-js-cur", "")
    seed(board, "a-card-from-the-stream", "A card from the stream")
    added = page.locator("#sr-task-a-card-from-the-stream")
    expect(added).to_be_visible(timeout=WAIT)
    expect(page.locator(QUERY)).to_have_value("card")
    expect(page.locator(QUERY)).to_be_focused()
    expect(chosen).to_have_attribute("data-js-cur", "")


def test_enter_or_a_click_selects_the_waiting_interview_session(
    board: Board,
    window: OpenWindow,
) -> None:
    slug = "interview-keys"
    seed(board, slug, "The interview for the browser case", waits=True)
    session = beside.opened(slug, 0, "shape", "new").session
    page = window().pages[0]
    visit(page, f"{board.url}/waits", "#waits-list")
    row = page.locator(f"article.wrow[data-task='{slug}']")
    verb = row.locator(".wr-verb")
    for action in ("Enter", "Blur", "Click"):
        if action != "Click":
            mark_interview(page, row, blur=action == "Blur")
        with page.expect_response(
            lambda reply: session in reply.url and reply.request.method == "POST"
        ) as selected:
            if action == "Click":
                verb.click()
            else:
                page.keyboard.press("Enter")
        assert selected.value.ok
        expect(page.locator("#panel")).to_have_count(0)
    assert board.terminal.selections == [session] * 3


def mark_interview(page: Page, row: Locator, *, blur: bool) -> None:
    locate = "#waits-list [data-js-cur]"
    target = row.get_attribute("id")
    for _ in range(page.locator("#waits-list article, #waits-list details").count()):
        if (
            page.locator(locate).count()
            and page.locator(locate).get_attribute("id") == target
        ):
            break
        page.keyboard.press("j")
    wait_mark(page, row)
    if blur:
        page.evaluate("document.activeElement.blur()")


def test_waits_stack_opens_both_rows_with_a_click_or_a_tap(
    board: Board, window: OpenWindow
) -> None:
    for phone in (False, True):
        context = window(PHONE, phone=True) if phone else window()
        page = context.pages[0]
        visit(page, f"{board.url}/waits", "#waits-list")
        stack = page.locator(f"#wait-stack-{RECEIPT}")
        summary = stack.locator(":scope > summary")
        rows = stack.locator(":scope > .wst-rows > article")
        expect(summary).to_contain_text("Refund line on receipt")
        expect(summary).to_contain_text("Read the merge review")
        expect(summary).to_contain_text("2 things")
        expect(rows.first).to_be_hidden()
        click = summary.tap if phone else summary.click
        click()
        expect(rows).to_have_count(2)
        for row in rows.all():
            expect(row.locator(".wr-verb")).to_be_visible()
            expect(row.locator(".wr-time")).to_have_text(re.compile(r"\S"))
            expect(row.locator(".wr-time")).to_be_visible()
        expect(rows.last.get_by_role("link", name="Merge…")).to_have_attribute(
            "href", re.compile(r"/merge\?in=waits$")
        )
        click()
        expect(rows.first).to_be_hidden()
        page.close()


def test_sidebar_fold_survives_the_switch_to_the_drawer_and_back(
    board: Board,
    window: OpenWindow,
) -> None:
    page = window((1200, 900)).pages[0]
    visit(page, f"{board.url}/")
    shell = page.locator("#shell")
    fold = page.locator("#side-fold")
    fold.click()
    expect(shell).to_have_class(re.compile(r"\brailed\b"))
    expect(fold).to_have_attribute("title", "Unfold the sidebar")
    page.set_viewport_size({"width": 700, "height": 900})
    page.locator('[data-action="drawer#open"]').click()
    expect(shell).to_have_attribute("data-js-drawer", "")
    expect(fold).to_be_visible()
    fold.click()
    expect(shell).not_to_have_class(re.compile(r"\brailed\b"))
    expect(page.get_by_role("link", name="Backlog", exact=False).first).to_be_visible()
    page.set_viewport_size({"width": 1200, "height": 900})
    expect(fold).to_have_attribute("title", "Fold the sidebar")


def test_backlog_and_other_views_keep_the_key_line_at_the_foot(
    board: Board,
    window: OpenWindow,
) -> None:
    for number in range(20):
        backlog_item(board, f"browser-case-{number:02d}", f"Browser case {number:02d}")
    page = window((1200, 720)).pages[0]
    visit(page, f"{board.url}/backlog", "#backlog")
    keys = page.locator("#backlog-keys")
    status = page.locator("#status")
    _, foot, _, height = box(keys)
    assert abs(foot + height - box(status)[1]) <= 2
    last = page.locator("#bl-groups details.bl-item").last
    expect(last).not_to_be_in_viewport()
    last.scroll_into_view_if_needed()
    expect(last).to_be_in_viewport()
    _, end, _, item_height = box(last)
    assert end + item_height <= foot + 2
    for key, name in (("w", "waits"), ("t", "kanban"), ("a", "activity")):
        page.keyboard.press(key)
        line = page.locator(f"#{name}-keys")
        expect(line).to_be_visible()
        assert abs(box(line)[1] - foot) <= 2


def test_start_from_backlog_reaches_the_new_task_after_the_stream_refresh(
    board: Board,
    window: OpenWindow,
) -> None:
    page = window().pages[0]
    visit(page, f"{board.url}/backlog", "#backlog")
    item = page.locator("#item-invoice-footer-wraps")
    item.locator("summary").click()
    expect(page.locator("#status .st-live")).to_contain_text("live")
    page.evaluate("""document.addEventListener('turbo:before-stream-render', event => {
      if (event.detail.newStream?.action === 'refresh') {
        queueMicrotask(() => { window.heldBacklogRefresh = event.defaultPrevented })
      }
    })""")
    board.terminal.pause = True
    item.get_by_role("button", name="Start a task").click(no_wait_after=True)
    assert board.terminal.requested.wait(5)
    try:
        backlog_item(
            board, "browser-refresh", "This item arrives while the start waits"
        )
        page.wait_for_function("window.heldBacklogRefresh === true", timeout=WAIT)
        expect(page.locator("#item-browser-refresh")).to_have_count(0)
        expect(item).to_have_attribute("open", "")
    finally:
        board.terminal.proceed.set()
    expect(page.locator("#panel")).to_be_visible(timeout=WAIT)
    slug = page.locator("#panel").get_attribute("data-task")
    assert slug
    assert (
        board.record(slug).task.backlog_item == "docs/backlog/invoice-footer-wraps.md"
    )
    assert len(board.terminal.openings) == 1
