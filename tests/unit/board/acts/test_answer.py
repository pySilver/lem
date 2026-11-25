"""The owner's answer from the board, through the server's app on fakes: a breaker's Help, Park
and Drop, a plan's Build, the skip of the persona read, and the criteria's Yes and No; the first
answer counts, and an answer whose question waits no more records nothing and says why."""

import threading
from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

from lem.app.criteria import typed
from lem.app.tasks import resume
from lem.board.acts import answer, asking, given
from lem.board.acts.asked import Asked
from lem.board.acts.asker import Asker
from lem.kernel import clock
from lem.model.criteria import digest, waits
from lem.records.holds import BreakerHold, OwnerHold, Parked
from lem.records.journal.task import OwnerAct
from unit.board.acts.acts import SLUG, made, note_of, opened, read
from unit.board.acts.conftest import PHONE
from unit.criteria import world

if TYPE_CHECKING:
    from datetime import datetime

    from unit.board.acts.conftest import Board

SINCE = world.EARLY
BREAKER = BreakerHold(number=1, since=SINCE)
KEY = f"breaker:{SLUG}:1:20260101T090000Z"
ANSWER = f"/tasks/{SLUG}/answer"
HELP = "keep the note in the last column"


def breaker(board: Board) -> None:
    """A task whose breaker 1 waits for the owner."""
    made(board, status="building", hold=BREAKER)


def test_criterion_6_help_needs_his_words_and_no_option_is_refused(
    board: Board,
) -> None:
    breaker(board)
    said = {
        "": "Pick an option first.",
        "help": "Help needs your words for the lead.",
        "yes": "takes Help, Park, Drop.",
    }
    for option, words in said.items():
        note = note_of(board.post(ANSWER, {"key": KEY, "option": option}))
        assert note.state == "refused"
        assert words in note.said
    assert read(board).task.questions == ()


def test_criterion_9_the_record_is_the_owners_with_the_question_option_note_time_and_device(
    board: Board,
) -> None:
    breaker(board)
    session = opened(board)
    fields = {"key": KEY, "option": "help", "words": f"  {HELP}  "}
    note = note_of(board.post(ANSWER, fields, **{"user-agent": PHONE}))
    assert note.state == "done"
    assert note.said.startswith(answer.ON_RECORD)
    assert "got word of it" in note.said
    record = read(board)
    (question,) = record.task.questions
    assert (question.id, question.topic) == (KEY, "breaker")
    said = question.answer
    assert said is not None
    assert (said.option, said.label, said.note) == ("help", "Help", HELP)
    assert (said.source, said.via, said.device, said.agent) == (
        "board",
        "local",
        "phone",
        PHONE,
    )
    assert question.took_effect is None
    acts = [one for one in record.journal if isinstance(one, OwnerAct)]
    assert [(one.act, one.question, one.option, one.via) for one in acts] == [
        ("answer", KEY, "help", "local")
    ]
    assert (session, f"lem: {SLUG} owner") in board.terminal.told


def test_criterion_6_only_the_first_answer_counts_and_a_later_one_says_what_took_effect(
    board: Board,
) -> None:
    breaker(board)
    board.post(ANSWER, {"key": KEY, "option": "help", "words": HELP})
    fields = {"key": KEY, "option": "drop", "confirm": "yes"}
    note = note_of(board.post(ANSWER, fields, **{"user-agent": PHONE}))
    assert note.state == "refused"
    assert "You picked Help for the breaker at" in note.said
    assert "the first answer counts" in note.said
    (question,) = read(board).task.questions
    assert question.answer is not None
    assert question.answer.option == "help"


def test_criterion_6_drop_asks_for_its_confirm_and_after_it_is_on_record(
    board: Board,
) -> None:
    breaker(board)
    plain = note_of(board.post(ANSWER, {"key": KEY, "option": "drop"}))
    assert plain.state == "refused"
    assert "Drop asks for a confirm first" in plain.said
    assert read(board).task.questions == ()
    fields = {"key": KEY, "option": "drop", "confirm": "yes", "words": "not now"}
    note = note_of(board.post(ANSWER, fields))
    assert "it drops the task as on /lem drop" in note.said
    (question,) = read(board).task.questions
    assert question.answer is not None
    assert (question.answer.option, question.answer.note) == ("drop", "not now")
    assert read(board).task.status == "building"


