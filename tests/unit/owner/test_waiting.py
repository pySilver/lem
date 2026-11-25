"""The rows of what waits for the owner, from records and the look at the world: each kind, who
it is his for, and the list's order (`main`: `tests/lem-decisions.sh` "waiting lists in one
JSON what waits for the owner", `tests/unit/test_board_model.py` `WaitingByTask`, `Breakers`,
`AfterDropped`, `InterviewTurns`, `SeatThatFailed`)."""

from datetime import date, timedelta
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from msgspec.structs import replace

from fakes.records import MOMENT, record
from lem.app.landing import mergeread, reconcile
from lem.app.owner import briefs, listing
from lem.kernel.errors import Refusal
from lem.model.criteria import change, waits
from lem.model.landing.merge import LAND_OWNER, MOVED
from lem.model.landing.merge_standing import kept
from lem.model.owner import merges, merging, verbs, waiting
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
from lem.records.landing.merge import MergeAccepted, MergeIntent
from lem.records.questions import Answer, Question
from lem.records.work import Span
from lem.store import tasks
from unit.landing.merges import BY_OWNER
from unit.landing.worlds import CRITERION
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
from unit.task.spaces import workspace

if TYPE_CHECKING:
    from pathlib import Path

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


def test_criteria_asked_again_in_the_same_second_wait_for_an_answer() -> None:
    before = waits.asked(record(status="shaping").task, MOMENT, "Please approve", "d1")
    answered = change.typed(before, MOMENT, "Keep the criteria as they are.")
    assert rows(Look(record=replace(record(), task=answered))) == []
    again = change.unchanged(answered, MOMENT, "d1")
    assert again.questions[-1].id != answered.questions[-1].id
    assert rows(Look(record=replace(record(), task=again))) == [
        ("criteria", "held:fix-the-login")
    ]


def test_a_task_queued_after_a_dropped_task_waits_for_his_word() -> None:
    dropped = look("first", status="dropped", since=LATER)
    after = look("second", status="queued", after=("first",))
    assert rows(dropped, after) == [("after_dropped", "after_dropped:second")]
    found = waiting.rows((dropped, after), away=False, now=NOW)
    assert found[0].after == ("first",)
    assert found[0].since == LATER
    queued_later = look("second", status="queued", after=("first",), since=NOW)
    found = waiting.rows((dropped, queued_later), away=False, now=NOW)
    assert found[0].since == NOW
    assert rows(look("first", status="building"), after) == []
    assert rows(look("first", status="landed"), after) == []
    started = look("second", status="building", after=("first",))
    assert rows(dropped, started) == []


def test_the_after_dropped_row_ends_on_drop_or_when_a_queue_clears_after() -> None:
    dropped = look("first", status="dropped")
    queued = look("second", status="queued", after=("first",))
    assert rows(dropped, queued) == [("after_dropped", "after_dropped:second")]
    assert rows(dropped, look("second", status="dropped", after=("first",))) == []
    assert rows(dropped, look("second", status="queued")) == []


def test_a_block_is_his_unless_it_waits_for_the_task_that_repairs_the_base() -> None:
    mine = Blocked(why="a builder ended twice", fix="tell it what to do", since=MOMENT)
    base = replace(mine, after="fix-the-base")
    assert rows(look(status="landing", hold=mine)) == [("blocked", "blocked:gift-note")]
    assert rows(look(status="landing", hold=base)) == []


def test_all_drops_in_queue_order_give_the_owner_one_action() -> None:
    queue = look("last", status="queued", after=("missing", "next", "first", "next"))
    first = look("first", status="dropped")
    next_drop = look("next", status="dropped", since=LATER)
    found = waiting.rows((first, next_drop, queue), away=False, now=NOW)
    assert [(row.key, row.after, row.since) for row in found] == [
        ("after_dropped:last", ("next", "first"), LATER)
    ]


def test_a_queued_task_needs_a_session_when_each_predecessor_finished() -> None:
    queue = seen(look("last", status="queued", after=("first", "next")), session=gone())
    first = look("first", status="landed")
    assert rows(first, queue) == []
    assert rows(first, look("next", status="building"), queue) == []
    assert rows(first, look("next", status="answered"), queue) == [
        ("session", "session:last")
    ]
    assert rows(seen(look("last", status="queued"), session=gone())) == []


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
            look("second", status="queued", after=("first",), hold=parked),
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
    carried = replace(
        read("merge", why="The same changes passed."), carried_from="d" * 40
    )
    owner_merges = opened(
        proposed=replace(proposed(who="owner"), merge_review="carried"),
        reads=(carried,),
    )
    found = waiting.rows((owner_merges,), away=False, now=NOW)
    assert [(row.kind, row.why) for row in found] == [
        ("review", LAND_OWNER),
        ("merge", None),
    ]


