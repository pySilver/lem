"""Read and answer the actual question pages delivered by the board."""

import re
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace
from playwright.sync_api import expect

from browser.board_ui import ROUNDING, STREAM_WAIT, in_screen, posts, visit
from browser.chromium import DESKTOP, PHONE
from browser.test_close_refresh import count_on, counts, live, server_count
from browser.test_keys import seed
from fixtures.board.working import CARD, CARD_PROMPT
from lem.app import wiring
from lem.app.asking import form, keys, receipts, saved
from lem.app.asking import live as live_session
from lem.app.asking.overlay_read import PageOutcome
from lem.app.sessions import log
from lem.board.ask import live_card
from lem.cli.ask import catalog, html, preferences, spec
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from playwright.sync_api import Page

    from browser.conftest import OpenWindow
    from browser.server import Board
    from lem.cli.ask.spec import Spec
    from lem.records.questions import Answer

TEMPLATES = (
    "architecture",
    "checklist",
    "confirm",
    "design-tokens",
    "layouts",
    "pick",
    "stats",
    "text",
    "tradeoffs",
    "tune",
)
READY = ".hd-foot"
SUCCESS = "The owner’s answer is on record"


@pytest.fixture
def cards(board: Board, monkeypatch: pytest.MonkeyPatch) -> Board:
    """The recorded agent holds its overlay without an earlier answer at the Mac."""
    monkeypatch.setattr(live_session, "bound", wiring.bound)
    monkeypatch.setattr(live_card, "outcome", lambda *_: PageOutcome(kind="pending"))
    session = log.newest_open(log.read(folder(board)))
    assert session is not None
    board.terminal.grounds[session.session] = ("claude",)
    return board


def folder(board: Board) -> Path:
    return places.task_folder(board.state, ROUNDING)


def kept(board: Board, page: str, asked: Spec, base: Path) -> bytes:
    task = folder(board)
    session = log.newest_open(log.read(task))
    assert session is not None
    preferences.apply(asked, preferences.defaults())
    rendered = html.build(asked, base)
    saved.keep(task, form.metadata(asked, page, session.session), rendered)
    return rendered


def template(board: Board, name: str) -> tuple[str, bytes, Spec]:
    path = catalog.folder("templates") / f"{name}.json"
    asked, base = spec.load(str(path))
    page = f"browser-{name}"
    return page, kept(board, page, asked, base), asked


def open_card(page: Page, board: Board, key: str) -> None:
    visit(page, board.task(ROUNDING, f"/cards/{key}/"), READY, scripts=False)


def show_rounding(board: Board) -> None:
    before = board.record(ROUNDING)
    tasks.update(
        board.state,
        ROUNDING,
        lambda older: replace(
            older,
            task=replace(
                older.task,
                questions=tuple(
                    asked
                    for asked in older.task.questions
                    if not (
                        asked.topic == "card" and asked.id.rsplit(":", 1)[-1] == CARD
                    )
                ),
            ),
        ),
        before.revision,
    )
    asked: Spec = {
        "prompt": CARD_PROMPT,
        "options": [
            {"id": "line", "label": "Each line"},
            {"id": "total", "label": "Only the total"},
        ],
    }
    kept(board, CARD, asked, board.checkout)


def answer(board: Board, page: str) -> Answer:
    question = saved.question(folder(board), page)
    assert question is not None and question.answer is not None
    return question.answer


def check_rounding_answer(board: Board, note: str) -> None:
    recorded = answer(board, CARD)
    assert (recorded.label, recorded.note, recorded.device, recorded.source) == (
        "Only the total",
        note,
        "phone",
        "board",
    )
    found = receipts.read(keys.copies(folder(board), CARD), recorded.at)
    assert isinstance(found["answers"], dict)
    assert found["answers"]["answer"]["selected"] == ["total"]


