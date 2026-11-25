"""His answer to a question of a task: the first answer counts, and an answer to a question asked
again or to a text that changed is refused (`main`: `answers.py`, `test_board_answers`)."""

from datetime import timedelta

import pytest
from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.kernel.errors import Refusal
from lem.model.owner import answers, waiting
from lem.model.owner.looks import Look
from lem.records.holds import Blocked, BreakerHold, OwnerHold, Parked
from lem.records.questions import Answer, Question

ASKED = Question(
    id="plan:fix-the-login:20261125T100000Z",
    topic="plan",
    question="Build the plan?",
    options=("build", "drop"),
    digest="d1",
    asked=MOMENT,
)
YES = Answer(option="build", label="Build", source="board", at=MOMENT)
PLAN_HOLD = OwnerHold(on="plan", line="read the plan", since=MOMENT)
CRITERIA_HOLD = OwnerHold(on="criteria", line="approve the criteria", since=MOMENT)
CRITERIA = replace(
    ASKED,
    id="criterion:fix-the-login:20261125T100000Z",
    topic="criterion",
    options=("yes", "no"),
)
BREAKER = replace(
    ASKED,
    id="breaker:fix-the-login:2:20261125T100000Z",
    topic="breaker",
    options=("help", "park", "drop"),
)


def test_the_first_answer_counts() -> None:
    task = record(status="planned", hold=PLAN_HOLD, questions=(ASKED,)).task
    answered = answers.answer(task, ASKED.id, "d1", YES)
    assert answered.questions[-1].answer == YES
    with pytest.raises(Refusal) as caught:
        answers.answer(answered, ASKED.id, "d1", replace(YES, option="drop"))
    assert "the first answer counts" in caught.value.why


def test_an_invalid_criterion_option_leaves_the_row_open() -> None:
    question = CRITERIA
    before = record(
        status="shaping",
        hold=OwnerHold(on="criteria", line="approve the criteria", since=MOMENT),
        questions=(question,),
    )
    with pytest.raises(Refusal) as caught:
        answers.answer(
            before.task, question.id, question.digest, replace(YES, option="later")
        )
    assert caught.value.code == "option"
    assert "yes, no" in caught.value.fix
    assert before.task.questions[0].answer is None
    found = waiting.rows((Look(record=before),), away=False, now=MOMENT)
    assert [row.kind for row in found] == ["criteria"]


@pytest.mark.parametrize(
    ("question", "hold", "status", "option", "blank"),
    [
        (CRITERIA, CRITERIA_HOLD, "shaping", "no", None),
        (BREAKER, BreakerHold(number=2, since=MOMENT), "building", "help", "   "),
    ],
    ids=("criterion-no", "breaker-help"),
)
def test_a_wordless_answer_leaves_its_question_open(
    question: Question,
    hold: OwnerHold | BreakerHold,
    status: str,
    option: str,
    blank: str | None,
) -> None:
    before = record(status=status, hold=hold, questions=(question,))
    given = replace(YES, option=option, note=blank)
    with pytest.raises(Refusal) as caught:
        answers.answer(before.task, question.id, question.digest, given)
    assert caught.value.code == "note"
    assert waiting.rows((Look(record=before),), away=False, now=MOMENT)
    corrected = replace(given, note="Keep the hardware key requirement.")
    after = answers.answer(before.task, question.id, question.digest, corrected)
    assert after.questions[0].answer == corrected


@pytest.mark.parametrize(
    ("status", "hold"),
    [
        ("shaping", Parked(since=MOMENT, words="later")),
        ("dropped", None),
        ("shaping", Blocked(since=MOMENT, why="blocked", fix="read the stop")),
        ("shaping", replace(CRITERIA_HOLD, since=MOMENT + timedelta(seconds=1))),
    ],
    ids=("parked", "dropped", "blocked", "earlier-hold"),
)
def test_an_old_page_cannot_answer_a_question_that_no_longer_waits(
    status: str, hold: Parked | Blocked | OwnerHold | None
) -> None:
    task = record(status=status, hold=hold, questions=(CRITERIA,)).task
    with pytest.raises(Refusal) as caught:
        answers.answer(task, CRITERIA.id, CRITERIA.digest, replace(YES, option="yes"))
    assert caught.value.code == "question"


@pytest.mark.parametrize("minutes", [0, 1])
def test_an_answer_to_a_question_asked_again_is_refused(minutes: int) -> None:
    again = replace(ASKED, id="plan-2", asked=MOMENT + timedelta(minutes=minutes))
    task = record(questions=(ASKED, again)).task
    with pytest.raises(Refusal) as caught:
        answers.answer(task, ASKED.id, "d1", YES)
    assert caught.value.why == f"{ASKED.id} was asked again as {again.id}"


def test_a_plan_does_not_replace_a_breaker_question() -> None:
    task = record(status="planned", hold=PLAN_HOLD, questions=(BREAKER, ASKED)).task
    with pytest.raises(Refusal) as caught:
        answers.answer(task, BREAKER.id, BREAKER.digest, replace(YES, option="park"))
    assert caught.value.code == "question"
    assert caught.value.why == f"{BREAKER.id} no longer waits for the owner"


def test_two_open_cards_can_each_take_an_answer() -> None:
    first = replace(ASKED, id="card-1", topic="card")
    second = replace(first, id="card-2", asked=MOMENT + timedelta(minutes=1))
    task = record(questions=(first, second)).task
    answered = answers.answer(task, first.id, first.digest, YES)
    assert answered.questions == (replace(first, answer=YES), second)
    both = answers.answer(answered, second.id, second.digest, YES)
    assert both.questions == (replace(first, answer=YES), replace(second, answer=YES))


def test_an_answer_to_a_text_that_changed_is_refused() -> None:
    task = record(questions=(ASKED,)).task
    with pytest.raises(Refusal) as caught:
        answers.answer(task, ASKED.id, "d2", YES)
    assert "changed after the owner saw it" in caught.value.why


def test_an_answer_to_no_question_of_the_task_is_refused() -> None:
    with pytest.raises(Refusal) as caught:
        answers.answer(record().task, "plan-9", None, YES)
    assert caught.value.code == "question"
