"""Read the board's confirmation sheets and check what their native forms submit."""

import re
from typing import TYPE_CHECKING
from urllib.parse import parse_qs

from msgspec.structs import replace
from playwright.sync_api import expect

from browser.board_ui import GIFT, RECEIPT, STOCK, WAIT, box, in_screen, posts, visit
from browser.chromium import PHONE
from fakes.repo import RealRepo, git_env, run_git
from fixtures.board.moments import NOW, sha
from lem.adapters.git_cli import GitCli
from lem.app.landing import world
from lem.app.tasks import where
from lem.board.duties import context, forge
from lem.board.duties.memory import MEMORY
from lem.model.landing.checks import inputs
from lem.ports.forge_facts import Pull
from lem.records.journal.task import OwnerAct
from lem.store import places, tasks

if TYPE_CHECKING:
    import pytest
    from playwright.sync_api import Locator, Page

    from browser.conftest import OpenWindow
    from browser.server import Board
    from lem.records.landing.propose import Proposed

SHORT_PHONE = (390, 664)
SMALL_PHONE = (390, 400)
# Design part 8 gives the browser level three minutes. On main, a proposal
# took over 15 seconds to arrive under load (confirm_checks, 2026-11-23).
STREAM_WAIT = 180_000
CONFIRM = "#confirm"
APPROVAL = "#approve-criteria"
GATE = "Read to the end ↓"


def sheet(page: Page, selector: str = CONFIRM) -> Locator:
    found = page.locator(selector)
    expect(found).to_have_attribute("data-js-sheet", "")
    return found


def button(sheet: Locator) -> Locator:
    return sheet.locator(".cf-foot button[type=submit]").first


def merge_url(board: Board) -> str:
    return board.task(RECEIPT, "/merge?in=waits")


def approved_tip(board: Board) -> Proposed:
    found = board.record(RECEIPT).landing
    assert found is not None and found.proposed is not None
    return found.proposed


def repropose(board: Board, word: str, reasons: int, *, green: bool = False) -> str:
    old = board.record(RECEIPT)
    landing = old.landing
    assert landing is not None and landing.proposed is not None
    proposal = replace(
        landing.proposed,
        tip=sha(word),
        reasons=landing.proposed.reasons[:reasons],
        green=green,
    )
    tasks.update(
        board.state,
        RECEIPT,
        lambda record: replace(
            record,
            landing=replace(
                landing,
                proposed=proposal,
                pushed=proposal.tip,
                reviews=() if green else landing.reviews,
            ),
        ),
        old.revision,
    )
    return proposal.tip


def scroll_end(found: Locator) -> None:
    found.locator(".cf-body").evaluate("body => { body.scrollTop = body.scrollHeight }")


def gated(found: Locator, page: Page, label: str) -> None:
    expect(found).to_have_css("position", "fixed")
    expect(found.locator(".cf-head")).to_be_focused()
    tap_while_gated(found, page)
    scroll_end(found)
    expect(button(found)).to_have_text(label)
    expect(button(found)).to_be_enabled()


def tap_while_gated(found: Locator, page: Page) -> None:
    control = button(found)
    expect(control).to_have_text(GATE)
    expect(control).to_be_disabled()
    sent = posts(page)
    # The element remains a native submit button. Tap its center even while ARIA says off.
    left, top, width, height = box(control)
    page.touchscreen.tap(left + width / 2, top + height / 2)
    expect(control).to_have_text(GATE)
    assert not sent


def below_text(found: Locator) -> None:
    body = found.locator(".cf-body")
    text_end = body.locator(":scope > :visible").last
    assert box(text_end)[1] + box(text_end)[3] <= box(button(found))[1]


def no_fixed_parts(found: Locator) -> None:
    assert found.evaluate("""sheet => ![sheet, ...sheet.querySelectorAll('*')]
        .some(node => ['fixed', 'sticky'].includes(getComputedStyle(node).position))""")