def test_waits_opens_the_phone_card_and_records_only_an_option_with_its_note(
    cards: Board,
    window: OpenWindow,
) -> None:
    show_rounding(cards)
    page = window(PHONE, phone=True).pages[0]
    visit(page, f"{cards.url}/waits", "#waits-list")
    page.evaluate("window.waitsPage = true")
    row = page.locator(f"#wait-card-{CARD}")
    expect(row).to_contain_text(CARD_PROMPT)
    row.locator(".wr-verb").tap()
    iframe = page.locator("#card-step iframe")
    expect(iframe).to_be_visible()
    in_screen(iframe, PHONE)
    card = iframe.content_frame
    expect(card.get_by_text("Each line", exact=True)).to_be_visible()
    expect(card.get_by_text("Only the total", exact=True)).to_be_visible()
    expect(card.locator(".hd-keys")).to_be_hidden()
    expect(
        card.get_by_role("button", name="Discuss in chat", include_hidden=True)
    ).to_have_count(0)
    field = card.locator(".hd-q.cur textarea")
    review = card.locator(".hd-review.cur")
    review_title = review.get_by_text("Review your answers", exact=True)
    review_button = card.get_by_role("button", name="Review", exact=True)
    send = card.get_by_role("button", name="Send answers", exact=True)
    sent = posts(page)
    field.fill("why not both?")
    review_button.tap()
    expect(review_title).to_be_visible()
    expect(review.locator(".hd-note")).to_have_text("why not both?")
    assert not sent
    with page.expect_response(lambda reply: reply.request.method == "POST") as rejected:
        send.tap()
    assert rejected.value.status == 422
    expect(card.locator(".hd-status")).to_contain_text("task’s session")
    asked = saved.question(folder(cards), CARD)
    assert asked is not None and asked.answer is None
    expect(row).to_have_count(1)

    review.locator(".hd-ritem").get_by_text("Edit", exact=True).tap()
    expect(review).to_have_count(0)
    note = "as the receipts do"
    field.fill(note)
    card.get_by_text("Only the total", exact=True).tap()
    review_button.tap()
    expect(review_title).to_be_visible()
    expect(review.locator(".hd-chip")).to_have_text("Only the total")
    expect(review.locator(".hd-note")).to_have_text(note)
    assert len(sent) == 1
    with page.expect_response(lambda reply: reply.request.method == "POST") as accepted:
        send.tap()
    assert accepted.value.ok
    expect(card.locator(".hd-done")).to_contain_text(SUCCESS)
    check_rounding_answer(cards, note)
    expect(row).to_have_count(0, timeout=STREAM_WAIT)
    assert page.evaluate("window.waitsPage") is True


# Counts each load of a card's frame, the first one too, in the page's own window.
FRAME_LOADS = """() => {
  window.cardLoads = 0
  document.addEventListener('load', event => {
    if (event.target.localName === 'iframe') window.cardLoads++
  }, true)
}"""


@pytest.mark.parametrize("phone", (True, False), ids=("phone", "desktop"))
def test_an_open_card_keeps_the_choice_and_the_note_through_refreshes(
    cards: Board, window: OpenWindow, *, phone: bool
) -> None:
    show_rounding(cards)
    page = window(PHONE if phone else DESKTOP, phone=phone).pages[0]
    visit(page, f"{cards.url}/waits", "#waits-list")
    live(page)
    page.evaluate(FRAME_LOADS)
    row = page.locator(f"#wait-card-{CARD} .wr-verb")
    if phone:
        row.tap()
    else:
        row.click()
    card = page.locator("#card-step iframe").content_frame
    option = card.locator(".hd-q.cur .hd-opt").filter(has_text="Only the total")
    option.locator(".hd-label").click()
    expect(option).to_have_class(re.compile(r"\bon\b"))
    field = card.locator(".hd-q.cur textarea")
    field.fill("For the export")
    field.focus()
    before = count_on(page)
    for step in range(3):
        seed(cards, f"a-wait-while-i-answer-{step}", "A new interview", waits=True)
        counts(page, before + step + 1)
    assert page.evaluate("window.cardLoads") == 1
    expect(option).to_have_class(re.compile(r"\bon\b"))
    expect(field).to_have_value("For the export")
    expect(field).to_be_focused()


def opened_card(board: Board, window: OpenWindow, *, phone: bool) -> Page:
    """A board with the rounding card open in its task's frame, from its row of what waits."""
    page = window(PHONE if phone else DESKTOP, phone=phone).pages[0]
    visit(page, f"{board.url}/waits", "#waits-list")
    live(page)
    page.locator(f"#wait-card-{CARD} .wr-verb").click()
    expect(page.locator("#card-step iframe")).to_be_visible()
    return page


@pytest.mark.parametrize(
    "phone", (True, False), ids=("phone-answers", "desktop-answers")
)
def test_an_answer_on_one_board_replaces_the_open_card_on_the_other(
    cards: Board, window: OpenWindow, *, phone: bool
) -> None:
    show_rounding(cards)
    here = opened_card(cards, window, phone=phone)
    there = opened_card(cards, window, phone=not phone)
    card = here.locator("#card-step iframe").content_frame
    card.locator(".hd-q.cur .hd-opt").filter(has_text="Only the total").locator(
        ".hd-label"
    ).click()
    card.locator(".hd-q.cur textarea").fill("For the export")
    send = card.locator(".hd-foot button.primary")
    send.click()
    expect(card.locator(".hd-review.cur")).to_be_visible()
    send.click()
    expect(card.locator(".hd-done")).to_contain_text(SUCCESS)
    recorded = answer(cards, CARD)
    assert (recorded.label, recorded.note, recorded.source) == (
        "Only the total",
        "For the export",
        "board",
    )
    taken = "Only the total was taken on the board"
    expect(there.locator("#card-step")).to_contain_text(taken, timeout=STREAM_WAIT)
    expect(there.locator("#card-step iframe")).to_have_count(0)
    # The answering board's own refresh after the answer may still be on its way.
    before = server_count(here, cards)
    counts(here, before)
    seed(cards, "a-wait-after-the-answer", "A new interview", waits=True)
    counts(here, before + 1)
    expect(card.locator(".hd-done")).to_contain_text(SUCCESS)
    expect(here.locator("#card-step")).not_to_contain_text(taken)


