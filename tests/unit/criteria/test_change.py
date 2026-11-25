"""The owner's change of the criteria that wait for his yes: his typed No first, the change that
keeps what he answered and asks again under a new question, its pairs, a stop in the middle and
the run that ends it, a new wait of the same text, and each refusal."""

from datetime import date, timedelta
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from lem.app.criteria import approve, change, typed
from lem.kernel.errors import Refusal
from lem.model.criteria import digest, waits
from lem.model.criteria.pairs import pairs
from lem.model.criteria.read import sheet_of
from lem.records.criterion import Criterion
from lem.records.holds import OwnerHold
from lem.records.questions import Answer
from lem.store import places, tasks
from unit.criteria import world

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from lem.records.record import Record

NOTE = "criterion 2 must also cover empty rows"
CHANGED = world.FULL.replace(
    'not the word "None".',
    'not the word "None", and a blank row stays: order 1042 with no note exports both.',
)


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    found = world.workspace(tmp_path / "shop")
    world.task(found, hold=world.WAITS)
    world.sheet(found, world.FULL)
    return found


def new_file(checkout: Path, text: str = CHANGED) -> Path:
    path = checkout / "criteria-change.md"
    path.write_text(text, encoding="utf-8")
    return path


def refused(call: Callable[..., object], *args: object) -> Refusal:
    with pytest.raises(Refusal) as caught:
        call(*args)
    return caught.value


def number(criterion: Criterion | None) -> int:
    """A side's number, 0 for a side a pair has not."""
    return criterion.number if criterion else 0


def criteria(text: str) -> tuple[str, ...]:
    return tuple(one.text for one in sheet_of(text, "x.md").criteria)


def test_one_changed_and_two_in_one_note_are_pairs_by_text() -> None:
    before = sheet_of(world.FULL, "a").criteria
    after = sheet_of(CHANGED, "b").criteria
    found = pairs(before, after)
    assert [(one.change, number(one.before), number(one.after)) for one in found] == [
        ("changed", 2, 2)
    ]
    both = sheet_of(CHANGED.replace("1042 with the", "1043 with the"), "c").criteria
    assert [one.change for one in pairs(before, both)] == ["changed", "changed"]


def test_a_removal_keeps_the_next_criterion_as_it_was() -> None:
    three = world.FULL + "3. A third rule, with 7.\n"
    two = world.FULL.split("2. An order")[0] + "2. A third rule, with 7.\n"
    found = pairs(sheet_of(three, "a").criteria, sheet_of(two, "b").criteria)
    assert [one.change for one in found] == ["removed"]
    assert found[0].before is not None
    assert found[0].before.number == 2


def test_one_replaced_by_two_is_a_removal_and_two_additions() -> None:
    before = sheet_of(world.FULL, "a").criteria
    split = world.FULL.replace(
        '2. An order with no gift note has an empty cell, not the word "None".',
        "2. An order with no note has an empty cell.\n3. An empty cell is never None.",
    )
    found = pairs(before, sheet_of(split, "b").criteria)
    assert [one.change for one in found] == ["removed", "added", "added"]


def test_an_added_criterion_and_a_new_line_break_that_is_no_change() -> None:
    before = sheet_of(world.FULL, "a").criteria
    after = (
        world.FULL.replace("has\n   that text", "has that\n   text")
        + "3. A third, 7.\n"
    )
    found = pairs(before, sheet_of(after, "b").criteria)
    assert [(one.change, number(one.after)) for one in found] == [("added", 3)]


def test_his_typed_no_is_the_answer_and_twice_is_one_record(checkout: Path) -> None:
    first = typed.typed(checkout, world.SLUG, NOTE)
    again = typed.typed(checkout, world.SLUG, NOTE)
    assert (first.recorded, again.recorded) == (True, False)
    assert first.question == again.question
    assert waits.said_no(world.read(checkout).task) is not None


def answered_on_board(checkout: Path, option: str) -> None:
    state = checkout / places.STATE
    record = tasks.read(state, world.SLUG)
    task = record.task
    question = waits.question(task, world.EARLY, None)
    said = Answer(option=option, label=option.title(), source="board", at=world.EARLY)
    after = waits.answered(task, question, said)
    tasks.update(
        state, world.SLUG, lambda found: replace(found, task=after), record.revision
    )


def test_a_board_answer_that_came_first_refuses_his_typed_no(checkout: Path) -> None:
    answered_on_board(checkout, "yes")
    assert refused(typed.typed, checkout, world.SLUG, NOTE).code == "answered-first"