def test_merge_sheet_on_the_phone_has_its_heading_reasons_facts_and_actions(
    board: Board,
    window: OpenWindow,
) -> None:
    old = board.record(RECEIPT)
    landing = old.landing
    assert landing is not None and landing.proposed is not None
    reason = "The total under the refund is money the customer pays."
    reviewed = replace(landing.reviews[-1], careful=True, careful_why=reason)
    proposed = replace(landing.proposed, careful=True)
    shown_landing = replace(
        landing, proposed=proposed, reviews=(*landing.reviews[:-1], reviewed)
    )
    tasks.update(
        board.state,
        RECEIPT,
        lambda record: replace(record, landing=shown_landing),
        old.revision,
    )
    page = window(PHONE, phone=True).pages[0]
    visit(page, merge_url(board), CONFIRM)
    shown = sheet(page)
    expect(shown).to_have_css("position", "fixed")
    head = shown.locator(".cf-head")
    expect(head.get_by_text("Merge #44 · confirm")).to_be_visible()
    expect(head).to_be_focused()
    body = shown.locator(".cf-body")
    parts = body.locator(":scope > *").all_text_contents()
    assert parts[0].lstrip().startswith("Not green")
    assert "Decision 1" in parts[2]
    assert f"Careful: {reason}" in parts[3]
    assert "A merge cannot be undone" in parts[-1]
    expect(body.locator(".cf-facts dt")).to_have_text(
        ["Pull request", "Commit", "Branch", "Into", "Lands as"]
    )
    for part in (
        head,
        button(shown),
        shown.get_by_role("link", name="Back", exact=True),
    ):
        in_screen(part, PHONE)


def test_merge_approval_requires_a_read_to_the_end_and_resets_after_a_new_proposal(
    board: Board,
    window: OpenWindow,
) -> None:
    page = window(SHORT_PHONE, phone=True).pages[0]
    visit(page, merge_url(board), CONFIRM)
    shown = sheet(page)
    body = shown.locator(".cf-body")
    assert body.evaluate("body => body.scrollHeight > body.clientHeight")
    gated(shown, page, "Approve")
    for mark, reasons in (
        ("new tip in the same pull request", 4),
        ("a shorter proposal", 3),
    ):
        tip = repropose(board, mark, reasons)
        expect(shown.locator("#fact-commit code")).to_have_text(
            tip[:12], timeout=STREAM_WAIT
        )
        assert body.evaluate("body => body.scrollTop") == 0
        assert body.evaluate("body => body.scrollHeight > body.clientHeight")
        tap_while_gated(shown, page)
        if reasons == 4:
            body.evaluate(
                "body => { body.scrollTop = body.scrollHeight - body.clientHeight - 12 }"
            )
            assert body.evaluate("body => body.scrollTop") > 0
            expect(button(shown)).to_have_text(GATE)
    scroll_end(shown)
    expect(button(shown)).to_be_enabled()


def test_a_short_green_merge_is_ready_at_once_on_a_phone(
    board: Board, window: OpenWindow
) -> None:
    repropose(board, "a short green pull request", 0, green=True)
    page = window(PHONE, phone=True).pages[0]
    visit(page, merge_url(board), CONFIRM)
    shown = sheet(page)
    expect(shown).to_have_css("position", "fixed")
    expect(shown.locator(".cf-verdict")).to_contain_text("Green")
    assert shown.locator(".cf-body").evaluate(
        "body => body.scrollHeight <= body.clientHeight"
    )
    expect(button(shown)).to_have_text("Approve")
    expect(button(shown)).to_be_enabled()


def test_merge_on_a_desktop_has_a_button_below_the_text(
    board: Board, window: OpenWindow
) -> None:
    page = window().pages[0]
    visit(page, merge_url(board), CONFIRM)
    shown = sheet(page)
    no_fixed_parts(shown)
    below_text(shown)
    expect(button(shown)).to_have_text("Approve")
    expect(button(shown)).to_be_enabled()
    expect(shown.get_by_role("link", name="Back", exact=True)).to_be_visible()