def test_the_board_that_took_the_answer_closes_the_card(
    cards: Board, window: OpenWindow
) -> None:
    show_rounding(cards)
    here = opened_card(cards, window, phone=False)
    card = here.locator("#card-step iframe").content_frame
    card.locator(".hd-q.cur .hd-opt").filter(has_text="Only the total").locator(
        ".hd-label"
    ).click()
    card.locator(".hd-q.cur textarea").fill("For the export")
    send = card.locator(".hd-foot button.primary")
    send.click()
    expect(card.locator(".hd-review.cur")).to_be_visible()
    send.click()
    expect(card.locator(".hd-done")).to_contain_text(SUCCESS)
    assert answer(cards, CARD).source == "board"
    expect(here.locator("#card-step iframe")).to_have_count(0, timeout=STREAM_WAIT)


def test_the_line_after_an_answer_has_a_background_of_its_own(
    cards: Board, window: OpenWindow
) -> None:
    page_id, _, _ = template(cards, "tune")
    page = window(DESKTOP, phone=False).pages[0]
    open_card(page, cards, page_id)
    page.locator(".hd-label").filter(has_text="Soft").click()
    page.locator(".hd-foot button.primary").click()
    done = page.locator(".hd-done")
    expect(done).to_contain_text(SUCCESS)
    drawn = done.evaluate("line => getComputedStyle(line).backgroundColor")
    assert drawn not in {"rgba(0, 0, 0, 0)", "transparent"}, drawn


def test_tune_records_the_slider_value_and_the_preset_it_started_from(
    cards: Board,
    window: OpenWindow,
) -> None:
    page_id, _, _ = template(cards, "tune")
    page = window(PHONE, phone=True).pages[0]
    open_card(page, cards, page_id)
    page.locator(".hd-label").filter(has_text="Soft").tap()
    slider = page.get_by_role("slider").first
    slider.fill("20")
    expect(page.locator(".hd-ctl-v").first).to_have_text("20px")
    expect(page.locator(".hd-opt.on")).to_have_count(0)
    page.locator(".hd-foot button.primary").tap()
    expect(page.locator(".hd-done")).to_contain_text(SUCCESS)
    recorded = answer(cards, page_id)
    assert (recorded.device, recorded.source) == ("phone", "board")
    found = receipts.read(keys.copies(folder(cards), page_id), recorded.at)
    assert isinstance(found["answers"], dict)
    picked = found["answers"]["answer"]
    assert picked["values"]["radius"] == 20
    assert picked["values"]["gap"] == 16
    assert picked["selected"] == []
    assert picked["from"] == "soft"


LAYOUT = """() => {
  const screen = document.documentElement.clientWidth
  const shown = n => n.getClientRects().length && getComputedStyle(n).visibility !== 'hidden'
  const elements = [...document.querySelectorAll('.hd *')].filter(shown)
  const sideScroll = n => {
    for (let up = n.parentElement; up; up = up.parentElement) {
      if (['auto', 'scroll'].includes(getComputedStyle(up).overflowX)) return true
    }
    return false
  }
  const over = elements.filter(n => {
    if ((n.ownerSVGElement && n.tagName.toLowerCase() !== 'svg') || sideScroll(n)) return false
    const bounds = n.getBoundingClientRect()
    return bounds.right > screen + 0.5 || bounds.left < -0.5
  })
  const clipped = elements.filter(n => (
    (['hidden', 'clip'].includes(getComputedStyle(n).overflowX) || n.matches('.hd-code')) &&
    n.scrollWidth > n.clientWidth + 1
  ))
  const fonts = [...document.querySelectorAll('.hd-q.cur svg')].filter(svg => (
    shown(svg) && !svg.closest('.hd-prev') && svg.viewBox.baseVal.width
  )).flatMap(svg => {
    const scale = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width
    return [...svg.querySelectorAll('text, foreignObject span, foreignObject p')]
      .filter(n => n.textContent.trim() && shown(n))
      .map(n => scale * parseFloat(getComputedStyle(n).fontSize))
  })
  const describe = n => n.tagName + '.' + (n.getAttribute('class') || '')
  return {wide: document.documentElement.scrollWidth > screen, over: over.map(describe),
          clipped: clipped.map(describe), fonts}
}"""