def test_a_park_puts_the_task_aside_and_a_later_drop_is_told_which_answer_won(
    board: Board,
) -> None:
    breaker(board)
    fields = {"key": KEY, "option": "park", "words": "wait for the export's owner"}
    note = note_of(board.post(ANSWER, fields))
    assert note.state == "done"
    assert note.said.startswith("The task is parked.")
    assert f"/lem resume {SLUG}" in note.said
    record = read(board)
    hold = record.task.hold
    assert isinstance(hold, Parked)
    assert hold.words == "wait for the export's owner"
    assert hold.held == BREAKER
    (question,) = record.task.questions
    assert question.answer is not None
    assert (question.id, question.answer.option) == (KEY, "park")
    acts = [one for one in record.journal if isinstance(one, OwnerAct)]
    assert [(one.act, one.option) for one in acts] == [("park", "park")]
    later = {"key": KEY, "option": "drop", "confirm": "yes"}
    refused = note_of(board.post(ANSWER, later))
    assert refused.state == "refused"
    assert "You picked Park for the breaker at" in refused.said


@pytest.mark.parametrize("resumed_at", (SINCE, SINCE + timedelta(minutes=1)))
def test_resume_issues_a_new_breaker_key_and_keeps_the_old_park(
    board: Board, monkeypatch: pytest.MonkeyPatch, resumed_at: datetime
) -> None:
    breaker(board)
    monkeypatch.setattr(clock, "now", lambda: SINCE)
    assert note_of(board.post(ANSWER, {"key": KEY, "option": "park"})).state == "done"
    monkeypatch.setattr(clock, "now", lambda: resumed_at)
    resume.resumed(board.checkout, SLUG)
    current = asking.standing(read(board).task)
    assert current is not None and current.id != KEY and current.answer is None
    fields = {"key": KEY, "option": "drop", "confirm": "yes"}
    old = note_of(board.post(ANSWER, fields))
    assert old.state == "refused"
    assert "You picked Park" in old.said
    fresh = note_of(board.post(ANSWER, {**fields, "key": current.id}))
    assert fresh.state == "done"