def test_a_new_criteria_approval_gives_the_merge_to_the_owner() -> None:
    ready = opened(proposed=proposed(), reads=(read("merge"),))
    assert merging.merge_wait(ready) == "merges"
    criteria = ready.record.task.criteria
    lines = (replace(CRITERION, text="The login works with a hardware key."),)
    approval = replace(
        criteria.approvals[-1], number=2, at=MOMENT, by="owner", criteria=lines
    )
    task = replace(
        ready.record.task,
        criteria=replace(
            criteria, approvals=(*criteria.approvals, approval), criteria=lines
        ),
    )
    changed = replace(ready, record=replace(ready.record, task=task))
    assert merging.merge_wait(changed) == "owner"
    found = waiting.rows((changed,), away=False, now=NOW)
    assert [(row.kind, row.why) for row in found] == [
        ("review", MOVED),
        ("merge", None),
    ]
    pull = briefs.entry_of(found[-1], changed)
    assert pull.green is False and pull.not_green == (MOVED,)


def test_merge_rows_ask_who_merges_once() -> None:
    ready = opened(proposed=proposed(who="owner"), reads=(read("call"),))
    with patch.object(merging, "merge_wait", wraps=merging.merge_wait) as wait:
        assert [row.kind for row in merges.merge_rows(ready)] == ["review", "merge"]
    wait.assert_called_once_with(ready)


def test_an_unresolved_merge_intent_asks_for_a_check_on_github() -> None:
    proposal = proposed()
    intent = MergeIntent(tip=proposal.tip, by="merger", via="session", at=LATER)
    uncertain = opened(proposed=proposal, reads=(read("merge"),), intent=intent)
    found = waiting.rows((uncertain,), away=False, now=NOW)
    assert merging.merge_wait(uncertain) == "owner"
    assert [(row.kind, row.since) for row in found] == [("merge", LATER)]
    task = uncertain.record.task
    assert verbs.verb(found[0], task, uncertain.record.landing) == (
        "Check the pull request on GitHub"
    )
    accepted = MergeAccepted(tip=proposal.tip, at=LATER, queued="merge queue")
    assert rows(opened(proposed=proposal, accepted=accepted)) == []


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


def test_a_review_after_a_base_refusal_offers_the_owner_the_merge_again() -> None:
    old = refused("lem", "base")
    called = opened(
        proposed=proposed(), refused=old, reads=(replace(read(None), attempts=2),)
    )
    found = waiting.rows((called,), away=False, now=NOW)
    task, landing = called.record.task, called.record.landing
    assert [verbs.verb(row, task, landing) for row in found] == [
        "Read the merge review",
        "Merge the pull request #44",
    ]
    assert landing is not None and landing.refused == old
    other = opened(
        proposed=proposed(), refused=refused("lem", "rule"), reads=landing.reads
    )
    assert verbs.verb(found[-1], other.record.task, other.record.landing) == (
        "The merge did not go through"
    )


@pytest.mark.parametrize(
    "read_first", [True, False], ids=["read-first", "refusal-first"]
)
def test_a_read_and_base_refusal_in_the_same_second_follow_their_write_order(
    tmp_path: Path, *, read_first: bool
) -> None:
    review = replace(read(None), attempts=2, at=MOMENT)
    record = opened(proposed=proposed()).record
    if read_first:
        record = mergeread.noted(record, read=review)
    base_moved = Refusal("base", "the base moved", "read the moved base")
    held = kept(record, base_moved, BY_OWNER, MOMENT)
    assert held is not None
    record = reconcile.stood(record, held=held)
    if not read_first:
        record = mergeread.noted(record, read=review)

    tasks.create(workspace(tmp_path).state, record)
    found = listing.listed(tmp_path, None, NOW, NOW.date())
    expected = (
        [] if read_first else ["Read the merge review", "Merge the pull request #44"]
    )
    assert [
        thing.verb
        for stack in found.tasks
        for thing in stack.things
        if thing.kind in {"review", "merge"}
    ] == expected


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
    merge = opened("merge-me", proposed=proposed(), reads=(read("call"),))
    plan = look("read-me", status="planned", hold=held("plan", "read it"))
    later = replace(held("criteria"), since=LATER)
    criteria_later = look("approve-later", status="shaping", hold=later)
    criteria = look("approve-me", status="shaping", hold=held("criteria"))
    breaker = look(
        "stopped-build", status="building", hold=BreakerHold(number=1, since=LATER)
    )
    looks = (merge, plan, criteria_later, criteria, breaker)
    records = {look.record.task.slug: look.record for look in looks}
    found = waiting.rows(looks, away=False, now=NOW)
    stacks = waiting.stacks(found)
    assert [row.task for row in found] == [
        "stopped-build",
        "approve-me",
        "approve-later",
        "read-me",
        "merge-me",
        "merge-me",
    ]
    assert [
        [
            verbs.verb(row, records[row.task].task, records[row.task].landing)
            for row in stack
        ]
        for stack in stacks
    ] == [
        ["Read the breaker of stopped-build"],
        ["Approve the criteria"],
        ["Approve the criteria"],
        ["Read the plan"],
        ["Read the merge review", "Merge the pull request #44"],
    ]


def test_the_verbs_say_the_owners_act() -> None:
    task = record("second", status="queued", after=("first",)).task
    pair = (
        look("first", status="dropped"),
        look("second", status="queued", after=("first",)),
    )
    row = waiting.rows(pair, away=False, now=NOW)[0]
    assert (
        verbs.verb(row, task, None)
        == "first was dropped: your word starts or ends this task"
    )
