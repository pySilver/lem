"""The pure parts of the owner's acts: the question each wait asks and its id, the words of what
took effect, the name of a new task, the form's note, a refusal as a line, and the notes kept by
token."""

from datetime import timedelta
from typing import TYPE_CHECKING

from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.board.acts import asking, effect, slugs
from lem.board.acts.asked import line_of
from lem.board.acts.given import NOTE_CHARS, Given
from lem.board.acts.notes import Note, Notes
from lem.kernel.errors import Refusal
from lem.model.criteria import waits
from lem.model.task import claim
from lem.records.holds import Blocked, BreakerHold, OwnerHold, Parked
from lem.records.questions import Answer, Question

if TYPE_CHECKING:
    from lem.records.holds import Hold, OwnerWait
    from lem.records.task import Task

STAMP = "20261125T100000Z"


def held(hold: Hold | None, **fields: object) -> Task:
    """A task of `fields` under `hold`."""
    return record("gift-note", hold=hold, **fields).task


def owner(on: OwnerWait) -> OwnerHold:
    return OwnerHold(on=on, line="waits for the owner", since=MOMENT)


def test_each_wait_the_board_answers_asks_its_question_with_an_id_of_the_wait() -> None:
    found = {
        "breaker": held(BreakerHold(number=2, since=MOMENT), status="building"),
        "plan": held(owner("plan"), status="planned"),
        "skip": held(owner("skip-read"), status="shaping"),
        "criterion": held(owner("criteria"), status="shaping"),
    }
    asked = {topic: asking.standing(task) for topic, task in found.items()}
    assert {topic: one.id for topic, one in asked.items() if one} == {
        "breaker": f"breaker:gift-note:2:{STAMP}",
        "plan": f"plan:gift-note:{STAMP}",
        "skip": f"skip:gift-note:{STAMP}",
        "criterion": f"criterion:gift-note:{STAMP}",
    }
    options = {topic: one.options for topic, one in asked.items() if one}
    assert options == {
        "breaker": ("help", "park", "drop"),
        "plan": ("build", "drop"),
        "skip": ("yes", "no"),
        "criterion": ("yes", "no"),
    }
    breaker = asked["breaker"]
    assert breaker is not None
    assert breaker.question == "Breaker 2 of gift-note: help, park or drop the task?"


def test_no_question_waits_on_the_board_for_another_hold_or_none() -> None:
    for task in (
        held(None, status="building"),
        held(owner("fact"), status="shaping"),
        held(owner("plan"), status="building"),
        held(Parked(since=MOMENT), status="building"),
        held(Blocked(why="red", fix="mend", since=MOMENT), status="landing"),
    ):
        assert asking.standing(task) is None


def test_the_records_question_asked_since_the_wait_began_is_the_one_that_waits() -> (
    None
):
    old = Question(
        id="criterion-1-old",
        topic="criterion",
        question=waits.QUESTION,
        options=("yes", "no"),
        asked=MOMENT - timedelta(hours=1),
    )
    new = replace(old, id="criterion-2-new", asked=MOMENT, digest="d" * 16)
    task = held(owner("criteria"), status="shaping", questions=(old,))
    derived = asking.standing(task)
    assert derived is not None
    assert derived.id == f"criterion:gift-note:{STAMP}"
    task = held(owner("criteria"), status="shaping", questions=(old, new))
    assert asking.standing(task) == new


def test_what_took_effect_says_the_option_the_wait_the_time_and_where() -> None:
    question = Question(
        id="breaker:gift-note:1:x",
        topic="breaker",
        question="Breaker 1 of gift-note: help, park or drop the task?",
        options=("help", "park", "drop"),
        asked=MOMENT,
    )
    phone = Answer(
        option="drop", label="Drop", source="board", device="phone", at=MOMENT
    )
    typed = Answer(option="no", label="No", source="session", at=MOMENT)
    clock = effect.hhmm(MOMENT)
    assert effect.took_effect(question, phone) == (
        f"You picked Drop for the breaker at {clock}, from the phone"
    )
    criteria = replace(question, topic="criterion", question=waits.QUESTION)
    assert effect.took_effect(criteria, typed) == (
        f"You picked No on “Approve the criteria?” at {clock}, in the task’s session"
    )


def test_a_task_is_named_by_five_plain_words_and_an_item_by_its_stem() -> None:
    assert (
        slugs.slug_of("Add the gift note to the CSV export!") == "add-the-gift-note-to"
    )
    assert slugs.slug_of("¿¡ —") == ""
    ended = record("the-item", status="dropped")
    taken = record("the-item-2", status="landed")
    path = ".lem/state/backlog/the-item.md"
    assert slugs.item_slug(path, ()) == "the-item"
    assert slugs.item_slug(path, (ended,)) == "the-item-2"
    assert slugs.item_slug(path, (ended, taken)) == "the-item-3"
    assert slugs.item_slug("docs/backlog/The Receipt's Total.md", ()) == (
        "the-receipt-s-total"
    )
    holding = record("x", status="queued", backlog_item=path)
    assert claim.item_holder(path, (holding,)) == holding.task
    assert (
        claim.item_holder(
            path, (replace(holding, task=replace(holding.task, status="landed")),)
        )
        is None
    )


def test_the_note_is_his_words_on_one_line_and_at_most_the_box_holds() -> None:
    assert Given(words="  keep\n the   column \t").note == "keep the column"
    assert len(Given(words="w " * NOTE_CHARS).note) == NOTE_CHARS


def test_a_refusal_is_one_line_of_the_note() -> None:
    assert line_of(
        Refusal("x", "Pick an option first. Nothing was recorded.", "f")
    ) == ("Pick an option first. Nothing was recorded.")
    assert line_of(
        Refusal("no-task", "no task x here", "lem task list names the tasks")
    ) == ("No task x here: lem task list names the tasks.")


def test_a_note_is_kept_by_its_token_changed_in_place_and_one_merge_runs_for_a_task() -> (
    None
):
    notes = Notes()
    token = notes.put(Note(task="t", act="answer", state="done", said="on record"))
    assert notes.get(token) == Note(
        task="t", act="answer", state="done", said="on record"
    )
    assert notes.get("nothing") is None
    running = Note(task="t", act="merge", state="running", said="merging")
    first, new = notes.started(("/repo", "t"), running)
    second, again = notes.started(("/repo", "t"), running)
    assert (new, again, second) == (True, False, first)
    notes.change(first, "done", "merged")
    assert notes.get(first) == replace(running, state="done", said="merged")
    notes.ended(("/repo", "t"))
    assert notes.running(("/repo", "t")) is None
