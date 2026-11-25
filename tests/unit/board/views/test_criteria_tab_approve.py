"""The owner's yes on the tab Criteria and decisions: the card of the criteria that wait for it,
with the change from his note and its pairs, his answer form where the page may act, the words
where it may not, and his answer on record until the task's session takes it."""

from dataclasses import replace as changed
from typing import TYPE_CHECKING

from msgspec.structs import replace

from fixtures.board.beside import STOCK_CRITERIA
from fixtures.board.held import STOCK_AGAIN, STOCK_NOTE
from fixtures.board.moments import BASE, ago
from lem.board.inputs.forms import Field
from lem.board.inputs.task.criteria import Pair, Side
from lem.board.views import owed
from lem.board.views.criteria.tab import criteria
from lem.model.criteria import digest
from lem.records.holds import OwnerHold
from lem.records.questions import Answer
from lem.records.work import Span
from unit.board.views.afternoon import world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.views.world import Seen, World

STOCK = "stock-on-product-page"


def again(found: World, seen: Seen) -> World:
    """The world with the task `seen` in the place of its own."""
    slug = seen.record.task.slug
    tasks = tuple(
        seen if each.record.task.slug == slug else each for each in found.tasks
    )
    return changed(found, tasks=tasks)


def held(seen: Seen, hold: OwnerHold | None, *spans: Span) -> Seen:
    """The task under another hold of the owner's, with other spans."""
    task = replace(seen.record.task, hold=hold, spans=spans or seen.record.task.spans)
    return replace(seen, record=replace(seen.record, task=task))


def test_the_criteria_changed_from_his_note_wait_for_his_yes_again(
    tmp_path: Path,
) -> None:
    found = world(tmp_path)
    seen = owed.seen(found, STOCK)
    shown = digest.shown(STOCK_CRITERIA.encode())
    questions = tuple(
        replace(one, digest=shown) if one.id == STOCK_AGAIN else one
        for one in seen.record.task.questions
    )
    task = replace(seen.record.task, questions=questions)
    seen = replace(seen, record=replace(seen.record, task=task))
    tab = criteria(again(found, seen), seen)
    card = tab.approve
    assert card is not None
    assert (card.label, card.head) == (
        "Approve the criteria",
        "The criteria wait for your yes",
    )
    assert card.read == (
        "The personas flagged 1 of 2 criteria: read the flagged one before you approve."
    )
    assert card.change is not None
    assert card.change.said.startswith(
        f"Lem changed them from your note “{STOCK_NOTE}”."
    )
    assert card.change.pairs == (
        Pair(
            change="changed",
            sides=(
                Side(
                    label="Before · criterion 1",
                    text='A product with 3 in stock says "3 left" under its price.',
                ),
                Side(
                    label="Now · criterion 1",
                    text=(
                        'A product with 3 in stock says "3 left" under its price, and one '
                        'with 1 in stock says "Only 1 left" in the warning color: the blue '
                        'mug, with 1 in stock, says "Only 1 left".'
                    ),
                ),
            ),
        ),
    )
    assert card.criteria and card.criteria.text == STOCK_CRITERIA
    assert card.plain == STOCK_CRITERIA
    assert card.answer is not None
    assert card.answer.action == f"{BASE}/tasks/{STOCK}/answer"
    assert card.answer.question == "Approve the criteria?"
    assert card.answer.fields == (
        Field(name="key", shown=STOCK_AGAIN),
        Field(name="digest", shown=shown),
        Field(name="tab", shown="criteria"),
    )
    assert [choice.option for choice in card.answer.choices] == ["yes", "no"]
    assert (
        card.answer.note.label == "No needs your words: what should the criteria say?"
    )
    assert card.sheet and card.back and card.back.href == f"{BASE}/tasks/{STOCK}"
    assert card.words is None


def test_a_page_that_may_not_act_says_where_he_approves_them(tmp_path: Path) -> None:
    found = world(tmp_path)
    away = changed(found, viewer=replace(found.viewer, may_act=False, local=False))
    card = criteria(away, owed.seen(away, STOCK)).approve
    assert card is not None
    assert card.answer is None
    assert not card.sheet
    assert card.words == (
        "Approve them in the task’s session, or on this board on the Mac or through the "
        "tailnet door."
    )


def test_his_answer_on_record_waits_for_the_task_s_session(tmp_path: Path) -> None:
    found = world(tmp_path)
    seen = owed.seen(found, STOCK)
    answer = Answer(
        option="yes", label="Yes", source="board", device="phone", at=ago(2)
    )
    questions = tuple(
        replace(one, answer=answer) if one.id == STOCK_AGAIN else one
        for one in seen.record.task.questions
    )
    task = replace(seen.record.task, questions=questions)
    answered = replace(seen, record=replace(seen.record, task=task))
    card = criteria(again(found, answered), answered).approve
    assert card is not None
    assert card.answer is None
    assert card.took == (
        "Your answer is on record: the task’s session takes it. You picked Yes on "
        "“Approve the criteria?” at 15:58, from the phone."
    )


def test_his_yes_is_offered_for_criteria_and_for_an_interview_only_once_its_read_is_in(
    tmp_path: Path,
) -> None:
    """`main`'s test_board_model.Acts.test_his_yes_is_offered_for_criteria_and_for_an_interview_only_once_its_read_is_in:
    the card is there while the criteria wait (a held block of the criteria), not while the
    interview runs, and not after it ended until the personas' read is in; nor once the
    criteria are approved (the hold is gone)."""
    found = world(tmp_path)
    seen = owed.seen(found, STOCK)
    since = ago(31)
    interview = OwnerHold(
        on="interview", line="the interview waits for the owner", since=since
    )
    scout = Span(name="scout", start=ago(30.5), end=ago(28))

    def offered(each: Seen) -> bool:
        return criteria(again(found, each), each).approve is not None

    assert offered(seen)
    running = held(seen, interview, scout, Span(name="interview", start=ago(30)))
    assert not offered(running)
    ended = Span(name="interview", start=ago(30), end=ago(22))
    unread = held(seen, interview, scout, ended)
    criteria_of = replace(unread.record.task.criteria, reads=())
    unread = replace(
        unread,
        record=replace(
            unread.record, task=replace(unread.record.task, criteria=criteria_of)
        ),
    )
    assert not offered(unread)
    assert offered(held(seen, interview, scout, ended))
    assert not offered(held(seen, None))
