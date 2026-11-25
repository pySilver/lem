"""The afternoon's pages as typed inputs: each decodes back from its JSON whole and strictly, and
each fact it prints agrees with the records it is made from, so that a view made to give these
inputs from these records draws today's board."""

import hashlib
import re
from typing import TYPE_CHECKING

import msgspec
import pytest

from fixtures.board import columns, frame, panel, shelves, waiting
from fixtures.board.beside import BACKLOG, RECORDS, REVIEWED, lay
from fixtures.board.held import STOCK, STOCK_BEFORE
from fixtures.board.moments import BASE
from lem.app.criteria.stopped import unmoved
from lem.app.criteria.where import Here
from lem.board.inputs.backlog import Backlog
from lem.board.inputs.page import Frame
from lem.board.inputs.parts import Document
from lem.board.inputs.task.head import Fact
from lem.board.inputs.task.panel import Panel
from lem.board.inputs.tasks import Tasks
from lem.board.inputs.waits import Waits
from lem.model.criteria import digest
from lem.model.criteria.read import sheet_of
from lem.records.decisions import Taken
from lem.records.holds import BreakerHold, OwnerHold, Parked
from lem.records.record import Record
from lem.store import places

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from lem.board.inputs.task.steps import Merge

BY_SLUG = {each.task.slug: each for each in RECORDS}
RECEIPT = BY_SLUG["refund-line-on-receipt"]
EXPECTED: tuple[tuple[str, msgspec.Struct], ...] = (
    ("frame", frame.FRAME),
    ("tasks", columns.TASKS),
    ("waits", waiting.WAITS),
    ("backlog", shelves.BACKLOG),
    ("overview", panel.OPEN),
    ("criteria", panel.CRITERIA_TAB),
    ("checks", panel.CHECKS_TAB),
    ("merge", panel.MERGE_STEP),
)


@pytest.mark.parametrize(
    ("name", "expected"), EXPECTED, ids=[name for name, _ in EXPECTED]
)
def test_each_page_of_the_afternoon_decodes_back_from_its_json_whole(
    name: str, expected: msgspec.Struct
) -> None:
    encoded = msgspec.json.encode(expected)
    assert msgspec.json.decode(encoded, type=type(expected)) == expected, name


def walk(value: object) -> Iterator[object]:
    """`value` and every struct and tuple inside it."""
    yield value
    if isinstance(value, msgspec.Struct):
        for field in value.__struct_fields__:
            yield from walk(getattr(value, field))
    elif isinstance(value, tuple):
        for each in value:
            yield from walk(each)


def documents() -> list[Document]:
    """Every markdown text the afternoon's pages render."""
    return [
        found
        for _, expected in EXPECTED
        for found in walk(expected)
        if isinstance(found, Document)
    ]


@pytest.mark.parametrize("document", documents(), ids=lambda document: document.id)
def test_a_documents_id_is_its_key_and_the_digest_of_its_key_and_text(
    document: Document,
) -> None:
    key, _, digest = document.id.removeprefix("md-").rpartition("-")
    assert digest == hashlib.sha256(f"{key}|{document.text}".encode()).hexdigest()[:12]


def test_every_task_a_page_opens_is_a_record_of_the_afternoon() -> None:
    hrefs = {
        found
        for _, expected in EXPECTED
        for found in walk(expected)
        if isinstance(found, str) and found.startswith(f"{BASE}/tasks/")
    }
    named = {
        href.removeprefix(f"{BASE}/tasks/").split("/")[0].split("?")[0]
        for href in hrefs
    }
    assert named == set(BY_SLUG)


def test_the_columns_hold_every_task_but_the_parked_each_in_its_status() -> None:
    cards = [card for column in columns.TASKS.columns for card in column.cards]
    parked = {
        slug for slug, each in BY_SLUG.items() if isinstance(each.task.hold, Parked)
    }
    assert {card.slug for card in cards} == set(BY_SLUG) - parked
    for card in cards:
        assert card.status == BY_SLUG[card.slug].task.status, card.slug


def test_a_card_counts_from_its_hold_when_the_owner_holds_it_else_from_its_state() -> (
    None
):
    for column in columns.TASKS.columns:
        for card in column.cards:
            task = BY_SLUG[card.slug].task
            held = isinstance(task.hold, OwnerHold | BreakerHold)
            assert card.since.at == (
                task.hold.since if held and task.hold else task.since
            )
            assert card.since.ticks == ("ago" if column.key == "done" else "since")