TAPS = """.hd-q.cur .hd-opt:visible, .hd-q.cur .hd-toggle:visible,
.hd-q.cur .hd-ctl input:visible, .hd-q.cur .hd-seg button:visible,
.hd-q.cur .hd-ctl-r:visible, .hd-q.cur textarea:visible, .hd-q.cur .hd-replay:visible,
.hd-tab:visible, .hd-foot .hd-btn:visible"""


def check_layout(page: Page) -> None:
    page.wait_for_function("""[...document.querySelectorAll('.hd-q.cur .hd-mermaid')]
      .every(block => block.querySelector('svg') || block.classList.contains('err'))""")
    expect(page.locator(".hd-q.cur .hd-mermaid.err")).to_have_count(0)
    measured = page.evaluate(LAYOUT)
    assert not measured["wide"] and not measured["over"] and not measured["clipped"], (
        measured
    )
    assert all(round(font, 1) >= 10 for font in measured["fonts"]), measured
    expect(
        page.locator(".hd-keys:visible, .hd-tabkey:visible, .hd-btn kbd:visible")
    ).to_have_count(0)
    expect(page.get_by_role("button", name="Discuss in chat")).to_have_count(0)
    controls = page.locator(TAPS)
    assert controls.count()
    for control in controls.all():
        info = control.evaluate("""async n => {
          n.scrollIntoView({block: 'center', inline: 'center', behavior: 'instant'})
          await new Promise(requestAnimationFrame)
          const {left, top, width, height} = n.getBoundingClientRect()
          const target = document.elementFromPoint(left + width / 2, top + height / 2)
          return [Math.round(width), Math.round(height), !!target && (n.contains(target) || target.contains(n)),
                  n.className, target?.className]
        }""")
        assert info[0] >= 24 and info[1] >= 24 and info[2], info


def tap_options(page: Page, question: Spec) -> None:
    choices = page.locator(".hd-q.cur .hd-opts > .hd-opt")
    options = question.get("options", [])
    assert isinstance(options, list)
    labels = [
        option if isinstance(option, str) else option.get("label") or option["id"]
        for option in options
    ]
    expect(choices).to_have_count(len(labels))
    assert (
        choices.locator(".hd-label").evaluate_all("""nodes => nodes.map(node => {
      const label = node.cloneNode(true)
      label.querySelectorAll('.hd-key, .hd-badge, .hd-tag').forEach(part => part.remove())
      return label.textContent.trim()
    })""")
        == labels
    )
    for option in choices.all():
        label = option.locator(".hd-label")
        if "on" in (option.get_attribute("class") or "").split():
            label.tap()
            if "on" in (option.get_attribute("class") or "").split():
                continue
        label.tap()
        expect(option).to_have_class(re.compile(r"\bon\b"))
        if option.evaluate("n => !!n.closest('.hd-q.multi')"):
            label.tap()


def test_every_shipped_card_layout_fits_the_phone_and_the_file_keeps_desktop_keys(
    board: Board,
    window: OpenWindow,
    tmp_path: Path,
    subtests: pytest.Subtests,
) -> None:
    assert (
        tuple(path.stem for path in sorted(catalog.folder("templates").glob("*.json")))
        == TEMPLATES
    )
    phone = window(PHONE, phone=True).pages[0]
    for name in TEMPLATES:
        with subtests.test(card=name):
            page_id, rendered, asked = template(board, name)
            open_card(phone, board, page_id)
            tabs = phone.locator(".hd-tab")
            questions = asked.get("questions", [asked])
            assert isinstance(questions, list)
            has_tabs = len(questions) > 1
            expect(tabs).to_have_count(len(questions) if has_tabs else 0)
            if has_tabs:
                expect(tabs.locator(".h")).to_have_text(
                    [q.get("header") or q["prompt"] for q in questions]
                )
            for index, question in enumerate(questions):
                if has_tabs:
                    tabs.nth(index).tap()
                    expect(tabs.nth(index)).to_have_class(re.compile(r"\bcur\b"))
                expect(phone.locator(".hd-q.cur .hd-prompt")).to_have_text(
                    question["prompt"]
                )
                check_layout(phone)
                tap_options(phone, question)
            if name == "pick":
                pick = tmp_path / "pick.html"
                pick.write_bytes(rendered)
                desktop = window().pages[0]
                desktop.goto(pick.as_uri())
                expect(desktop.locator(".hd-keys")).to_be_visible()
                expect(
                    desktop.get_by_role("button", name="Discuss in chat")
                ).to_be_visible()
