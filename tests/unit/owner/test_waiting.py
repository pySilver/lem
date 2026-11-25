"""The rows of what waits for the owner, from records and the look at the world: each kind, who
it is his for, and the list's order (`main`: `tests/lem-decisions.sh` "waiting lists in one
JSON what waits for the owner", `tests/unit/test_board_model.py` `WaitingByTask`, `Breakers`,
`AfterDropped`, `InterviewTurns`, `SeatThatFailed`)."""

from datetime import date, timedelta

from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.model.owner import verbs, waiting
from lem.model.owner.looks import Look
from lem.records.approvals import PersonaRead
from lem.records.criteria import Criteria
from lem.records.holds import (
    Blocked,
    BreakerHold,
    OwnerHold,
    OwnerWait,
    Parked,
    ReleaseHold,
)
from lem.records.questions import Answer, Question
from lem.records.work import Span
from unit.owner.looked import (
    LATER,
    gone,
    live,
    look,
    opened,
    proposed,
    read,
    refused,
    seen,
    stop,
)

NOW = MOMENT + timedelta(hours=1)


def rows(*looks: Look, away: bool = False) -> list[tuple[str, str]]:
    return [(row.kind, row.key) for row in waiting.rows(looks, away=away, now=NOW)]


def held(on: OwnerWait, line: str = "the criteria wait for the owner") -> OwnerHold:
    return OwnerHold(on=on, line=line, since=MOMENT)


def test_nothing_waits_no_task_and_a_count_of_0() -> None:
    found = waiting.rows((look(status="building"),), away=False, now=NOW)
    assert found == ()
    assert waiting.stacks(found) == ()


def test_a_breaker_is_one_row_and_stays_his_while_he_is_away() -> None:
    breaker = look(status="building", hold=BreakerHold(number=2, since=MOMENT))
    assert rows(breaker) == [("breaker", "breaker:gift-note:2")]
    assert rows(breaker, away=True) == [("breaker", "breaker:gift-note:2")]


def test_criteria_that_wait_for_his_yes_go_on_without_him_while_he_is_away() -> None:
    criteria = look(status="shaping", hold=held("criteria"))
    night = look(
        "night-task", status="shaping", hold=held("criteria"), night=date(2026, 11, 25)
    )
    assert rows(criteria) == [("criteria", "held:gift-note")]
    assert rows(criteria, away=True) == []
    assert rows(night) == []


def test_an_interview_is_his_until_its_read_runs_and_his_again_when_it_is_in() -> None:
    asking = look(
        status="shaping", hold=held("interview", "the interview waits for the owner")
    )
    assert rows(asking) == [("held", "held:gift-note")]
    ended = Span(name="interview", start=MOMENT, end=MOMENT + timedelta(minutes=5))
    running = PersonaRead(by="lem", started=MOMENT + timedelta(minutes=6))
    reading = replace(running, ended=None)
    task = asking.record.task
    during = replace(task, spans=(ended,), criteria=Criteria(reads=(reading,)))
    assert rows(Look(record=replace(asking.record, task=during))) == []
    done = replace(running, ended=MOMENT + timedelta(minutes=9))
    after = replace(during, criteria=Criteria(reads=(done,)))
    assert rows(Look(record=replace(asking.record, task=after))) == [
        ("criteria", "held:gift-note")
    ]
    writing = replace(during, criteria=Criteria())
    assert rows(Look(record=replace(asking.record, task=writing))) == []


def test_an_order_that_names_no_task_stays_his_while_he_is_away() -> None:
    order = look(status="queued", hold=held("order", "the order waits for the owner"))
    assert rows(order, away=True) == [("held", "held:gift-note")]
    skip = look(status="shaping", hold=held("skip-read", "skip the read?"))
    assert rows(skip) == [("held", "held:gift-note")]
    assert rows(skip, away=True) == []