def test_an_approval_after_the_wait_refuses_his_typed_no(checkout: Path) -> None:
    approve.approved(
        checkout,
        world.SLUG,
        approve.Asked(by="owner", path=world.sheet(checkout, world.FULL)),
    )
    assert refused(typed.typed, checkout, world.SLUG, NOTE).code == "not-waiting"


def test_the_change_keeps_the_text_he_answered_and_writes_a_new_wait(
    checkout: Path,
) -> None:
    typed.typed(checkout, world.SLUG, NOTE)
    said = change.changed(checkout, world.SLUG, new_file(checkout), NOTE)
    task = world.read(checkout).task
    assert task.criteria.change is not None
    assert task.criteria.change.text == world.FULL
    assert isinstance(task.hold, OwnerHold)
    assert task.hold.line == waits.CHANGED
    assert waits.said_no(task) is None
    assert said.question == task.questions[-1].id
    assert [one.change for one in said.pairs] == ["changed"]
    assert said.shown == digest.shown(CHANGED.encode())
    assert world.sheet(checkout, world.FULL).parent.joinpath("criteria.md").exists()


def test_the_new_wait_is_a_new_question_also_in_the_same_second(checkout: Path) -> None:
    typed.typed(checkout, world.SLUG, NOTE)
    change.changed(checkout, world.SLUG, new_file(checkout), NOTE)
    task = world.read(checkout).task
    assert len({one.id for one in task.questions}) == 2
    assert waits.question_of(task) == task.questions[-1]


def test_a_second_no_changes_the_changed_text_again(checkout: Path) -> None:
    typed.typed(checkout, world.SLUG, NOTE)
    change.changed(checkout, world.SLUG, new_file(checkout), NOTE)
    typed.typed(checkout, world.SLUG, "and criterion 1 names Ania")
    third = CHANGED.replace("1042 with the", "1043 with the")
    said = change.changed(checkout, world.SLUG, new_file(checkout, third), "and 1043")
    kept = world.read(checkout).task.criteria.change
    assert kept is not None
    assert kept.text == CHANGED
    assert said.words == "and 1043"


def test_the_pairs_again_while_the_wait_stands(checkout: Path) -> None:
    typed.typed(checkout, world.SLUG, NOTE)
    world.sheet(checkout, world.FULL)
    said = change.changed(checkout, world.SLUG, new_file(checkout), NOTE)
    world.sheet(checkout, CHANGED)
    again = change.again(checkout, world.SLUG)
    assert (again.pairs, again.question, again.shown) == (
        said.pairs,
        said.question,
        said.shown,
    )


