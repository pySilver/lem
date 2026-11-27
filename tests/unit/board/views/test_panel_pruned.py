"""The panel of a task whose journal became one summary (`main`'s `test_board_model.py`
SummarizedBoard: `board_task.summary_card`, `files_line`, `went_tab` and `overview_tab`)."""

import dataclasses
from typing import TYPE_CHECKING

import msgspec

from lem.board.views import owed, standing
from lem.board.views.panel import pruned
from lem.board.views.panel.head import head
from lem.board.views.panel.opened import Opened
from lem.board.views.panel.panel import panel
from lem.records.journal.task import StateNoted, Summary
from lem.records.tickets import Ticket
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.inputs.task.overview import Overview
    from lem.board.views.world import Seen, World

INVOICE = "order-date-on-invoice"
RECORD = "its small record: its state, its request and its pull request"


def summarized(afternoon: World, *files: str) -> World:
    """The afternoon with the invoice's journal folded into one summary of 60 entries, and
    its folder holding its request and `files`."""
    seen = owed.seen(afternoon, INVOICE)
    record = seen.record
    last = next(one for one in reversed(record.journal) if isinstance(one, StateNoted))
    summary = Summary(
        at=afternoon.clock.now,
        statuses=("shaping", "building", "landing", "open", "landed"),
        last_state=last,
        first=record.task.opened,
        last=last.at,
        entries=60,
        pull=38,
        green=True,
    )
    folded = msgspec.structs.replace(record, journal=(summary,))
    kept = msgspec.structs.replace(seen, record=folded, files=("task.md", *files))
    tasks = tuple(kept if one is seen else one for one in afternoon.tasks)
    return dataclasses.replace(afternoon, tasks=tasks)


def overview_of(afternoon: World, keep_days: int | None = 30) -> Overview:
    """The Overview of the invoice in `afternoon`."""
    found = panel(afternoon, INVOICE, "overview", opened=Opened(keep_days=keep_days))
    assert found.overview is not None
    return found.overview


def files_said(afternoon: World, keep_days: int | None = 30) -> str:
    """The line of what the invoice's folder holds."""
    found = overview_of(afternoon, keep_days).pruned
    assert found is not None
    return found.files


def test_a_pruned_task_whose_folder_holds_its_small_record_alone_says_what_stayed(
    tmp_path: Path,
) -> None:
    """`main`'s SummarizedBoard.test_a_pruned_task_whose_folder_holds_its_small_record_alone_
    says_what_stayed_and_that_the_rest_left; and, changed, its
    test_a_pruned_task_whose_folder_does_not_read_claims_nothing_of_its_files: the record is in
    the folder, so a task the board reads has a folder that reads."""
    said = files_said(summarized(world(tmp_path)))
    assert said == (
        f"What stayed of its folder is {RECORD}. Its other files left: Lem keeps only "
        "this record of an ended task after 30 days in which nothing of it happened "
        "(state.keep_days, as the settings say now)."
    )
    assert "ticket" not in said


def test_a_pruned_task_with_a_ticket_names_it_from_its_record_and_the_number_is_the_settings_of_now(
    tmp_path: Path,
) -> None:
    """`main`'s SummarizedBoard.test_a_pruned_task_with_a_ticket_names_its_files_and_the_
    number_is_the_settings_of_now, changed: the ticket and the task it was resumed from are
    fields of the record, and the files retention keeps beside it are no files left over."""
    afternoon = summarized(
        world(tmp_path), "sessions.jsonl", "parked.json", "criteria.lock"
    )
    seen = owed.seen(afternoon, INVOICE)
    task = msgspec.structs.replace(
        seen.record.task,
        ticket=Ticket(tracker="linear", id="SHOP-12"),
        resumed_from="order-date-first-try",
    )
    record = msgspec.structs.replace(seen.record, task=task)
    kept = msgspec.structs.replace(seen, record=record)
    tasks = tuple(kept if one is seen else one for one in afternoon.tasks)
    said = files_said(dataclasses.replace(afternoon, tasks=tasks), keep_days=7)
    assert said.startswith(
        "1 file of its folder is still there beside its small record: "
    )
    assert "parked.json" not in said
    without = summarized(world(tmp_path / "again"), "sessions.jsonl", "criteria.lock")
    seen = owed.seen(without, INVOICE)
    named = msgspec.structs.replace(seen, record=record)
    tasks = tuple(named if one is seen else one for one in without.tasks)
    said = files_said(dataclasses.replace(without, tasks=tasks), keep_days=7)
    assert (
        "its small record: its state, its request, its pull request, its ticket "
        "and the name of the task it was resumed from."
    ) in said
    assert "after 7 days in which nothing of it happened" in said


