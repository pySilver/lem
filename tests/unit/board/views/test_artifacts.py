"""The map of a task's files: the seven sections of every task, a record on its document, a
picture on the document that shows it, and every file the map does not know among the working
files; and the count of documents the tab bar shows."""

from typing import TYPE_CHECKING

from fixtures.board.receipt import SLUG
from lem.board.views import owed
from lem.board.views.artifacts.arrange import arrange
from lem.board.views.artifacts.kinds import kind_of
from lem.board.views.artifacts.listing import count, map_of
from lem.board.views.artifacts.mapped import Entry
from lem.board.views.artifacts.scratch import place
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path


def entry(path: str) -> Entry:
    """A file of a task's folder, placed as the map places it."""
    return Entry(path=path, spot=place(path), kind=kind_of(path))


def test_the_refund_line_has_seven_documents_on_its_map(tmp_path: Path) -> None:
    """Today's `artifacts.arrange` over the laid folder gives 7: `state.md` and the plan in the
    worktree, which made `main`'s 9 with a file of the owner's words, are not in the
    afternoon."""
    seen = owed.seen(world(tmp_path), SLUG)
    assert count(seen) == 11
    found = map_of(seen)
    assert found.count == 7
    assert [shelf.name for shelf in found.sections] == [
        "Request",
        "Criteria",
        "Plan",
        "Build",
        "Checks",
        "Review",
        "Pull request",
    ]
    docs = {
        shelf.key: [hung.doc.path for hung in shelf.docs] for shelf in found.sections
    }
    assert docs == {
        "request": ["task.md"],
        "criteria": [],
        "plan": [],
        "build": ["report.md"],
        "checks": [
            "checks/r1-1-000000000001.log",
            "checks/r1-2-000000000002.log",
        ],
        "review": [],
        "pr": ["merge-review.md", "page.html", "pr.md"],
    }
    report = found.sections[3].docs[0]
    assert [(each.path, each.label) for each in report.attached] == [
        ("media/receipt-after.png", "receipt-after.png")
    ]
    piles = [(pile.folder, [each.path for each in pile.files]) for pile in found.work]
    assert piles == [
        (None, ["built.md", "decisions.md"]),
        ("Pictures", ["media/receipt-before.png"]),
    ]
    assert found.work_count == 3


def test_a_record_hangs_on_its_document_and_what_the_map_does_not_know_is_a_working_file() -> (
    None
):
    """The ruling "A task's artifacts have one map" (`main`'s
    test_board_task.Map.test_a_record_hangs_on_its_document_and_what_the_map_does_not_know_is_a_working_file)."""
    paths = (
        "task.md",
        "report.md",
        "polish.json",
        "notes/scratch.txt",
        "reviews/claude-01-whole.log",
        "reviews/shop/01-whole/report.md",
        "reviews/shop/01-whole/raw.json",
    )
    found = arrange(tuple(entry(path) for path in paths), {})
    report = found.sections[3].docs[0]
    assert report.doc.path == "report.md"
    assert [(each.path, each.spot.label) for each in report.attached] == [
        ("polish.json", "polish pass")
    ]
    assert [hung.doc.spot.title for hung in found.sections[5].docs] == [
        "Review round 01-whole"
    ]
    piles = {pile.folder: [each.path for each in pile.files] for pile in found.work}
    assert piles == {
        "notes": ["notes/scratch.txt"],
        "Review round 01-whole": [
            "reviews/claude-01-whole.log",
            "reviews/shop/01-whole/raw.json",
        ],
    }
    assert found.count == 3
    alone = arrange((entry("polish.json"),), {})
    assert [
        (pile.folder, [each.path for each in pile.files]) for pile in alone.work
    ] == [("Records with no document", ["polish.json"])]


def test_a_check_output_is_placed_by_its_round_and_place_and_a_file_no_step_writes_is_loose() -> (
    None
):
    """A command's output where the checks publish it (`app/landing/checks_run.py`) is a document
    of the checks; a name the map knew from `main` that no step of this Lem writes is a working
    file like any other."""
    spot = place("checks/r2-3-0123456789ab.log")
    assert (spot.group, spot.title, spot.role) == (
        "checks",
        "Check 3 output, round 2",
        "doc",
    )
    assert place("reports/01-export.md").title == "Report: 01-export"
    for gone in ("gate/01.log", "ticket.txt", "landing.json", "red.json"):
        assert place(gone).role == "work", gone


def test_the_merge_agents_brief_of_a_tip_on_a_base_is_a_document_of_the_pull_request() -> (
    None
):
    """The ruling "A task's artifacts have one map" (`main`'s
    test_board_task.Map.test_the_merge_agents_brief_of_a_tip_on_a_base_is_a_document_of_the_pull_request)."""
    spot = place("merge-brief-0123456789abcdef-fedcba9876543210.md")
    assert (spot.group, spot.title, spot.role) == (
        "pr",
        "The merge agent's brief of 012345678 on fedcba987",
        "doc",
    )
