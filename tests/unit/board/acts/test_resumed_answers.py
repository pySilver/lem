"""A form answers the wait it showed, even across a park or two breakers in one second."""

from datetime import timedelta
from functools import partial
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import replace

from fakes.command import lem
from lem.app.tasks import park, resume, shown_answer
from lem.board.acts import asking
from lem.board.views.panel import held_head
from lem.kernel import clock
from lem.model.criteria import digest, waits
from lem.model.decisions import breaker, log
from lem.model.owner import held, hold_question
from lem.records.decisions import Breaker
from lem.records.holds import BreakerHold, OwnerHold
from lem.store import tasks
from unit.board.acts.acts import SLUG, made, note_of, opened, read
from unit.board.acts.conftest import PHONE
from unit.board.acts.test_answer import ANSWER, HELP, SINCE
from unit.criteria import world
from unit.task.spaces import refusal, result

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.holds import OwnerWait
    from lem.records.questions import Question
    from lem.records.task import Status, Task
    from unit.board.acts.conftest import Board


def current(board: Board) -> Question:
    """The question whose id the current form carries."""
    question = asking.standing(read(board).task)
    assert question is not None
    return question


def test_the_board_and_task_use_the_same_pending_answer_rule(
    board: Board,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = made(board, status="building", hold=BreakerHold(number=1, since=SINCE))
    seen: list[Task] = []

    def pending(task: Task) -> None:
        seen.append(task)

    monkeypatch.setattr(hold_question, "pending_answer", pending)
    assert shown_answer.pending(record) is None
    assert (
        held_head.breaker(record.task, working=False)
        == "The build stopped: its breaker waits for you"
    )
    assert seen == [record.task, record.task]


def test_the_phone_approval_wake_keeps_the_note_under_its_question_key(
    board: Board,
) -> None:
    made(board, status="shaping", hold=world.WAITS)
    session = opened(board)
    mark = digest.shown(world.sheet(board.checkout, world.FULL).read_bytes())
    key = current(board).id
    fields = {"key": key, "option": "yes", "digest": mark, "words": HELP}
    assert note_of(board.post(ANSWER, fields, **{"user-agent": PHONE})).state == "done"
    assert (session, f"lem: {SLUG} owner") in board.terminal.told
    approved = read(board)
    assert approved.task.hold is None
    shown = result(lem("task", "show", SLUG, cwd=board.checkout))["board_answer"]
    assert (shown["key"], shown["option"], shown["note"]) == (key, "yes", HELP)
    assert (shown["source"], shown["via"], shown["device"]) == (
        "board",
        "local",
        "phone",
    )

    tasks.update(
        board.state,
        SLUG,
        lambda record: replace(
            record,
            task=replace(
                record.task,
                hold=OwnerHold(on="fact", line="the owner waits", since=SINCE),
            ),
        ),
        approved.revision,
    )
    assert (
        result(lem("task", "show", SLUG, cwd=board.checkout)).get("board_answer")
        is None
    )
    saved = next(
        question for question in read(board).task.questions if question.id == key
    )
    assert saved.answer is not None
    assert (saved.answer.note, saved.answer.device) == (HELP, "phone")


@pytest.mark.parametrize(
    ("on", "status", "option"),
    (
        ("plan", "planned", "drop"),
        ("criteria", "shaping", "no"),
        ("skip-read", "shaping", "yes"),
    ),
)
@pytest.mark.parametrize("minutes", (0, 2))
def test_resume_refuses_the_old_form_and_keeps_the_criteria_digest(
    board: Board,
    monkeypatch: pytest.MonkeyPatch,
    on: OwnerWait,
    status: Status,
    option: str,
    minutes: int,
) -> None:
    record = made(
        board, status=status, hold=OwnerHold(on=on, line="the owner waits", since=SINCE)
    )
    fields = {"option": option, "confirm": "yes", "words": HELP}
    if on == "criteria":
        path = world.sheet(board.checkout, world.FULL)
        shown = digest.shown(path.read_bytes())
        fields["digest"] = shown
        tasks.update(
            board.state,
            SLUG,
            lambda record: replace(
                record, task=waits.asked(record.task, SINCE, "the criteria wait", shown)
            ),
            record.revision,
        )
    first = current(board)
    monkeypatch.setattr(
        clock, "now", lambda: SINCE + timedelta(minutes=min(minutes, 1))
    )
    park.parked(board.checkout, SLUG, "later")
    monkeypatch.setattr(clock, "now", lambda: SINCE + timedelta(minutes=minutes))
    resume.resumed(board.checkout, SLUG)
    resumed = read(board)
    assert note_of(board.post(ANSWER, {**fields, "key": first.id})).state == "refused"
    assert read(board) == resumed
    fresh = current(board)
    assert fresh.id != first.id
    assert fresh.digest == first.digest
    assert note_of(board.post(ANSWER, {**fields, "key": fresh.id})).state == "done"
    if on == "criteria":
        assert first in read(board).task.questions


def test_the_first_answer_to_resumed_criteria_keeps_the_digest(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    made(board, status="shaping", hold=world.WAITS)
    path = world.sheet(board.checkout, world.FULL)
    shown = digest.shown(path.read_bytes())
    monkeypatch.setattr(clock, "now", lambda: SINCE)
    park.parked(board.checkout, SLUG, "later")
    resume.resumed(board.checkout, SLUG)
    key = current(board).id
    fields = {"key": key, "option": "no", "words": HELP, "digest": shown}
    assert note_of(board.post(ANSWER, fields)).state == "done"
    saved = current(board)
    assert (saved.id, saved.digest) == (key, shown)
    assert saved.answer is not None
    park.parked(board.checkout, SLUG, "later")
    resume.resumed(board.checkout, SLUG)
    fresh = current(board)
    assert (fresh.digest, fresh.answer) == (shown, None)
    assert fresh.id != key
    assert saved in read(board).task.questions


def trip(board: Board, number: int, at: datetime) -> None:
    """Trip a breaker with its decision number at the fixed moment."""
    decision = Breaker(
        id=number,
        at=at,
        cause="criteria",
        what="the export needs a choice",
        document=f"breaker-{number}.md",
        handoff="handoff.md",
    )
    change = partial(
        breaker.tripped, breaker=decision, why="the note must stay", now=at
    )
    tasks.update(board.state, SLUG, change, read(board).revision)


def test_help_without_a_decision_asks_again_under_a_new_board_key(board: Board) -> None:
    """Main's breaker stage: Help without a decision puts the same breaker back on the board."""
    made(board, status="building")
    trip(board, 1, SINCE)
    original = current(board)
    fields = {"key": original.id, "option": "help", "words": HELP}
    assert note_of(board.post(ANSWER, fields)).state == "done"
    answered = current(board)
    before = read(board)
    hold = before.task.hold
    assert isinstance(hold, BreakerHold)
    assert held.breaker_rows(before.task, hold) == ()
    shown = result(lem("task", "show", SLUG, cwd=board.checkout))["board_answer"]
    assert (shown["key"], shown["option"], shown["note"]) == (original.id, "help", HELP)

    again = ("decisions", "reask", SLUG, "--question", shown["key"], "--line", HELP)
    fresh = result(lem(*again, cwd=board.checkout))
    updated = read(board)
    new_hold = updated.task.hold
    assert isinstance(new_hold, BreakerHold) and new_hold.number == hold.number
    assert fresh["id"] == current(board).id != original.id
    assert fresh["options"] == ["help", "park", "drop"]
    assert answered in updated.task.questions
    assert updated.task.decisions == before.task.decisions
    assert held.breaker_rows(updated.task, new_hold)
    assert (
        result(lem("task", "show", SLUG, cwd=board.checkout)).get("board_answer")
        is None
    )

    assert refusal(lem(*again, cwd=board.checkout))["code"] == "breaker-question"
    assert note_of(board.post(ANSWER, fields)).state == "refused"
    assert read(board) == updated
    assert note_of(board.post(ANSWER, {**fields, "key": fresh["id"]})).state == "done"


@pytest.mark.parametrize("board_help", (False, True))
def test_a_same_second_breaker_refuses_the_prior_breakers_form(
    board: Board, monkeypatch: pytest.MonkeyPatch, *, board_help: bool
) -> None:
    now = SINCE + timedelta(minutes=2)
    made(board, status="building")
    trip(board, 1, SINCE)
    monkeypatch.setattr(clock, "now", lambda: SINCE + timedelta(minutes=1))
    park.parked(board.checkout, SLUG, "later")
    monkeypatch.setattr(clock, "now", lambda: now)
    resume.resumed(board.checkout, SLUG)
    old = current(board)
    if board_help:
        fields = {"key": old.id, "option": "help", "words": HELP}
        assert note_of(board.post(ANSWER, fields)).state == "done"
    help_given = log.Logged(
        what="the export", chose="keep the note", why=HELP, by="owner", breaker=1
    )
    change = partial(log.logged, asked=help_given, now=now)
    tasks.update(board.state, SLUG, change, read(board).revision)
    trip(board, 3, now)
    record = read(board)
    fields = {"option": "drop", "confirm": "yes"}
    assert note_of(board.post(ANSWER, {**fields, "key": old.id})).state == "refused"
    assert read(board) == record
    hold = record.task.hold
    assert isinstance(hold, BreakerHold)
    assert [row.key for row in held.breaker_rows(record.task, hold)] == [
        f"breaker:{SLUG}:3"
    ]
    fresh = f"breaker:{SLUG}:3:{clock.compact(now)}"
    assert current(board).id == fresh
    assert note_of(board.post(ANSWER, {**fields, "key": fresh})).state == "done"
