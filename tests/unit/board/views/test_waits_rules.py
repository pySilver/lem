"""The rules of Waits for you, case by case (`main`'s `tests/unit/test_board_model.py`:
`WaitStacks`, `AnsweredInSession`, `Breakers`): the stacks by task, the rows whose verb goes to
the task's own session, and the parked tasks apart."""

from datetime import timedelta
from typing import TYPE_CHECKING

from msgspec.structs import replace

from fakes.records import MOMENT
from lem.app.sessions.acts import Open
from lem.board.views.waits import view
from lem.model.owner.looks import Session
from lem.records.decisions import Breaker
from lem.records.holds import Blocked, BreakerHold, OwnerHold, Parked
from lem.records.landing.merge import Refused
from lem.records.landing.propose import MergeRead, Proposed
from lem.records.landing.record import Landing, Pull
from lem.records.questions import Question
from unit.board.views.small import gone, task, world

if TYPE_CHECKING:
    from lem.board.inputs.waits import Wait
    from lem.board.views.world import Seen

TIP = "a" * 40
BASE = "b" * 40
OPENED = Open(at=MOMENT, session="S1", name="gift-note", phase="build", why="new")
INTERVIEW = OwnerHold(
    on="interview", line="the interview waits for the owner", since=MOMENT
)


def calling(slug: str, number: int, minutes: float) -> Seen:
    """An open pull request `number`, proposed `minutes` after the moment, whose merge review
    calls the owner a minute later."""
    at = MOMENT + timedelta(minutes=minutes)
    pull = Pull(
        number=number, url=f"https://github.com/acme/shop/pull/{number}", title="x"
    )
    read = MergeRead(
        tip=TIP,
        base=BASE,
        base_tree=BASE,
        verdict="call",
        why="Verdict: call. It is careful.",
        at=at + timedelta(minutes=1),
    )
    landing = Landing(
        phase="open",
        pull=pull,
        proposed=Proposed(tip=TIP, base=BASE, green=True, who_acts="owner", at=at),
        reads=(read,),
    )
    made = task(slug, f"pull request {pull.url}", status="open", since=at)
    return replace(made, record=replace(made.record, landing=landing))


def groups(*tasks: Seen) -> list[tuple[str, list[str]]]:
    """Each stack of Waits for you: its task, and the ids of its rows."""
    return [
        (stack.slug, [wait.id for wait in stack.waits])
        for stack in view.waits(world(*tasks)).stacks
    ]


def test_a_task_of_two_things_is_one_stack_in_the_place_of_its_first_and_another_after_it() -> (
    None
):
    """`WaitStacks.test_a_task_of_two_things_is_one_group_in_the_place_of_its_first_and_another_tasks_row_after_it`."""
    single = calling("board-card", 42, 5)
    landing = single.record.landing
    assert landing is not None
    refused = Refused(
        tip=TIP,
        source="github",
        kind="rule",
        line="a review is required",
        by="owner",
        at=MOMENT + timedelta(minutes=6),
    )
    turned_down = replace(landing, reads=(), refused=refused)
    board = replace(single, record=replace(single.record, landing=turned_down))
    shown = view.waits(world(calling("logo-eyes", 73, 10), board)).stacks
    assert [(stack.slug, stack.count) for stack in shown] == [
        ("logo-eyes", "2 things"),
        ("board-card", "1 thing"),
    ]
    assert [wait.verb for wait in shown[0].waits] == [
        "Read the merge review",
        "Merge the pull request #73",
    ]
    assert shown[0].first == "Read the merge review"


def test_a_task_of_one_thing_is_a_stack_of_its_one_row() -> None:
    """`WaitStacks.test_a_task_of_one_thing_is_a_group_of_its_one_row`."""
    held = task("board-answers-a-card", status="shaping", hold=INTERVIEW)
    assert groups(held) == [
        ("board-answers-a-card", ["wait-held-board-answers-a-card"])
    ]


def test_two_tasks_of_two_things_are_two_stacks_in_the_order_of_their_first_rows() -> (
    None
):
    """`WaitStacks.test_two_tasks_of_two_things_are_two_groups_in_the_order_of_their_first_rows`."""
    assert groups(calling("receipt", 44, 20), calling("logo-eyes", 73, 10)) == [
        ("logo-eyes", ["wait-review-logo-eyes", "wait-merge-logo-eyes"]),
        ("receipt", ["wait-review-receipt", "wait-merge-receipt"]),
    ]


def test_nothing_waits_no_stack() -> None:
    """`WaitStacks.test_nothing_waits_no_group`."""
    assert view.waits(world(task(status="building"))).stacks == ()


def only(seen: Seen, kind: str | None = None) -> Wait:
    """The one row of the task of `seen` (of `kind`), with Lem's open of session S1."""
    opened = replace(seen, acts=(OPENED,))
    rows = [
        wait
        for stack in view.waits(world(opened)).stacks
        for wait in stack.waits
        if kind is None or wait.kind == kind
    ]
    assert len(rows) == 1, [wait.kind for wait in rows]
    return rows[0]