def test_settings_that_do_not_read_give_no_number_on_the_card(tmp_path: Path) -> None:
    """`main`'s SummarizedBoard.test_settings_that_do_not_read_give_no_number_on_the_card."""
    said = files_said(summarized(world(tmp_path)), keep_days=None)
    assert (
        "after state.keep_days days in which nothing of it happened (the settings do not "
        "read now, so the board does not say that number)"
    ) in said
    assert "30" not in said


def test_a_pruned_task_whose_folder_still_holds_files_beyond_its_record_says_only_how_many(
    tmp_path: Path,
) -> None:
    """`main`'s SummarizedBoard.test_a_pruned_task_whose_folder_still_holds_files_beyond_its_
    record_says_only_how_many."""
    afternoon = summarized(
        world(tmp_path), "report.md", "media/after.png", "reviews/r/round.lock"
    )
    said = files_said(afternoon)
    assert said == f"3 files of its folder are still there beside {RECORD}."


def test_the_header_says_the_same_status_end_pull_request_and_track(
    tmp_path: Path,
) -> None:
    """`main`'s SummarizedBoard.test_the_header_says_the_same_status_end_pull_request_and_
    track."""
    before = world(tmp_path)
    after = summarized(before)

    def drawn(afternoon: World) -> tuple[object, ...]:
        seen: Seen = owed.seen(afternoon, INVOICE)
        rows = owed.of_task(afternoon, INVOICE)
        found = head(afternoon, seen, rows, standing.standing(seen, rows), acting=True)
        keyed = {fact.key: fact for fact in found.facts}
        return (found.pill, keyed["pr"], keyed["time"], found.key_line, keyed["type"])

    assert drawn(after) == drawn(before)
    pull, kind = drawn(after)[1], drawn(after)[4]
    assert getattr(getattr(pull, "link", None), "label", None) == "acme/shop#38"
    assert (getattr(kind, "bold", None), getattr(kind, "text", None)) == (
        "feat",
        "standard track",
    )


def test_the_overview_opens_with_the_summary_and_no_tab_draws_an_empty_section(
    tmp_path: Path,
) -> None:
    """`main`'s SummarizedBoard.test_the_overview_opens_with_the_summary_and_no_tab_draws_an_
    empty_section: the summary keeps its facts, the Overview has no progress, and each tab
    whose detail went says so in one line."""
    afternoon = summarized(world(tmp_path))
    found = overview_of(afternoon)
    assert found.pruned is not None
    assert found.pruned.events == "60 events"
    for kept in (
        "landed",
        "pull request acme/shop#38",
        "green",
        "type feat",
        "branch feat/order-date-on-invoice",
    ):
        assert kept in found.pruned.kept
    assert found.pruned.artifacts.label == "Artifacts"
    assert found.building is not None
    assert found.phases is None
    seen = owed.seen(afternoon, INVOICE)
    for tab, went in (
        (
            "criteria",
            (
                "Its acceptance criteria, their approval, the personas’ read and its "
                "decisions went with its events"
            ),
        ),
        (
            "checks",
            (
                "Its runs of the checks, its review rounds and the proposal’s reasons went "
                "with its events"
            ),
        ),
        ("timeline", "Its timeline and its events went with its events"),
    ):
        line = pruned.went(afternoon, seen, tab)
        assert line.id == f"went-{tab}"
        assert line.said.startswith(went)


def test_a_task_whose_journal_is_whole_has_no_summary_card(tmp_path: Path) -> None:
    """`main`'s SummarizedBoard.test_a_task_whose_events_are_whole_has_no_summary_card."""
    found = overview_of(world(tmp_path))
    assert found.pruned is None
    assert found.phases is not None


def test_an_answered_task_names_its_report_only_while_its_folder_holds_it(
    tmp_path: Path,
) -> None:
    """`main`'s SummarizedBoard.test_an_answered_task_names_its_report_only_while_its_folder_
    holds_it."""
    afternoon = world(tmp_path)
    slug = "why-export-is-slow"
    line = "The report is investigation.md in the task directory"
    found = panel(afternoon, slug, "overview").overview
    assert found is not None
    assert found.now.report == line
    assert found.now.found is not None
    assert "the export reads each order of the month" in found.now.found
    seen = owed.seen(afternoon, slug)
    gone = msgspec.structs.replace(seen, files=())
    tasks = tuple(gone if one is seen else one for one in afternoon.tasks)
    later = panel(dataclasses.replace(afternoon, tasks=tasks), slug, "overview")
    assert later.overview is not None
    assert later.overview.now.report is None
    assert later.overview.now.found == found.now.found