def test_each_pull_request_a_card_links_is_its_landings() -> None:
    for column in columns.TASKS.columns:
        for card in column.cards:
            linked = [chip.link.href for chip in card.chips if chip.link]
            landing = BY_SLUG[card.slug].landing
            pull = landing.pull if landing else None
            assert linked == ([pull.url] if pull else []), card.slug


def test_what_waits_answers_the_records_open_questions_and_the_parked_are_their_holds() -> (
    None
):
    gift = waiting.BREAKER
    assert gift.acts and gift.acts.answer
    key = next(field.shown for field in gift.acts.answer.fields if field.name == "key")
    question = next(
        q for q in BY_SLUG["gift-note-in-export"].task.questions if q.id == key
    )
    assert (question.answer, question.options) == (None, ("help", "park", "drop"))
    stock = BY_SLUG["stock-on-product-page"].task
    waiting_now = [q.id for q in stock.questions if q.answer is None]
    assert waiting_now == ["criterion:stock-on-product-page:20261125T155200Z"]
    assert waiting.CRITERIA.id == f"wait-{waiting_now[0].replace(':', '-')}"
    for parked in waiting.WAITS.parked:
        hold = BY_SLUG[parked.slug].task.hold
        assert isinstance(hold, Parked)
        assert parked.since.at == hold.since
        assert parked.resume == f"/lem resume {parked.slug}"
    assert len(waiting.WAITS.parked) == 2


def test_the_sidebar_counts_what_waits_and_the_search_finds_every_task_once() -> None:
    sidebar = frame.FRAME.sidebar
    assert sidebar.waits_count == len(sidebar.waits) == len(waiting.WAITS.stacks)
    things = sum(len(stack.waits) for stack in waiting.WAITS.stacks)
    assert (
        sidebar.waits_title == f"{things} things you do, in {len(sidebar.waits)} tasks"
    )
    found = [row.key for row in frame.FRAME.search.rows if row.kind == "task"]
    assert sorted(found) == sorted(BY_SLUG)


def test_the_workspace_switcher_uses_the_saved_tasks_pages_fallback() -> None:
    assert frame.FRAME.sidebar.switcher.title == "shop"


def test_the_open_criteria_question_accepts_the_file_shown_to_the_owner(
    tmp_path: Path,
) -> None:
    here = Here(workspace=places.workspace(lay(tmp_path)), slug=STOCK.task.slug)
    raw = here.sheet.read_bytes()
    unmoved(here, STOCK, raw, here.sheet)
    question = next(each for each in STOCK.task.questions if each.answer is None)
    assert question.digest == digest.shown(raw)
    sheet = STOCK.task.criteria
    assert sheet.size and sheet.change
    assert sheet.digest == digest.of_tests(sheet.size, sheet.criteria)
    assert (
        sheet.change.before
        == sheet.reads[0].digest
        == digest.of_texts(
            sheet.size,
            sheet_of(sheet.change.text, "the criteria before the note").criteria,
        )
    )
    assert STOCK.task.questions[0].digest == digest.shown(sheet.change.text.encode())
    assert sheet.change.before == digest.of_texts(sheet.size, STOCK_BEFORE)
    assert sheet.change.after == digest.of_texts(sheet.size, sheet.criteria)


def test_the_status_bar_counts_every_entry_of_the_afternoons_journals() -> None:
    entries = sum(len(each.journal) for each in RECORDS)
    assert entries == frame.ENTRIES
    assert frame.FRAME.statusbar.events == f"{entries} entries"


def test_the_backlog_shows_every_item_and_the_task_that_holds_one() -> None:
    paths = {name for name, _ in BACKLOG} | {
        f".lem/state/backlog/{name}" for name, _ in REVIEWED
    }
    entries = [entry for shelf in shelves.BACKLOG.shelves for entry in shelf.entries]
    assert {entry.path for entry in entries} == paths
    assert shelves.BACKLOG.every.count == len(entries)
    held = [entry for entry in entries if entry.holds.held_by]
    holders = [each.task for each in RECORDS if each.task.backlog_item]
    assert [entry.path for entry in held] == [task.backlog_item for task in holders]


def test_the_backlog_starts_a_task_at_the_workspace_tasks_route() -> None:
    item = shelves.FOOTER_ITEM
    form = item.holds.start
    assert form
    assert (form.action, [(field.name, field.shown) for field in form.fields]) == (
        f"{BASE}/tasks",
        [("item", item.path)],
    )


