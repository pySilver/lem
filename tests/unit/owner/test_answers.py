"""His answer to a question of a task: the first answer counts, and an answer to a question asked
again or to a text that changed is refused (`main`: `answers.py`, `test_board_answers`)."""

from datetime import timedelta

import pytest
from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.kernel.errors import Refusal
from lem.model.owner import answers
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


def test_an_answer_to_a_question_asked_again_is_refused() -> None:
    again = replace(ASKED, id="plan-2", asked=MOMENT + timedelta(minutes=1))
    task = record(questions=(ASKED, again)).task
    with pytest.raises(Refusal) as caught:
        answers.answer(task, "plan-1", "d1", YES)
    assert caught.value.why == "plan-1 was asked again as plan-2"


def test_an_answer_to_a_text_that_changed_is_refused() -> None:
    task = record(questions=(ASKED,)).task
    with pytest.raises(Refusal) as caught:
        answers.answer(task, "plan-1", "d2", YES)
    assert "changed after the owner saw it" in caught.value.why


def test_an_answer_to_no_question_of_the_task_is_refused() -> None:
    with pytest.raises(Refusal) as caught:
        answers.answer(record().task, "plan-9", None, YES)
    assert caught.value.code == "question"
