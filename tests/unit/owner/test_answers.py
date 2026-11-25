"""His answer to a question of a task: the first answer counts, and an answer to a question asked
again or to a text that changed is refused (`main`: `answers.py`, `test_board_answers`)."""

from datetime import timedelta

import pytest
from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.kernel.errors import Refusal
from lem.model.owner import answers, waiting
from lem.model.owner.looks import Look
from lem.records.holds import OwnerHold
from lem.records.questions import Answer, Question

ASKED = Question(
    id="plan-1",
    topic="plan",
    question="Build the plan?",
    options=("build", "drop"),
    digest="d1",
    asked=MOMENT,
)
YES = Answer(option="build", label="Build", source="board", at=MOMENT)


def test_the_first_answer_counts() -> None:
    task = record(questions=(ASKED,)).task
    answered = answers.answer(task, "plan-1", "d1", YES)
    assert answered.questions[-1].answer == YES
    with pytest.raises(Refusal) as caught:
        answers.answer(answered, "plan-1", "d1", replace(YES, option="drop"))
    assert "the first answer counts" in caught.value.why


def test_an_invalid_criterion_option_leaves_the_row_open() -> None:
    question = replace(
        ASKED, id="criterion-1", topic="criterion", options=("yes", "no")
    )
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


@pytest.mark.parametrize("minutes", [0, 1])
def test_an_answer_to_a_question_asked_again_is_refused(minutes: int) -> None:
    again = replace(ASKED, id="plan-2", asked=MOMENT + timedelta(minutes=minutes))
    task = record(questions=(ASKED, again)).task
    with pytest.raises(Refusal) as caught:
        answers.answer(task, "plan-1", "d1", YES)
    assert caught.value.why == "plan-1 was asked again as plan-2"


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
        answers.answer(task, "plan-1", "d2", YES)
    assert "changed after the owner saw it" in caught.value.why


def test_an_answer_to_no_question_of_the_task_is_refused() -> None:
    with pytest.raises(Refusal) as caught:
        answers.answer(record().task, "plan-9", None, YES)
    assert caught.value.code == "question"