def mergeable_receipt(board: Board) -> str:
    """Give the demo proposal a local worktree and a pull request the fake forge can merge."""
    checkout = board.checkout
    origin = checkout.parent / "origin.git"
    run_git(checkout, "init", "--quiet", "--bare", str(origin))
    run_git(checkout, "remote", "add", "origin", str(origin))
    run_git(checkout, "push", "--quiet", "origin", "main")
    before = board.record(RECEIPT)
    landing, branch = before.landing, before.task.branch
    assert landing and landing.pull and landing.checked and landing.proposed and branch
    workspace = places.workspace(checkout)
    worktree = where.worktree(workspace, RECEIPT)
    run_git(checkout, "worktree", "add", "--quiet", "-b", branch, str(worktree), "main")
    (worktree / "receipt.txt").write_text("Show the refund\n", encoding="utf-8")
    run_git(worktree, "add", "receipt.txt")
    run_git(worktree, "commit", "--quiet", "-m", "Show the refund")
    run_git(worktree, "push", "--quiet", "origin", branch)
    tip = run_git(worktree, "rev-parse", "HEAD")
    base = run_git(checkout, "rev-parse", "main")
    checked = replace(
        landing.checked,
        tip=tip,
        tree=run_git(worktree, "rev-parse", "HEAD^{tree}"),
        base=base,
        inputs=inputs(world.rules(workspace)),
    )
    proposed = replace(landing.proposed, tip=tip, base=base)
    tasks.update(
        board.state,
        RECEIPT,
        lambda record: replace(
            record,
            landing=replace(landing, proposed=proposed, pushed=tip, checked=checked),
        ),
        before.revision,
    )
    board.forge.remote = RealRepo(origin, checkout, worktree, "main")
    pull = landing.pull
    board.forge.pulls[pull.number] = Pull(
        number=pull.number,
        url=pull.url,
        title=pull.title,
        state="open",
        head=tip,
        head_ref=branch,
        base="main",
        mergeable="mergeable",
    )
    return tip


def test_native_merge_form_submits_the_tip_and_the_board_records_the_approval(
    board: Board,
    window: OpenWindow,
) -> None:
    tip = mergeable_receipt(board)
    page = window(PHONE, phone=True, scripts=False).pages[0]
    url = merge_url(board)
    visit(page, url, CONFIRM, scripts=False)
    shown = page.locator(CONFIRM)
    expect(shown).not_to_have_attribute("data-js-sheet", "")
    no_fixed_parts(shown)
    below_text(shown)
    expect(shown.locator("#fact-commit code")).to_have_text(tip[:12])
    with page.expect_request(lambda request: request.method == "POST") as submit:
        button(shown).tap()
    request = submit.value
    assert request.url == url.partition("?")[0]
    assert parse_qs(request.post_data or "") == {
        "confirm": ["yes"],
        "tip": [tip],
        "in": ["waits"],
    }
    expect(page.locator("#panel")).to_be_visible(timeout=WAIT)
    expect(page).to_have_url(re.compile(r"[?&]note="))
    worker = MEMORY.of(board.checkout).merging[RECEIPT]
    worker.join(timeout=10)
    assert not worker.is_alive()
    page.reload()
    note = page.locator("#panel .act-note").first
    expect(note).to_contain_text("Merged: pull request #44 is on main.")
    assert board.forge.merge_calls == [(44, tip)]
    assert board.forge.pull(44).state == "merged"
    assert any(
        isinstance(entry, OwnerAct) and entry.act == "merge" and entry.option == tip
        for entry in board.record(RECEIPT).journal
    )


