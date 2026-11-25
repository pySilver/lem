"""The afternoon gathered from its workspace: every record with Lem's acts and its files beside
it, each session as a demo takes it from the acts alone, and the rows of what waits for the
owner that every view counts."""

from typing import TYPE_CHECKING

from fixtures.board.beside import RECORDS
from fixtures.board.receipt import TIP
from lem.board.views import owed
from unit.board.views.afternoon import SUBJECT, world

if TYPE_CHECKING:
    from pathlib import Path


def test_the_world_holds_each_record_with_its_acts_files_and_branch(
    tmp_path: Path,
) -> None:
    seen = world(tmp_path)
    assert [each.record for each in seen.tasks] == sorted(
        RECORDS, key=lambda each: each.task.slug
    )
    receipt = owed.seen(seen, "refund-line-on-receipt")
    assert receipt.head and (receipt.head.sha, receipt.head.subject) == (TIP, SUBJECT)
    assert receipt.filed == ()
    assert "merge-review.md" in receipt.files
    assert receipt.text("task.md") and receipt.text("merge-review.md")
    assert seen.demo
    assert seen.unknown is None


def test_a_demo_takes_each_session_from_the_acts_alone(tmp_path: Path) -> None:
    seen = world(tmp_path)
    live = {
        each.record.task.slug
        for each in seen.tasks
        if each.session and each.session.live
    }
    assert live == {
        "coupon-has-a-slug",
        "gift-note-in-export",
        "refund-line-on-receipt",
        "refund-rounding",
        "stock-on-product-page",
    }


def test_six_things_wait_for_the_owner_in_five_tasks(tmp_path: Path) -> None:
    seen = world(tmp_path)
    rows = owed.rows(seen)
    assert [(row.kind, row.task) for row in rows] == [
        ("breaker", "gift-note-in-export"),
        ("session", "cart-total-after-coupon"),
        ("card", "refund-rounding"),
        ("criteria", "stock-on-product-page"),
        ("review", "refund-line-on-receipt"),
        ("merge", "refund-line-on-receipt"),
    ]
    assert len(owed.stacks(seen)) == 5