def test_a_plan_to_read_is_a_row_of_its_own() -> None:
    plan = look(status="planned", hold=held("plan", "the plan waits for the owner"))
    assert rows(plan) == [("plan", "plan:gift-note")]


def test_his_answer_on_the_board_is_the_sessions_until_it_takes_effect() -> None:
    answer = Answer(option="yes", label="Yes", source="board", at=LATER)
    question = Question(
        id="criterion-1",
        topic="criterion",
        question="Approve the criteria?",
        options=("yes", "no"),
        asked=MOMENT,
        answer=answer,
    )
    waits = look(status="shaping", hold=held("criteria"), questions=(question,))
    assert rows(waits) == []
    taken = replace(question, took_effect="approved")
    assert rows(look(status="shaping", hold=held("criteria"), questions=(taken,))) == [
        ("criteria", "held:gift-note")
    ]


def test_a_task_queued_after_a_dropped_task_waits_for_his_word() -> None:
    dropped = look("first", status="dropped")
    after = look("second", status="queued", after="first")
    assert rows(dropped, after) == [("after_dropped", "after_dropped:second")]
    found = waiting.rows((dropped, after), away=False, now=NOW)
    assert found[0].after == "first"
    assert rows(look("first", status="building"), after) == []
    assert rows(look("first", status="landed"), after) == []
    started = look("second", status="building", after="first")
    assert rows(dropped, started) == []


def test_a_block_is_his_unless_it_waits_for_the_task_that_repairs_the_base() -> None:
    mine = Blocked(why="a builder ended twice", fix="tell it what to do", since=MOMENT)
    base = replace(mine, after="fix-the-base")
    assert rows(look(status="landing", hold=mine)) == [("blocked", "blocked:gift-note")]
    assert rows(look(status="landing", hold=base)) == []


def test_a_task_two_releases_back_has_the_stops_one_row_only() -> None:
    stopped = ReleaseHold(
        began="0.9.0", running="1.1.0", say="drop, then resume", since=MOMENT
    )
    task = seen(opened(), stop=stop())
    task = replace(
        task, record=replace(task.record, task=replace(task.record.task, hold=stopped))
    )
    found = waiting.rows((task,), away=False, now=NOW)
    assert [(row.kind, row.say) for row in found] == [("blocked", "drop, then resume")]


def test_a_parked_task_has_no_row() -> None:
    parked = Parked(since=MOMENT, words="later")
    assert (
        rows(
            look("first", status="dropped"),
            look("second", status="queued", after="first", hold=parked),
        )
        == []
    )


def test_an_open_task_with_no_proposal_waits_for_his_merge() -> None:
    assert rows(opened()) == [("merge", "merge:gift-note")]


def test_a_read_that_calls_him_is_a_review_before_its_merge_in_one_stack() -> None:
    calls = opened(proposed=proposed(green=False, who="owner"), reads=(read("call"),))
    found = waiting.rows((calls,), away=False, now=NOW)
    assert [(row.kind, row.why) for row in found] == [
        ("review", "Verdict: call. It needs you."),
        ("merge", None),
    ]
    assert len(waiting.stacks(found)) == 1


def test_a_merge_the_agent_or_the_server_takes_is_not_his() -> None:
    reads = opened(proposed=proposed())
    merges = opened(proposed=proposed(), reads=(read("merge"),))
    assert rows(reads) == []
    assert rows(merges) == []
    owner_merges = opened(
        proposed=proposed(green=False, who="owner"), reads=(read("merge"),)
    )
    assert rows(owner_merges) == [("merge", "merge:gift-note")]


def test_a_refused_merge_is_his_unless_the_merge_agent_reads_the_moved_base() -> None:
    github = opened(proposed=proposed(), refused=refused("github", "rule"))
    base = opened(proposed=proposed(), refused=refused("lem", "base"))
    called = opened(
        proposed=proposed(),
        refused=refused("lem", "base"),
        reads=(replace(read(None), attempts=2),),
    )
    assert rows(github) == [("merge", "merge:gift-note")]
    assert rows(base) == []
    assert rows(called) == [
        ("review", "review:gift-note"),
        ("merge", "merge:gift-note"),
    ]