def test_a_held_step_with_no_yes_on_the_board_goes_to_the_session() -> None:
    """`AnsweredInSession.test_a_held_step_with_no_yes_on_the_board_goes_to_the_session`."""
    row = only(task(status="shaping", hold=INTERVIEW))
    assert (row.kind, row.jump) == ("held", "S1")


def test_criteria_stay_on_the_board() -> None:
    """`AnsweredInSession.test_a_held_step_whose_yes_is_on_the_board_and_criteria_stay_on_the_board`:
    criteria that wait for his yes, and an interview whose read is in, which is a criteria row."""
    hold = OwnerHold(
        on="criteria", line="the criteria wait for the owner", since=MOMENT
    )
    row = only(task(status="shaping", hold=hold))
    assert (row.kind, row.jump) == ("criteria", None)


def test_a_task_its_session_stopped_goes_to_the_session() -> None:
    """`AnsweredInSession.test_a_task_its_session_stopped_goes_to_the_session`."""
    hold = Blocked(
        why="a builder ended two times with no report", fix="tell it", since=MOMENT
    )
    row = only(task(status="building", hold=hold))
    assert (row.kind, row.jump) == ("blocked", "S1")


def test_a_session_that_does_not_answer_goes_to_it_and_a_task_with_no_session_does_not() -> (
    None
):
    """`AnsweredInSession.test_a_session_that_does_not_answer_goes_to_it_and_a_task_with_no_session_does_not`."""
    deaf = Session(live=True, since=MOMENT, unanswered=True)
    row = only(replace(task(status="building"), session=deaf), "session")
    assert (row.kind, row.jump) == ("session", "S1")
    row = only(replace(task(status="building"), session=gone()), "session")
    assert (row.kind, row.jump) == ("session", None)


def test_a_merge_a_breaker_and_a_plan_stay_on_the_board() -> None:
    """`AnsweredInSession.test_a_merge_a_breaker_a_plan_and_a_task_after_a_dropped_one_stay_on_the_board`
    (the task after a dropped one: `test_owner_rows.py`)."""
    assert only(calling("gift-note", 44, 1), "merge").jump is None
    breaker = Breaker(
        id=1,
        at=MOMENT,
        cause="criteria",
        what="x",
        document="breaker-1.md",
        handoff="h.md",
    )
    stopped = task(
        status="building",
        hold=BreakerHold(number=1, since=MOMENT),
        decisions=(breaker,),
    )
    assert (only(stopped).kind, only(stopped).jump) == ("breaker", None)
    plan = OwnerHold(on="plan", line="the plan waits for the owner", since=MOMENT)
    row = only(task(status="planned", hold=plan))
    assert (row.kind, row.jump) == ("plan", None)


def test_a_session_that_does_not_live_takes_no_jump() -> None:
    """`AnsweredInSession.test_a_session_that_does_not_live_takes_no_jump`."""
    asleep = Session(live=False, since=MOMENT + timedelta(minutes=59))
    row = only(replace(task(status="shaping", hold=INTERVIEW), session=asleep), "held")
    assert (row.kind, row.jump) == ("held", None)


def test_a_parked_task_waits_for_nobody_and_stands_apart() -> None:
    """`Breakers.test_a_parked_or_ended_task_waits_for_nobody_and_a_parked_one_stands_apart`."""
    breaker = Breaker(
        id=1,
        at=MOMENT,
        cause="criteria",
        what="x",
        document="breaker-1.md",
        handoff="h.md",
    )
    parked = task(
        line="the owner parked it: later",
        status="building",
        hold=Parked(since=MOMENT, words="later"),
        decisions=(breaker,),
    )
    shown = view.waits(world(parked, task("ended", status="landed")))
    assert shown.stacks == ()
    assert [(one.slug, one.why) for one in shown.parked] == [
        ("gift-note", "The owner parked it: later")
    ]
    assert shown.parked[0].breaker == (
        "Breaker 1 stopped its build: “x”, since no option keeps the criteria you approved."
    )


def test_a_card_of_the_live_session_is_a_row_whose_verb_opens_the_card() -> None:
    """The view's part of `Cards.test_an_open_card_of_the_live_session_is_a_row_with_its_question_whose_verb_opens_the_card`."""
    card = Question(
        id="card:gift-note:PAGE-1",
        topic="card",
        question="which one?",
        options=("a", "b"),
        asked=MOMENT,
    )
    row = only(task(status="building", questions=(card,)))
    assert (row.kind, row.verb) == ("card", "Which one?")
    assert row.href == "/studio/shop/tasks/gift-note/card/PAGE-1?in=waits"
    assert row.acts and row.acts.links[0].label == "Answer the card…"