def test_the_phone_folds_the_header_and_the_board_rejects_stale_merge_state(
    board: Board,
    window: OpenWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    phone = window(PHONE, phone=True).pages[0]
    visit(phone, board.task(RECEIPT), "#panel")
    head = phone.locator("#p-head")
    expect(head.locator(".p-fold")).to_have_attribute("aria-expanded", "false")
    expect(head.locator("#p-more")).to_be_hidden()
    head.locator(".p-fold").tap()
    expect(head.locator("#p-more")).to_be_visible()

    native = window(PHONE, phone=True, scripts=False).pages[0]
    visit(native, merge_url(board), CONFIRM, scripts=False)
    before = board.record(RECEIPT)
    repropose(board, "the tip moved before the owner's click", 4)
    button(native.locator(CONFIRM)).tap()
    expect(native.locator("#panel .act-note").first).to_contain_text(
        "The branch was proposed again"
    )
    assert board.record(RECEIPT).journal == before.journal

    landing = before.landing
    assert landing is not None and landing.pull is not None and before.task.branch
    pull = landing.pull
    board.forge.pulls[pull.number] = Pull(
        number=pull.number,
        url=pull.url,
        title=pull.title,
        state="closed",
        head=approved_tip(board).tip,
        head_ref=before.task.branch,
        base="main",
    )
    place = places.workspace(board.checkout)
    duty = context.Duty(
        name=board.checkout.name,
        here=context.bound(place, git_env(), board.checkout.parent / "lem-home"),
        now=NOW,
        kept=MEMORY.of(board.checkout),
    )
    origin = board.checkout.parent / "origin.git"
    run_git(board.checkout, "init", "--quiet", "--bare", str(origin))
    run_git(board.checkout, "remote", "add", "origin", str(origin))
    run_git(board.checkout, "push", "--quiet", "origin", "main")
    monkeypatch.setattr(
        GitCli, "origin_url", lambda *_: "https://github.com/acme/shop.git"
    )
    forge.tick(duty)
    assert board.record(RECEIPT).task.status == "dropped", duty.kept.problems
    expect(phone.locator("#p-head .pill")).to_contain_text("Dropped", timeout=WAIT)
    expect(phone.locator("#p-head .p-acts a").filter(has_text="Merge")).to_have_count(0)
    assert not board.forge.merge_calls


def test_park_and_criteria_sheets_wait_for_a_read_when_the_screen_is_short(
    board: Board,
    window: OpenWindow,
) -> None:
    page = window(SMALL_PHONE, phone=True).pages[0]
    for slug, tail, selector, title, label in (
        (GIFT, "/park", CONFIRM, "Park · breaker 1", "Park the task"),
        (STOCK, "/criteria", APPROVAL, "The criteria wait for your yes", "Yes"),
    ):
        visit(page, board.task(slug, tail), selector)
        found = sheet(page, selector)
        expect(found.locator(".cf-head")).to_contain_text(title)
        assert found.locator(".cf-body").evaluate(
            "body => body.scrollHeight > body.clientHeight"
        )
        gated(found, page, label)


def test_park_and_criteria_fit_a_tall_phone_and_stay_inline_on_desktop(
    board: Board,
    window: OpenWindow,
) -> None:
    for screen in (PHONE, (1440, 900)):
        phone = screen == PHONE
        page = window(screen, phone=phone).pages[0]
        for slug, tail, selector, label in (
            (GIFT, "/park", CONFIRM, "Park the task"),
            (STOCK, "/criteria", APPROVAL, "Yes"),
        ):
            visit(page, board.task(slug, tail), selector)
            found = sheet(page, selector)
            expect(button(found)).to_have_text(label)
            expect(button(found)).to_be_enabled()
            back = found.get_by_role(
                "link", name="Back", exact=True, include_hidden=True
            )
            if phone:
                expect(found).to_have_css("position", "fixed")
                in_screen(button(found), screen)
                in_screen(back, screen)
                if slug == STOCK:
                    in_screen(
                        found.get_by_role("button", name="No", exact=True), screen
                    )
            else:
                no_fixed_parts(found)
                below_text(found)
                if slug == STOCK:
                    expect(back).to_be_hidden()


def test_changed_criteria_stack_on_a_phone_and_sit_side_by_side_on_desktop(
    board: Board,
    window: OpenWindow,
) -> None:
    for screen in (PHONE, (1440, 900)):
        phone = screen == PHONE
        page = window(screen, phone=phone).pages[0]
        visit(page, board.task(STOCK, "/criteria"), APPROVAL)
        found = sheet(page, APPROVAL)
        pairs = found.locator(".cf-pair.cf-changed > section")
        expect(pairs.get_by_role("heading", level=3)).to_have_text(
            ["Before · criterion 1", "Now · criterion 1"]
        )
        expect(pairs.first).to_contain_text('says "3 left"')
        expect(pairs.last).to_contain_text('says "Only 1 left"')
        x1, y1, w1, h1 = box(pairs.first)
        x2, y2, w2, _ = box(pairs.last)
        if phone:
            assert abs(x1 - x2) <= 1
            assert y2 >= y1 + h1 - 1
        else:
            assert abs(y1 - y2) <= 1
            assert x2 >= x1 + w1 - 1
        assert x1 >= 0 and x2 + w2 <= screen[0] + 1
        assert found.locator(".cf-body").evaluate(
            "body => body.scrollWidth <= body.clientWidth + 1"
        )


def test_no_on_criteria_requires_a_note_and_records_no_answer(
    board: Board, window: OpenWindow
) -> None:
    page = window(PHONE, phone=True).pages[0]
    visit(page, board.task(STOCK, "/criteria"), APPROVAL)
    found = sheet(page, APPROVAL)
    scroll_end(found)
    before = board.record(STOCK)
    found.get_by_role("button", name="No", exact=True).tap()
    expect(page.locator("#panel .act-note").first).to_contain_text(
        "No needs your words: what the criteria should say."
    )
    assert board.record(STOCK) == before


def test_native_park_and_criteria_forms_send_the_question_and_record_the_answer(
    board: Board,
    window: OpenWindow,
) -> None:
    page = window(PHONE, phone=True, scripts=False).pages[0]
    for slug, tail, selector, choice in (
        (STOCK, "/criteria", APPROVAL, "yes"),
        (GIFT, "/park", CONFIRM, "park"),
    ):
        visit(page, board.task(slug, tail), selector, scripts=False)
        found = page.locator(selector)
        expect(found).not_to_have_attribute("data-js-sheet", "")
        no_fixed_parts(found)
        below_text(found)
        if slug == STOCK:
            expect(found.locator("noscript pre")).to_contain_text(
                "## Acceptance criteria"
            )
        with page.expect_request(lambda request: request.method == "POST") as saved:
            button(found).tap()
        submit = saved.value
        assert submit.url == board.task(slug, "/answer")
        form = parse_qs(submit.post_data or "")
        assert form["option"] == [choice]
        assert form["key"][0] in {
            asked.id for asked in board.record(slug).task.questions
        }
        if slug == STOCK:
            assert form["digest"]
        expect(page).to_have_url(re.compile(r"[?&]note="))
        assert any(
            asked.answer and asked.answer.option == choice
            for asked in board.record(slug).task.questions
        )


def test_breaker_drop_opens_a_confirm_sheet_and_carries_the_note(
    board: Board, window: OpenWindow
) -> None:
    page = window(PHONE, phone=True).pages[0]
    visit(page, f"{board.url}/waits", "#waits-list")
    breaker = page.locator(f"article.wrow[data-task='{GIFT}']")
    fields = breaker.locator(".answer-form")
    for text in ("Help", "Park…", "Drop…"):
        expect(fields.get_by_role("button", name=text, exact=True)).to_be_visible()
    note = "Wait for the next export"
    fields.locator('[name="words"]').fill(note)
    sent = posts(page)
    fields.get_by_role("button", name="Drop…").tap()
    drop = sheet(page)
    expect(drop.locator(".cf-head")).to_contain_text(f"Drop {GIFT}?")
    expect(drop.locator('[name="words"]')).to_have_value(note)
    expect(button(drop)).to_have_text("Confirm")
    assert not sent