def test_only_the_documents_with_charts_request_the_chart_library() -> None:
    building = panel.OVERVIEW.building
    decision = panel.CRITERIA.decisions[0]
    criterion = panel.CRITERIA.criteria[0]
    assert building and building.outcome and panel.CRITERIA.how
    assert decision.chart and criterion.chart and shelves.FOOTER_ITEM.body
    assert building.outcome.charts
    assert panel.CRITERIA.how.charts
    assert decision.chart.charts
    assert criterion.chart.charts
    assert not shelves.FOOTER_ITEM.body.charts


def test_the_proposed_receipt_counts_each_plan_task_as_finished() -> None:
    task = RECEIPT.task
    phases = panel.OVERVIEW.phases
    assert task.status == "open" and task.plan and phases and phases.ring
    finished = sum(span.name == "task" and span.end is not None for span in task.spans)
    ring = phases.ring
    assert (ring.done, ring.current, ring.total) == (finished, 0, task.plan.tasks)


def test_the_panel_prints_the_landing_the_decisions_and_the_criteria_of_its_record() -> (
    None
):
    landing = RECEIPT.landing
    assert landing and landing.proposed and landing.checked
    merge = panel.MERGE
    assert merge.confirm.form
    fields = {field.name: field.shown for field in merge.confirm.form.fields}
    assert fields == {"confirm": "yes", "tip": landing.proposed.tip}
    taken = [each for each in RECEIPT.task.decisions if isinstance(each, Taken)]
    shown = panel.CRITERIA.decisions
    assert [(each.id, each.what, each.chose) for each in shown] == [
        (each.id, each.what, each.chose) for each in taken
    ]
    criteria = RECEIPT.task.criteria.criteria
    assert [(each.number, each.text) for each in panel.CRITERIA.criteria] == [
        (each.number, each.text) for each in criteria
    ]
    assert [(each.command, each.last) for each in panel.CHECKS.commands] == [
        (each.command, each.last) for each in landing.checked.outcomes
    ]
    assert len(panel.CHECKS.rounds) == len(landing.reviews)
    for reasons in (
        panel.OVERVIEW.verdict and panel.OVERVIEW.verdict.reasons,
        panel.CHECKS.proposal and panel.CHECKS.proposal.reasons,
        merge.reasons,
        waiting.MERGE.reasons,
    ):
        assert reasons and len(reasons.rows) == len(landing.proposed.reasons)


def test_the_merge_confirm_shows_the_prefix_of_the_tip_it_submits() -> None:
    form = panel.MERGE.confirm.form
    assert form
    tip = next(field.shown for field in form.fields if field.name == "tip")
    commit = next(fact for fact in panel.MERGE.facts if fact.key == "commit")
    # The saved showcase page prints a 12-digit prefix, with the full tip in the form.
    assert (commit.term, commit.text, commit.mono) == ("Commit", tip[:12], True)


def assert_merge_target(merge: Merge) -> None:
    landing = RECEIPT.landing
    assert landing and landing.pull and landing.started
    pull_rows = [
        fact
        for fact in merge.facts
        if fact.key == "pr" or fact.term == "Pull request" or fact.link is not None
    ]
    into_rows = [
        fact for fact in merge.facts if fact.key == "into" or fact.term == "Into"
    ]
    assert len(pull_rows) == 1
    assert len(into_rows) == 1
    assert (pull_rows[0].key, pull_rows[0].term) == ("pr", "Pull request")
    assert (into_rows[0].key, into_rows[0].term) == ("into", "Into")
    link = pull_rows[0].link
    assert link
    assert (link.label, link.href, into_rows[0].text) == (
        f"acme/shop#{landing.pull.number}",
        landing.pull.url,
        landing.started.base_ref,
    )
    form = merge.confirm.form
    assert form
    assert merge.confirm.eyebrow == f"Merge #{landing.pull.number} · confirm"
    assert (form.label, form.busy) == ("Approve", "Approving…")


def test_the_merge_confirm_links_to_the_pull_and_names_its_base_branch() -> None:
    assert_merge_target(panel.MERGE)


def assert_merge_verdict(merge: Merge) -> None:
    landing = RECEIPT.landing
    assert landing and landing.proposed
    green = landing.proposed.green
    assert (merge.green, merge.word) == (green, "Green" if green else "Not green")
    assert merge.confirm.form and merge.confirm.sheet


def test_the_merge_confirm_matches_the_proposals_verdict_and_uses_a_sheet() -> None:
    assert_merge_verdict(panel.MERGE)


