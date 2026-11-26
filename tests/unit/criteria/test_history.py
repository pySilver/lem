"""The criteria's history as the pull request reads it, written by the commands themselves: the
wait for the owner's yes and the approval that ended it, each change from his notes, a reversal
too, and a change against a read of the personas in the order they were written, also in the same
second (`main:land.criteria_waited`, `changed_after_read`)."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from lem.app.criteria import approve, change, typed
from lem.app.landing import checks_record, pr_read
from lem.app.tasks import shape
from lem.kernel import clock
from lem.model.criteria import reads
from lem.model.task.read import Queue
from lem.records.approvals import Silent
from lem.records.task import Shape
from lem.store import places, tasks
from unit.criteria import world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.approvals import ApprovedBy
    from lem.records.record import Record

SHAPE = Shape(type="feat", why="the export gets a new column", track="full")
NOTE = "criterion 2 must also cover empty rows"
OTHER = world.FULL.replace(
    'not the word "None".',
    'not the word "None", and a blank row stays: order 1042 with no note exports both.',
)
BEGAN = datetime(2026, 11, 25, 10, 0, tzinfo=UTC)
YES = BEGAN + timedelta(hours=1)
CLEAR = reads.Found(
    asked=2,
    answered=2,
    families=("opus", "sol"),
    criteria=2,
    flagged=0,
    digest="d" * 16,
)
SILENT = reads.Found(
    asked=2,
    answered=0,
    silent=(
        Silent(name="the buyer, opus", why="the model was at capacity"),
        Silent(name="the clerk, sol", why="the model was at capacity"),
    ),
    criteria=2,
    flagged=0,
    digest="d" * 16,
)


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    found = world.workspace(tmp_path / "shop")
    world.task(found)
    world.sheet(found, world.FULL)
    return found


def at(monkeypatch: pytest.MonkeyPatch, moment: datetime) -> None:
    monkeypatch.setattr(clock, "now", lambda: moment)


def sheet(checkout: Path) -> Path:
    return places.task_folder(checkout / places.STATE, world.SLUG) / "criteria.md"


def waits_for_him(checkout: Path) -> None:
    """`lem task read --wait criteria`: the criteria wait for the owner's yes."""
    shape.shaped(checkout, world.SLUG, SHAPE, Queue(wait="criteria"))


def approved(checkout: Path, by: ApprovedBy = "owner") -> None:
    approve.approved(checkout, world.SLUG, approve.Asked(by=by, path=sheet(checkout)))


def changed_to(checkout: Path, text: str) -> None:
    """His typed No, and the change of the criteria to `text` from his note."""
    typed.typed(checkout, world.SLUG, NOTE)
    path = checkout / "criteria-change.md"
    path.write_text(text, encoding="utf-8")
    change.changed(checkout, world.SLUG, path, NOTE)


def read_by_personas(checkout: Path, found: reads.Found | None = CLEAR) -> None:
    """A read of the personas that starts and ends now, with `found`."""
    state = checkout / places.STATE
    record = tasks.read(state, world.SLUG)
    task = reads.ended(record.task, "lem", clock.now(), found)
    tasks.update(
        state, world.SLUG, lambda one: replace(one, task=task), record.revision
    )


def line(checkout: Path) -> str:
    return pr_read.read_line(world.read(checkout))


def test_his_yes_ends_the_wait_the_read_began(
    checkout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at(monkeypatch, BEGAN)
    waits_for_him(checkout)
    at(monkeypatch, YES)
    approved(checkout)
    assert line(checkout).endswith(
        "the criteria waited for the owner's yes from 2026-11-25 10:00 UTC, and the owner "
        "gave it on 2026-11-25 11:00 UTC"
    )
    at(monkeypatch, YES + timedelta(days=1))
    approved(checkout)
    assert line(checkout).endswith(
        "the owner gave it on 2026-11-25 11:00 UTC; the owner approved them again on "
        "2026-11-26"
    )


def test_an_approval_without_him_ends_the_wait_and_his_later_one_is_named(
    checkout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at(monkeypatch, BEGAN)
    waits_for_him(checkout)
    world.away()
    at(monkeypatch, YES)
    approved(checkout, "alone")
    world.away(gone=False)
    at(monkeypatch, YES + timedelta(days=1))
    approved(checkout)
    assert line(checkout).endswith(
        "the criteria waited for the owner's yes from 2026-11-25 10:00 UTC, and the wait "
        "ended without the owner: approved on 2026-11-25 11:00 UTC while the task ran "
        "without the owner; the owner approved them on 2026-11-26"
    )


def test_a_new_wait_after_his_no_is_ended_by_the_approval_after_it(
    checkout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at(monkeypatch, BEGAN)
    waits_for_him(checkout)
    at(monkeypatch, BEGAN + timedelta(minutes=20))
    changed_to(checkout, OTHER)
    assert "waited for" not in line(checkout)
    at(monkeypatch, YES)
    approved(checkout)
    assert line(checkout).endswith(
        "the criteria waited for the owner's yes from 2026-11-25 10:20 UTC, and the owner "
        "gave it on 2026-11-25 11:00 UTC"
    )


def test_the_fast_track_that_grew_is_held_for_the_interview_with_no_wait(
    checkout: Path,
) -> None:
    record: Record = world.read(checkout)
    grown = checks_record.reshaped(
        record,
        line="the criteria wait for the owner: the small change is a full change",
        at=BEGAN,
    )
    assert grown.task.criteria.waited is None


def test_a_change_and_its_way_back_both_count_after_the_read(
    checkout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at(monkeypatch, BEGAN)
    waits_for_him(checkout)
    read_by_personas(checkout)
    at(monkeypatch, BEGAN + timedelta(minutes=5))
    changed_to(checkout, OTHER)
    at(monkeypatch, BEGAN + timedelta(minutes=10))
    changed_to(checkout, world.FULL)
    assert (
        "; the criteria changed 2 times after the personas' read, from the owner's notes"
        in line(checkout)
    )


def test_a_change_and_a_read_in_the_same_second_keep_their_order(
    checkout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at(monkeypatch, BEGAN)
    waits_for_him(checkout)
    changed_to(checkout, OTHER)
    read_by_personas(checkout)
    assert "after the personas' read" not in line(checkout)
    changed_to(checkout, world.FULL)
    assert (
        "; the criteria changed once after the personas' read, from the owner's notes"
        in line(checkout)
    )


def test_a_change_after_two_reads_nobody_answered_is_counted(
    checkout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    at(monkeypatch, BEGAN)
    waits_for_him(checkout)
    read_by_personas(checkout, SILENT)
    read_by_personas(checkout, SILENT)
    at(monkeypatch, BEGAN + timedelta(minutes=5))
    changed_to(checkout, OTHER)
    assert line(checkout).startswith(
        "- the criteria were not read by the personas: 2 reads in a row, and none of the "
        "2 personas asked answered; the criteria changed once after the personas' read, "
        "from the owner's notes; "
    )