def test_a_stop_between_the_record_and_the_file_and_a_second_run_ends_it(
    checkout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    typed.typed(checkout, world.SLUG, NOTE)

    class Cut:
        @staticmethod
        def write_whole(path: Path, body: bytes) -> None:
            raise OSError(path, body)

    monkeypatch.setattr(change, "files", Cut)
    with pytest.raises(OSError):
        change.changed(checkout, world.SLUG, new_file(checkout), NOTE)
    monkeypatch.undo()
    assert refused(change.again, checkout, world.SLUG).code == "changed-meanwhile"
    assert refused(typed.unchanged, checkout, world.SLUG).code == "changed-meanwhile"
    ended = change.changed(checkout, world.SLUG, new_file(checkout), NOTE)
    assert ended.resumed
    assert criteria(
        (checkout / ".lem/state/tasks/gift-note/criteria.md").read_text()
    ) == criteria(CHANGED)


def test_his_yes_after_the_change_approves_the_text_the_page_showed(
    checkout: Path,
) -> None:
    typed.typed(checkout, world.SLUG, NOTE)
    said = change.changed(checkout, world.SLUG, new_file(checkout), NOTE)
    sheet = checkout / ".lem/state/tasks/gift-note/criteria.md"
    made = approve.approved(
        checkout, world.SLUG, approve.Asked(by="owner", path=sheet, shown=said.shown)
    )
    after = sheet_of(CHANGED, "x.md")
    assert made.number == 1
    assert made.digest == digest.of_texts(after.size, after.criteria)


def test_a_new_wait_of_the_same_text_takes_his_yes(checkout: Path) -> None:
    typed.typed(checkout, world.SLUG, "why two columns?")
    again = typed.unchanged(checkout, world.SLUG)
    task = world.read(checkout).task
    assert isinstance(task.hold, OwnerHold)
    assert (again.words, task.hold.line) == ("why two columns?", waits.UNCHANGED)
    sheet = checkout / ".lem/state/tasks/gift-note/criteria.md"
    made = approve.approved(
        checkout, world.SLUG, approve.Asked(by="owner", path=sheet, shown=again.shown)
    )
    assert made.number == 1


def test_a_new_wait_needs_his_no_on_record(checkout: Path) -> None:
    assert refused(typed.unchanged, checkout, world.SLUG).code == "no-answer"
    answered_on_board(checkout, "yes")
    assert refused(typed.unchanged, checkout, world.SLUG).code == "answered-first"


def test_his_no_then_away_refuses_alone_until_the_change_from_his_note(
    checkout: Path,
) -> None:
    typed.typed(checkout, world.SLUG, NOTE)
    world.away()
    sheet = checkout / ".lem/state/tasks/gift-note/criteria.md"
    alone = approve.Asked(by="alone", path=sheet)
    assert refused(approve.approved, checkout, world.SLUG, alone).code == "said-no"
    change.changed(checkout, world.SLUG, new_file(checkout), NOTE)
    assert approve.approved(checkout, world.SLUG, alone).by == "alone"


def test_refusals(checkout: Path, tmp_path: Path) -> None:
    assert (
        refused(change.changed, checkout, world.SLUG, new_file(checkout), " ").code
        == "no-words"
    )
    same = new_file(checkout, world.FULL)
    typed.typed(checkout, world.SLUG, NOTE)
    assert refused(change.changed, checkout, world.SLUG, same, NOTE).code == "unchanged"
    tested = new_file(checkout, CHANGED.replace("row.\n", "row.\n" + world.TESTED))
    assert (
        refused(change.changed, checkout, world.SLUG, tested, NOTE).code == "test-lines"
    )
    small = new_file(checkout, world.SMALL)
    assert refused(change.changed, checkout, world.SLUG, small, NOTE).code == "not-full"
    assert refused(change.again, checkout, world.SLUG).code == "no-change"
    other = world.workspace(tmp_path / "other")
    world.task(other, hold=world.WAITS)
    assert (
        refused(change.changed, other, world.SLUG, new_file(checkout), NOTE).code
        == "no-file"
    )
    quiet = world.workspace(tmp_path / "quiet")
    world.task(quiet)
    world.sheet(quiet, world.FULL)
    assert refused(
        change.changed, quiet, world.SLUG, new_file(checkout), NOTE
    ).code == ("not-waiting")


def held_since(checkout: Path, hold_line: str, *, approved_before: bool) -> None:
    """The task held for his yes again from EARLY, with its newest approval moved before that
    moment, or to it."""
    state = checkout / places.STATE
    record: Record = tasks.read(state, world.SLUG)
    *older, newest = record.task.criteria.approvals
    moved = world.EARLY - timedelta(days=int(approved_before))
    approvals = (*older, replace(newest, at=moved))
    hold = replace(world.WAITS, line=hold_line)
    criteria = replace(record.task.criteria, approvals=approvals)
    tasks.update(
        state,
        world.SLUG,
        lambda found: replace(
            found, task=replace(found.task, hold=hold, criteria=criteria)
        ),
        record.revision,
    )


def test_the_fast_track_and_an_approval_of_the_standard_track(tmp_path: Path) -> None:
    fast = world.workspace(tmp_path / "fast")
    world.task(fast, hold=world.WAITS)
    world.sheet(fast, world.SMALL)
    assert refused(typed.typed, fast, world.SLUG, NOTE).code == "fast-track"
    full = world.workspace(tmp_path / "full")
    world.task(full)
    path = world.sheet(full, world.FULL)
    approve.approved(full, world.SLUG, approve.Asked(by="owner", path=path))
    held_since(full, "the criteria wait for the owner", approved_before=False)
    assert refused(typed.typed, full, world.SLUG, NOTE).code == "answered-first"
    held_since(full, "the criteria wait for the owner", approved_before=True)
    assert refused(typed.typed, full, world.SLUG, NOTE).code == "approved"


def test_a_grown_task_keeps_its_small_approval_and_takes_the_change(
    tmp_path: Path,
) -> None:
    grown = world.workspace(tmp_path / "grown")
    world.task(grown, night=date(2026, 11, 24))
    path = world.sheet(grown, world.SMALL)
    approve.approved(grown, world.SLUG, approve.Asked(by="alone", path=path))
    world.sheet(grown, world.FULL)
    held_since(
        grown,
        "the criteria wait for the owner: the small change is a full change",
        approved_before=True,
    )
    typed.typed(grown, world.SLUG, NOTE)
    said = change.changed(grown, world.SLUG, new_file(grown), NOTE)
    task = world.read(grown).task
    assert [one.change for one in said.pairs] == ["changed"]
    assert task.criteria.approvals[-1].size == "small"