def test_the_forges_conflict_is_said_on_the_merge() -> None:
    conflicting = seen(opened(), conflict=True)
    found = waiting.rows((conflicting,), away=False, now=NOW)
    assert found[0].conflict
    task = conflicting.record
    assert verbs.verb(found[0], task.task, task.landing) == "It conflicts with the base"
    plain = waiting.rows((opened(),), away=False, now=NOW)[0]
    assert verbs.verb(plain, task.task, task.landing) == "Merge the pull request #44"


def test_a_task_whose_session_is_gone_or_deaf_says_so() -> None:
    building = look(status="building")
    assert rows(seen(building, session=gone())) == [("session", "session:gift-note")]
    assert rows(seen(building, session=live(unanswered=True))) == [
        ("session", "deaf:gift-note")
    ]
    assert rows(seen(building, session=live())) == []
    soon = waiting.rows((seen(building, session=gone()),), away=False, now=MOMENT)
    assert soon == ()


def test_an_ended_task_needs_its_session_only_for_its_cleanup() -> None:
    landed = seen(look(status="landed"), session=gone())
    assert rows(landed) == []
    assert rows(seen(landed, worktree=True)) == [("session", "session:gift-note")]
    assert rows(seen(look(status="answered"), session=gone(), worktree=True)) == []
    open_merge = seen(opened(), session=gone())
    assert rows(open_merge) == [("merge", "merge:gift-note")]
    reads = seen(opened(proposed=proposed()), session=gone())
    assert rows(reads) == [("session", "session:gift-note")]


def test_a_stop_of_the_guard_comes_first_and_is_no_session_row() -> None:
    stopped = seen(look(status="building"), session=gone(), stop=stop(unread=True))
    found = waiting.rows((stopped,), away=False, now=NOW)
    assert [(row.kind, row.unread) for row in found] == [("stopped", True)]


def test_a_card_of_the_live_session_waits_until_it_is_answered() -> None:
    card = Question(
        id="page-7",
        topic="card",
        question="which name?",
        options=("a", "b"),
        asked=MOMENT,
    )
    asking = look(status="building", questions=(card,))
    assert rows(seen(asking, session=live())) == [("card", "card:gift-note:page-7")]
    assert rows(seen(asking, session=gone())) == [("session", "session:gift-note")]
    answer = Answer(option="a", label="a", source="card", at=LATER)
    done = look(status="building", questions=(replace(card, answer=answer),))
    assert rows(seen(done, session=live())) == []


def test_the_list_orders_by_kind_then_by_moment_and_stacks_by_task() -> None:
    merge = opened("merge-me")
    plan = look("read-me", status="planned", hold=held("plan", "read it"))
    later = replace(held("criteria"), since=LATER)
    criteria_later = look("approve-later", status="shaping", hold=later)
    criteria = look("approve-me", status="shaping", hold=held("criteria"))
    breaker = look(
        "stopped-build", status="building", hold=BreakerHold(number=1, since=LATER)
    )
    found = waiting.rows(
        (merge, plan, criteria_later, criteria, breaker), away=False, now=NOW
    )
    assert [row.task for row in found] == [
        "stopped-build",
        "approve-me",
        "approve-later",
        "read-me",
        "merge-me",
    ]
    assert len(waiting.stacks(found)) == 5


def test_the_verbs_say_the_owners_act() -> None:
    task = record("second", status="queued", after="first").task
    pair = (
        look("first", status="dropped"),
        look("second", status="queued", after="first"),
    )
    row = waiting.rows(pair, away=False, now=NOW)[0]
    assert (
        verbs.verb(row, task, None)
        == "first was dropped: your word starts or ends this task"
    )
