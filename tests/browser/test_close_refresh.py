"""Keep the phone's page, forms and waits in step with the board's stream."""

import re
import time
from threading import Event
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlsplit

import pytest
from msgspec.structs import replace
from playwright.sync_api import expect

from browser.board_ui import GIFT, RECEIPT, STREAM_WAIT, WAIT, visit
from browser.chromium import DESKTOP, PHONE
from browser.test_keys import card, panel, seed
from browser.test_sheets import CONFIRM, button, mergeable_receipt, scroll_end
from fakes.repo import run_git
from fixtures.board import beside
from lem.board.counts import FRESH
from lem.board.duties.memory import MEMORY
from lem.store import places, tasks

if TYPE_CHECKING:
    from playwright.sync_api import Page, Route

    from browser.conftest import OpenWindow
    from browser.server import Board
    from lem.ports.forge_facts import MergeMethod, MergeOutcome, MergeText


def count_on(page: Page) -> int:
    return int(page.locator(".m-waits span").inner_text())


def counts(page: Page, count: int) -> None:
    page.wait_for_function(
        """count => document.querySelector('.m-waits span')?.textContent === count
                  && document.querySelector('#side .side-head em')?.textContent === count""",
        arg=str(count),
        timeout=STREAM_WAIT,
    )


def watch_counts(page: Page) -> None:
    """Sample both badges together after every mutation through the approval."""
    page.evaluate("""() => {
      const pair = () => [
        document.querySelector('.m-waits span')?.textContent,
        document.querySelector('#side .side-head em')?.textContent
      ];
      window.waitPairs = [pair()];
      new MutationObserver(() => window.waitPairs.push(pair())).observe(
        document.documentElement,
        { subtree: true, childList: true, characterData: true, attributes: true }
      );
    }""")


def server_count(page: Page, board: Board) -> int:
    """Read the workspace's waits count from the API."""
    url = urljoin(board.url, "/api/workspaces")
    path = str(board.checkout)
    reply = page.request.get(url, timeout=STREAM_WAIT)
    assert reply.ok, f"{url}: HTTP {reply.status}"
    [row] = [row for row in reply.json() if row.get("path") == path]
    return int(row["waits"])


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
    original = server_count(phone, board)
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
    watch_counts(phone)
    button(shown).tap()
    expect(phone.locator("#panel .act-note").first).to_contain_text(
        re.compile("base moved" if moved else "Merged:", re.IGNORECASE), timeout=WAIT
    )
    worker = MEMORY.of(board.checkout).merging.get(RECEIPT)
    if worker is not None:
        worker.join(timeout=10)
        assert not worker.is_alive()
    assert board.forge.merge_calls == ([] if moved else [(44, tip)])
    time.sleep(FRESH)
    final = server_count(phone, board)
    counts(phone, final)
    pairs = phone.evaluate("window.waitPairs")
    changed = [
        pair
        for index, pair in enumerate(pairs)
        if index == 0 or pair != pairs[index - 1]
    ]
    expected = [[str(count)] * 2 for count in dict.fromkeys((original, final))]
    assert changed == expected, (
        f"API counts: {original}, {final}. Badge pairs: {changed}"
    )
    phone.reload()
    counts(phone, final)


def held_merge(board: Board) -> Event:
    """Hold the forge's merge call until the case releases it, as GitHub takes its time."""
    release = Event()
    merge = board.forge.merge

    def held(
        number: int, expected_head: str, method: MergeMethod, text: MergeText
    ) -> MergeOutcome:
        assert release.wait(STREAM_WAIT / 1000), "the case did not release the merge"
        return merge(number, expected_head, method, text)

    board.forge.merge = held
    return release


def empty_bad_gateway(route: Route) -> None:
    """What the tailnet door answers while the board server behind it is gone."""
    route.fulfill(status=502, body="")


@pytest.mark.parametrize("phone", (True, False), ids=("phone", "desktop"))
def test_an_approval_shows_its_merge_and_a_lost_server_never_blanks_the_page(
    board: Board, window: OpenWindow, *, phone: bool
) -> None:
    tip = mergeable_receipt(board)
    merge_read_for_tip(board)
    release = held_merge(board)
    page = window(PHONE if phone else DESKTOP, phone=phone).pages[0]
    visit(page, board.task(RECEIPT), "#panel")
    live(page)
    if phone:
        page.locator(".p-fold").tap()
    page.locator("#p-head .p-acts a").filter(has_text="Merge").click()
    shown = page.locator(CONFIRM)
    expect(shown).to_be_visible()
    scroll_end(shown)
    expect(button(shown)).to_have_text("Approve")
    button(shown).click()
    note = page.locator("#panel .act-note").first
    expect(note).to_contain_text("Lem merges", timeout=WAIT)
    assert "note=" in page.url
    address = page.url
    page.evaluate("window.stillHere = true")
    release.set()
    expect(note).to_contain_text("Merged:", timeout=STREAM_WAIT)
    assert board.forge.merge_calls == [(44, tip)]
    task_path = urlsplit(address).path
    page.route(lambda url: urlsplit(url).path == task_path, empty_bad_gateway)
    seed(board, "a-wait-while-the-server-is-gone", "A new interview", waits=True)
    expect(page.locator("#status .st-live")).to_have_text("reconnecting", timeout=WAIT)
    assert page.url == address
    assert page.evaluate("[window.stillHere, Boolean(document.body.textContent)]") == [
        True,
        True,
    ]
    expect(note).to_contain_text("Merged:")
    page.unroute_all()
    live(page)
    expect(page.locator("#side .side-head em")).to_have_text(
        str(server_count(page, board)), timeout=STREAM_WAIT
    )
    assert page.evaluate("window.stillHere") is True