def test_drop_between_parks_first_check_and_its_write_wins_alone(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    breaker(board)
    parked = answer.parking.parked

    def after_drop(asked: Asked) -> str:
        drop = note_of(
            board.post(ANSWER, {"key": KEY, "option": "drop", "confirm": "yes"})
        )
        assert drop.state == "done"
        return parked(asked)

    monkeypatch.setattr(answer.parking, "parked", after_drop)
    note = note_of(board.post(ANSWER, {"key": KEY, "option": "park"}))
    assert note.state == "refused"
    assert "You picked Drop" in note.said
    record = read(board)
    assert record.task.hold == BREAKER
    assert record.revision == 2
    assert not (board.state / "tasks" / SLUG / "parked.json").exists()


def test_an_answer_to_an_earlier_breaker_says_the_wait_began_again(
    board: Board,
) -> None:
    again = BreakerHold(number=2, since=SINCE + timedelta(hours=1))
    made(board, status="building", hold=again)
    note = note_of(board.post(ANSWER, {"key": KEY, "option": "help", "words": HELP}))
    assert note.state == "refused"
    assert "waits again since" in note.said
    assert read(board).task.questions == ()


def test_a_key_that_no_longer_waits_says_what_holds_now_and_records_nothing(
    board: Board,
) -> None:
    made(board, status="building")
    note = note_of(board.post(ANSWER, {"key": KEY, "option": "help", "words": HELP}))
    assert note.state == "refused"
    assert "no longer waits: it is building since" in note.said
    assert read(board).task.questions == ()


def test_criterion_6_a_plan_takes_build_on_record_for_the_session(board: Board) -> None:
    hold = OwnerHold(on="plan", line="the plan waits for the owner", since=SINCE)
    made(board, status="planned", hold=hold)
    key = f"plan:{SLUG}:20260101T090000Z"
    note = note_of(board.post(ANSWER, {"key": key, "option": "build"}))
    assert "it builds the plan" in note.said
    (question,) = read(board).task.questions
    assert question.answer is not None
    assert (question.topic, question.answer.option) == ("plan", "build")


def test_criterion_7_the_skip_of_the_persona_read_takes_yes_and_no(
    board: Board,
) -> None:
    hold = OwnerHold(on="skip-read", line="skip the persona read?", since=SINCE)
    made(board, status="shaping", hold=hold)
    made(board, "other-task", status="shaping", hold=hold)
    key = f"skip:{SLUG}:20260101T090000Z"
    other = "skip:other-task:20260101T090000Z"
    yes = note_of(board.post(ANSWER, {"key": key, "option": "yes"}))
    no = note_of(board.post("/tasks/other-task/answer", {"key": other, "option": "no"}))
    assert "it takes your yes" in yes.said
    assert "it takes your no" in no.said
    picked = [
        read(board, slug).task.questions[0].answer for slug in (SLUG, "other-task")
    ]
    assert [one.option for one in picked if one is not None] == ["yes", "no"]


def criteria(board: Board) -> str:
    """A task whose criteria wait for the owner's yes, and the mark of their file."""
    made(board, status="shaping", hold=world.WAITS)
    path = world.sheet(board.checkout, world.FULL)
    return digest.shown(path.read_bytes())


def criteria_key() -> str:
    return f"criterion:{SLUG}:20260101T090000Z"


def test_criterion_3_a_no_with_no_note_is_refused_and_nothing_changes(
    board: Board,
) -> None:
    shown = criteria(board)
    fields = {"key": criteria_key(), "option": "no", "digest": shown}
    note = note_of(board.post(ANSWER, fields))
    assert "No needs your words" in note.said
    assert read(board).task.questions == ()


def test_criterion_2_a_no_with_his_note_is_on_record_with_the_text_he_read(
    board: Board,
) -> None:
    shown = criteria(board)
    stale = {"key": criteria_key(), "option": "no", "digest": "0" * 16, "words": "x"}
    assert (
        "changed since the page showed them" in note_of(board.post(ANSWER, stale)).said
    )
    fields = {
        "key": criteria_key(),
        "option": "no",
        "digest": shown,
        "words": "criterion 1 should also warn",
    }
    note = note_of(board.post(ANSWER, fields, **{"user-agent": PHONE}))
    assert "changes the criteria from your words" in note.said
    task = read(board).task
    no = waits.said_no(task)
    assert no is not None
    assert (no.note, no.device) == ("criterion 1 should also warn", "phone")
    question = waits.question_of(task)
    assert question is not None
    assert (question.id, question.digest) == (criteria_key(), shown)
    assert task.criteria.approvals == ()


def test_criterion_6_yes_approves_the_bytes_the_page_showed(board: Board) -> None:
    shown = criteria(board)
    stale = {"key": criteria_key(), "option": "yes", "digest": "0" * 16}
    assert note_of(board.post(ANSWER, stale)).state == "refused"
    fields = {"key": criteria_key(), "option": "yes", "digest": shown}
    note = note_of(board.post(ANSWER, fields))
    assert note.said.startswith("Your yes to the criteria is on record.")
    task = read(board).task
    (approval,) = task.criteria.approvals
    assert approval.by == "owner"
    assert task.hold is None
    acts = [one for one in read(board).journal if isinstance(one, OwnerAct)]
    assert [(one.act, one.option) for one in acts] == [("approve", "yes")]


def test_two_yes_requests_past_the_first_check_write_one_approval_and_answer(
    door: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    shown = criteria(door)
    fields = {"key": criteria_key(), "option": "yes", "digest": shown}
    approved = answer.approving.approved

    def after_first_yes(asked: Asked) -> str:
        monkeypatch.setattr(answer.approving, "approved", approved)
        first = door.client.post(
            f"{door.base}{ANSWER}",
            data={**fields, "words": HELP},
            headers={"user-agent": PHONE},
            follow_redirects=False,
        )
        assert note_of(first).state == "done"
        return approved(asked)

    monkeypatch.setattr(answer.approving, "approved", after_first_yes)
    note = note_of(
        door.client.post(f"{door.base}{ANSWER}", data=fields, follow_redirects=False)
    )
    assert note.state == "refused"
    assert "You picked Yes" in note.said
    record = read(door)
    (approval,) = record.task.criteria.approvals
    (question,) = record.task.questions
    assert (approval.by, question.id, question.digest) == (
        "owner",
        criteria_key(),
        shown,
    )
    said = question.answer
    assert said is not None
    assert (said.note, said.via, said.device, said.agent) == (
        HELP,
        "door",
        "phone",
        PHONE,
    )
    (entry,) = (one for one in record.journal if isinstance(one, OwnerAct))
    assert (entry.act, entry.question, record.revision) == ("approve", question.id, 2)


def test_his_typed_no_first_refuses_the_boards_yes_with_where_it_came_from(
    board: Board,
) -> None:
    shown = criteria(board)
    said = typed.typed(board.checkout, SLUG, "say what the column is called")
    fields = {"key": said.question, "option": "yes", "digest": shown}
    note = note_of(board.post(ANSWER, fields))
    assert note.state == "refused"
    assert "You picked No on “Approve the criteria?”" in note.said
    assert "in the task’s session" in note.said
    assert read(board).task.criteria.approvals == ()


def test_two_answers_at_once_record_one(board: Board) -> None:
    breaker(board)
    asker = Asker(via="local", device="computer")
    forms = (
        given.Given(key=KEY, option="help", words=HELP),
        given.Given(key=KEY, option="drop", confirm="yes"),
    )
    notes: list[str] = []
    asks = [
        Asked(
            checkout=board.checkout, slug=SLUG, given=one, asker=asker, now=clock.now()
        )
        for one in forms
    ]
    threads = [
        threading.Thread(
            target=lambda one=one: notes.append(answer.answered(one).state)
        )
        for one in asks
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(notes) == ["done", "refused"]
    (question,) = read(board).task.questions
    assert question.answer is not None


def test_through_the_door_the_answer_is_his_with_where_he_asked_and_never_his_login(
    door: Board,
) -> None:
    breaker(door)
    fields = {"key": KEY, "option": "help", "words": HELP}
    response = door.client.post(
        f"{door.base}{ANSWER}", data=fields, follow_redirects=False
    )
    note = note_of(response)
    assert note.state == "done"
    (question,) = read(door).task.questions
    assert question.answer is not None
    assert question.answer.via == "door"


def test_the_page_after_the_answer_is_the_tab_and_the_view_the_form_came_from(
    board: Board,
) -> None:
    breaker(board)
    fields = {
        "key": KEY,
        "option": "help",
        "words": HELP,
        "in": "waits",
        "tab": "criteria",
    }
    location = board.post(ANSWER, fields).headers["location"]
    assert location.startswith(f"{board.base}/tasks/{SLUG}/criteria?in=waits&note=")
    other = board.post(ANSWER, {"key": KEY, "option": "help", "in": "elsewhere"})
    assert "in=" not in other.headers["location"]


def test_a_plans_drop_asks_for_its_confirm_too(board: Board) -> None:
    hold = OwnerHold(on="plan", line="the plan waits for the owner", since=SINCE)
    made(board, status="planned", hold=hold)
    key = f"plan:{SLUG}:20260101T090000Z"
    plain = note_of(board.post(ANSWER, {"key": key, "option": "drop"}))
    assert "Drop asks for a confirm first" in plain.said
    note = note_of(board.post(ANSWER, {"key": key, "option": "drop", "confirm": "yes"}))
    assert "it drops the task as on /lem drop" in note.said
    (question,) = read(board).task.questions
    assert question.answer is not None
    assert question.answer.option == "drop"


def test_a_park_the_task_rules_refuse_records_nothing(board: Board) -> None:
    made(board, status="dropped", hold=BREAKER)
    note = note_of(board.post(ANSWER, {"key": KEY, "option": "park"}))
    assert note.state == "refused"
    assert "an ended task stays ended" in note.said
    record = read(board)
    assert record.task.hold == BREAKER
    assert record.task.questions == ()
    assert not [one for one in record.journal if isinstance(one, OwnerAct)]


def test_a_yes_whose_approval_refuses_records_nothing(board: Board) -> None:
    made(board, status="shaping", hold=world.WAITS)
    tested = world.FULL.replace("row.\n", "row.\n" + world.TESTED)
    path = world.sheet(board.checkout, tested)
    shown = digest.shown(path.read_bytes())
    fields = {"key": criteria_key(), "option": "yes", "digest": shown}
    note = note_of(board.post(ANSWER, fields))
    assert note.state == "refused"
    task = read(board).task
    assert (task.criteria.approvals, task.questions, task.hold) == ((), (), world.WAITS)


def test_through_the_door_his_yes_is_his_approval_with_where_he_asked(
    door: Board,
) -> None:
    made(door, status="shaping", hold=world.WAITS)
    path = world.sheet(door.checkout, world.FULL)
    fields = {
        "key": criteria_key(),
        "option": "yes",
        "digest": digest.shown(path.read_bytes()),
    }
    response = door.client.post(
        f"{door.base}{ANSWER}", data=fields, follow_redirects=False
    )
    assert note_of(response).said.startswith("Your yes to the criteria is on record.")
    record = read(door)
    (approval,) = record.task.criteria.approvals
    assert approval.by == "owner"
    acts = [one for one in record.journal if isinstance(one, OwnerAct)]
    assert [(one.act, one.via) for one in acts] == [("approve", "door")]