@pytest.mark.parametrize(
    "changes",
    [
        {"green": True},
        {"word": "Green"},
        {"confirm": msgspec.structs.replace(panel.MERGE.confirm, sheet=False)},
    ],
    ids=("flag", "word", "sheet"),
)
def test_the_merge_confirm_check_refuses_false_green_and_a_disabled_sheet(
    changes: dict[str, object],
) -> None:
    merge = msgspec.structs.replace(panel.MERGE, **changes)
    with pytest.raises(AssertionError):
        assert_merge_verdict(merge)


@pytest.mark.parametrize(
    ("wrong_pull", "wrong_base"),
    [(True, True), (True, False), (False, True)],
    ids=("both", "pull", "base"),
)
def test_the_merge_target_check_rejects_conflicting_rows(
    *, wrong_pull: bool, wrong_base: bool
) -> None:
    other_rows = []
    if wrong_pull:
        other_pull = msgspec.structs.replace(
            panel.PULL,
            label="acme/shop#99",
            href="https://github.com/acme/shop/pull/99",
        )
        other_rows.append(Fact(key="pr", term="Pull request", link=other_pull))
    if wrong_base:
        other_rows.append(Fact(key="into", term="Into", text="release", mono=True))
    merge = msgspec.structs.replace(
        panel.MERGE, facts=(*other_rows, *panel.MERGE.facts)
    )
    with pytest.raises(AssertionError):
        assert_merge_target(merge)


@pytest.mark.parametrize(
    ("wrong_heading", "wrong_button"),
    [(True, True), (True, False), (False, True)],
    ids=("both", "heading", "button"),
)
def test_the_merge_target_check_rejects_conflicting_text(
    *, wrong_heading: bool, wrong_button: bool
) -> None:
    confirm = panel.MERGE.confirm
    form = confirm.form
    assert form
    if wrong_heading:
        confirm = msgspec.structs.replace(confirm, eyebrow="Merge #99 · confirm")
    if wrong_button:
        form = msgspec.structs.replace(form, label="Merge pull request #99")
        confirm = msgspec.structs.replace(confirm, form=form)
    merge = msgspec.structs.replace(panel.MERGE, confirm=confirm)
    with pytest.raises(AssertionError):
        assert_merge_target(merge)


def test_the_merge_confirm_shows_each_proposed_reason_and_its_links() -> None:
    landing = RECEIPT.landing
    reasons = panel.MERGE.reasons
    assert landing and landing.proposed and landing.pull and reasons
    # The saved confirm page links decision 1 and PR #44, in the first and last rows.
    number, url = landing.pull.number, landing.pull.url
    pull = f"#{number}"
    last = f"request [{pull}]({url}) answers"
    refs = [row.ref for row in reasons.rows]
    link = refs[0]
    assert link
    assert (link.label, link.href, link.anchor, link.frame) == (
        "decision 1",
        f"{BASE}/tasks/{RECEIPT.task.slug}/criteria",
        "dec-1",
        True,
    )
    assert refs[1:] == [None, None, None]
    assert reasons.rows[-1].detail[0].endswith(last)
    # The proposal is plain prose. The page splits it into headings, labels and detail.
    shown = [
        " ".join((row.head, row.about or "", *row.detail)).replace(
            last, f"request {pull} answers"
        )
        for row in reasons.rows
    ]
    words = re.compile(r"[\w#]+")
    assert [words.findall(row.casefold()) for row in shown] == [
        words.findall(reason.casefold()) for reason in landing.proposed.reasons
    ]


def test_a_step_of_an_act_draws_the_header_with_no_act_and_no_tab_shown() -> None:
    assert panel.OPEN.head and panel.OPEN.head.acts
    assert panel.MERGE_STEP.head and panel.MERGE_STEP.head.acts is None
    assert not any(tab.current for tab in panel.MERGE_STEP.tabs)
    assert [tab.key for tab in panel.OPEN.tabs if tab.current] == ["overview"]


def test_the_types_of_the_afternoons_pages_are_the_sections_of_a_page() -> None:
    assert isinstance(frame.FRAME, Frame)
    assert isinstance(columns.TASKS, Tasks)
    assert isinstance(waiting.WAITS, Waits)
    assert isinstance(shelves.BACKLOG, Backlog)
    assert all(isinstance(each, Panel) for each in (panel.OPEN, panel.MERGE_STEP))
    assert all(isinstance(each, Record) for each in RECORDS)
