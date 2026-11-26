"""Keep the phone's page, forms and waits in step with the board's stream."""

import re
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import pytest
from msgspec.structs import replace
from playwright.sync_api import expect

from browser.board_ui import GIFT, RECEIPT, STREAM_WAIT, WAIT, visit
from browser.chromium import PHONE
from browser.test_keys import card, panel, seed
from browser.test_sheets import CONFIRM, button, mergeable_receipt, scroll_end
from fakes.repo import run_git
from fixtures.board import beside
from lem.board.duties.memory import MEMORY
from lem.store import places, tasks

if TYPE_CHECKING:
    from playwright.sync_api import Page

    from browser.conftest import OpenWindow
    from browser.server import Board


def count_on(page: Page) -> int:
    return int(page.locator(".m-waits span").inner_text())


def counts(page: Page, count: int) -> None:
    expect(page.locator(".m-waits span")).to_have_text(str(count), timeout=STREAM_WAIT)
    expect(page.locator("#side .side-head em")).to_have_text(str(count))


def live(page: Page) -> None:
    expect(page.locator("#status .st-live")).to_contain_text("live", timeout=WAIT)


def merge_read_for_tip(board: Board) -> None:
    record = board.record(RECEIPT)
    landing = record.landing
    assert landing and landing.proposed and landing.checked
    [read] = landing.reads
    tree = run_git(board.checkout, "rev-parse", "main^{tree}")
    read = replace(
        read, tip=landing.proposed.tip, base=landing.proposed.base, base_tree=tree
    )
    checked = replace(landing.checked, base_tree=tree)
    tasks.update(
        board.state,
        RECEIPT,
        lambda record: replace(
            record, landing=replace(landing, reads=(read,), checked=checked)
        ),
        record.revision,
    )


def test_an_open_phone_panel_and_both_badges_survive_a_stream_refresh(
    board: Board, window: OpenWindow
) -> None:
    phone = window(PHONE, phone=True).pages[0]
    visit(phone, f"{board.url}/", "#kanban")
    before = count_on(phone)
    card(phone, GIFT).locator(".tc-link").tap()
    panel(phone, GIFT)
    live(phone)
    seed(board, "a-phone-wait", "A new interview", waits=True)
    counts(phone, before + 1)
    panel(phone, GIFT)
    expect(phone.locator("#ptab-overview")).to_have_attribute("aria-current", "page")


@pytest.mark.parametrize(
    ("tail", "form"),
    (("/new", "#new-task"), (f"/tasks/{GIFT}/park", CONFIRM)),
    ids=("new-task", "park"),
)
def test_a_phone_refresh_keeps_the_words_and_focus(
    board: Board, window: OpenWindow, tail: str, form: str
) -> None:
    phone = window(PHONE, phone=True).pages[0]
    visit(phone, board.url + tail, form)
    live(phone)
    before = count_on(phone)
    words = phone.locator(f'{form} [name="words"]').filter(visible=True)
    words.tap()
    words.fill("Keep my draft through the refresh")
    seed(board, "a-wait-while-i-type", "A new interview", waits=True)
    counts(phone, before + 1)
    expect(words).to_have_value("Keep my draft through the refresh")
    expect(words).to_be_focused()


def test_back_from_criteria_restores_the_overview_then_counts_the_new_file(
    board: Board, window: OpenWindow
) -> None:
    phone = window(PHONE, phone=True).pages[0]
    overview = board.task(GIFT)
    visit(phone, overview, "#panel")
    artifacts = phone.locator("#ptab-artifacts em")
    count = int(artifacts.inner_text())
    phone.locator("#ptab-criteria").tap()
    expect(phone.locator("#ptab-criteria")).to_have_attribute("aria-current", "page")
    phone.evaluate("""() => {
      document.addEventListener('turbo:visit', event => {
        if (event.detail.action !== 'restore') return
        document.addEventListener('turbo:load', () => {
          window.restoredCount = document.querySelector('#ptab-artifacts em')?.textContent
        }, { once: true })
      })
    }""")
    folder = places.task_folder(board.state, GIFT)
    before = board.record(GIFT)
    beside.write(folder / "bench-notes.md", "A file with no journal entry.\n")
    expect(artifacts).to_have_text(str(count + 1), timeout=STREAM_WAIT)
    # Observe the restored snapshot before the stream's refresh can replace it.
    phone.go_back()
    phone.wait_for_url(lambda url: urlsplit(url).path == urlsplit(overview).path)
    expect(phone.locator("#ptab-overview")).to_have_attribute("aria-current", "page")
    assert phone.evaluate("window.restoredCount") == str(count)
    expect(artifacts).to_have_text(str(count + 1), timeout=STREAM_WAIT)
    assert board.record(GIFT) == before


def test_a_silent_open_stream_reconnects_and_catches_up_both_phone_badges(
    board: Board, window: OpenWindow
) -> None:
    phone = window(PHONE, phone=True).pages[0]
    visit(phone, f"{board.url}/", "#kanban")
    live(phone)
    before = count_on(phone)
    board.stream_silent.set()
    reconnect = re.compile(r"/stream(?:\?|$)")
    phone.route("**/api/server", lambda route: route.abort())
    phone.route(reconnect, lambda route: route.abort())
    seed(board, "a-wait-while-disconnected", "A new interview", waits=True)
    expect(phone.locator("#status .st-live")).to_have_text(
        "reconnecting", timeout=30_000
    )
    assert count_on(phone) == before
    board.stream_silent.clear()
    phone.unroute("**/api/server")
    phone.unroute(reconnect)
    live(phone)
    counts(phone, before + 1)


@pytest.mark.parametrize("moved", (False, True), ids=("merged", "moved-base"))
def test_a_phone_approval_and_the_next_page_agree_on_both_wait_counts(
    board: Board, window: OpenWindow, *, moved: bool
) -> None:
    tip = mergeable_receipt(board)
    merge_read_for_tip(board)
    phone = window(PHONE, phone=True).pages[0]
    visit(phone, board.task(RECEIPT), "#panel")
    original = count_on(phone)
    counts(phone, original)
    phone.locator(".p-fold").tap()
    phone.locator("#p-head .p-acts a").filter(has_text="Merge").tap()
    shown = phone.locator(CONFIRM)
    expect(shown).to_be_visible()
    if moved:
        beside.write(board.checkout / "notes.md", "A change on the base.\n")
        run_git(board.checkout, "add", "notes.md")
        run_git(board.checkout, "commit", "-m", "Move the base")
        run_git(board.checkout, "push", "origin", "main")
    scroll_end(shown)
    expect(button(shown)).to_have_text("Approve")
    button(shown).tap()
    expect(phone.locator("#panel .act-note").first).to_contain_text(
        re.compile("base moved" if moved else "Merged:", re.IGNORECASE), timeout=WAIT
    )
    worker = MEMORY.of(board.checkout).merging.get(RECEIPT)
    if worker is not None:
        worker.join(timeout=10)
        assert not worker.is_alive()
    assert board.forge.merge_calls == ([] if moved else [(44, tip)])
    counts(phone, original - 1)
    phone.reload()
    counts(phone, original - 1)
