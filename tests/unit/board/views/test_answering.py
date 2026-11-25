"""The answer the board takes to a question: one note and one button for each option, Park and
Drop after their confirm step, and nothing where the page may not act (the ruling "The board
takes an answer with a note, never a conversation"; the act's refusal of a note with no option
is `board-acts`')."""

import dataclasses

from msgspec.structs import replace

from fakes.records import MOMENT
from lem.board.views import answering
from lem.records.questions import Question
from unit.board.views.small import VIEWER, world

ASKED = Question(
    id="breaker:gift-note:1:20261125T100000Z",
    topic="breaker",
    question="Breaker 1 of gift-note: help, park or drop the task?",
    options=("help", "park", "drop"),
    asked=MOMENT,
)


def test_an_answer_is_one_note_and_one_button_for_each_option() -> None:
    form = answering.form(world(), ASKED, "row", "waits")
    assert form is not None
    assert form.note.label == "Help needs your words for the lead"
    assert [(one.option, one.label, one.confirm) for one in form.choices] == [
        ("help", "Help", None),
        ("park", "Park…", "/studio/shop/tasks/gift-note/park"),
        ("drop", "Drop…", "/studio/shop/tasks/gift-note/drop"),
    ]
    assert [(one.name, one.shown) for one in form.fields] == [
        ("key", ASKED.id),
        ("in", "waits"),
    ]


def test_the_criteria_post_the_digest_the_page_showed_and_their_tab() -> None:
    asked = replace(
        ASKED,
        id="criterion:gift-note:20261125T100000Z",
        topic="criterion",
        question="Approve the criteria?",
        options=("yes", "no"),
        digest="5e2c8a90b1d4",
    )
    form = answering.form(world(), asked, "approve", tab="criteria")
    assert form is not None
    assert [(one.name, one.shown) for one in form.fields] == [
        ("key", asked.id),
        ("digest", "5e2c8a90b1d4"),
        ("tab", "criteria"),
    ]
    assert form.note.label == "No needs your words: what should the criteria say?"


def test_a_page_that_may_not_act_takes_no_answer() -> None:
    reader = replace(VIEWER, may_act=False)
    assert (
        answering.form(dataclasses.replace(world(), viewer=reader), ASKED, "row")
        is None
    )
