"""The rules of `main`'s `tests/unit/test_board_model.py` on an open pull request, a landing and a
task two releases back, case by case (`Merge`, `MovedBase`, `Landing`, `WaitsBehind`,
`SeatThatFailed`, `ReleaseStop`): each test names the old case it stands for."""

import dataclasses
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal

import msgspec
import pytest
from msgspec.structs import replace

from fakes.records import MOMENT
from lem.app.landing.mergeread import noted
from lem.app.owner import forge
from lem.board.views import offers, owed, sessions, standing, tasks, telling
from lem.board.views.checks import tab
from lem.board.views.panel import heads, now
from lem.board.views.panel import waiting as panel_waiting
from lem.board.views.waits import view as waits_view
from lem.board.views.where import where
from lem.board.views.world import Forge
from lem.model.landing import merge_said, merge_standing
from lem.model.owner import merging
from lem.model.task import release
from lem.records.holds import Blocked, ReleaseHold
from lem.records.journal.landing import CheckWait
from lem.records.landing.checks import Checked, Outcome
from lem.records.landing.merge import Refused
from lem.records.landing.propose import MergeRead, Proposed, Standing
from lem.records.landing.record import Landing, Pull
from unit.board.views.small import gone, task, world

if TYPE_CHECKING:
    from pathlib import Path

    from lem.board.inputs.waits import Wait
    from lem.board.views.world import Seen
    from lem.records.landing.merge import Merger

type Verdict = Literal["merge", "call"]

SLUG = "gift-note"
TIP = "a" * 40
NEXT = "d" * 40
BASE = "b" * 40
MOVED = "e" * 40
PULL = Pull(number=41, url="https://github.com/acme/shop/pull/41", title="Gift note")
PROPOSED = Proposed(tip=TIP, base=BASE, green=True, who_acts="merger", at=MOMENT)
CAREFUL = replace(PROPOSED, who_acts="owner")


def at(minutes: float) -> datetime:
    """A moment `minutes` after the records' moment."""
    return MOMENT + timedelta(minutes=minutes)


def opened(**landing: object) -> Seen:
    """The open pull request #41 of the task, with the landing's `landing` fields."""
    made = task(SLUG, f"pull request {PULL.url}", status="open")
    shaped = replace(Landing(phase="open", pull=PULL), **landing)
    return replace(made, record=replace(made.record, landing=shaped))


def read(
    verdict: Verdict | None = "merge",
    *,
    tip: str = TIP,
    minutes: float = 2,
    **fields: object,
) -> MergeRead:
    """The merge agent's read of `tip` with `verdict`."""
    made = MergeRead(
        tip=tip,
        base=BASE,
        base_tree=BASE,
        verdict=verdict,
        why="Verdict: call. A test proves less than its criterion.",
        at=at(minutes),
    )
    return replace(made, **fields)


def refused(by: Merger = "merger", source: str = "lem", minutes: float = 3) -> Refused:
    """A refusal of the merge of the proposed tip: Lem's for a moved base, or GitHub's."""
    if source == "lem":
        return Refused(
            tip=TIP,
            source="lem",
            kind="base",
            line="origin/main moved after the checks ran",
            by=by,
            at=at(minutes),
        )
    return Refused(
        tip=TIP,
        source="github",
        kind="rule",
        line="Required status check is expected",
        by=by,
        at=at(minutes),
    )


def standing_merge(seen: Seen) -> Seen:
    """The task with the owner's merge standing for the proposed tip, with the reasons it is
    not green as they read now."""
    record = seen.record
    digest = merge_standing.digest_of(merge_standing.reasons_now(record))
    kept = Standing(tip=TIP, reasons_digest=digest, by_act="board", at=at(3))
    landing = replace(record.landing or Landing(), standing=kept)
    return replace(seen, record=replace(record, landing=landing))


def waits(seen: Seen, conflicts: frozenset[str] = frozenset()) -> list[Wait]:
    """The rows of Waits for you of the one task of `seen`."""
    shown = dataclasses.replace(world(seen), forge=Forge(conflicts=conflicts))
    return [one for stack in waits_view.waits(shown).stacks for one in stack.waits]


def wait_of(seen: Seen) -> str | None:
    """Who the merge of the task waits for."""
    return merging.merge_wait(seen.record)


def placed(seen: Seen) -> tuple[str, str, str]:
    """The task's column, its state's words, and its card's line."""
    rows = owed.of_task(world(seen), SLUG)
    where_it_stands = standing.standing(seen, rows)
    title = tasks.TITLES[where_it_stands.column]
    line = telling.line(seen.record, where_it_stands, title)
    return where_it_stands.column, where_it_stands.label, line


def test_a_merge_review_that_calls_him_comes_before_the_merge_and_a_new_proposal_forgets_it() -> (
    None
):
    """`main`'s Merge.test_a_merge_review_that_calls_him_comes_before_the_merge_and_a_new_
    proposal_forgets_it."""
    calls = opened(proposed=PROPOSED, reads=(read("call"),))
    shown = waits(calls)
    assert [(one.kind, one.verb) for one in shown] == [
        ("review", "Read the merge review"),
        ("merge", "Merge the pull request #41"),
    ]
    assert shown[0].where == (
        "The merge review is the first card of the task’s Overview. "
        "A test proves less than its criterion."
    )
    assert waits(opened(proposed=PROPOSED, reads=(read("merge"),))) == []
    again = opened(proposed=replace(PROPOSED, tip=NEXT), reads=(read("call"),))
    assert (wait_of(again), waits(again)) == ("reads", [])


def test_a_proposal_waits_for_his_merge_with_its_number_and_green() -> None:
    """`main`'s Merge.test_a_proposal_waits_for_his_merge_with_its_number_and_green: the card's
    line links the pull request's address by its number."""
    seen = opened(proposed=CAREFUL, reads=(read("call"),))
    assert placed(seen) == (
        "you",
        "Waits for the merge",
        f"Waits for the merge: pull request [#41]({PULL.url})",
    )
    assert waits(seen)[-1].verb == "Merge the pull request #41"
    rows = owed.of_task(world(seen), SLUG)
    card = now.now(world(seen), seen, rows, standing.standing(seen, rows))
    assert card.more == "green"


def test_an_open_task_needs_a_session_only_while_its_merge_review_is_due() -> None:
    proposed = replace(opened(proposed=PROPOSED), session=gone())
    assert [one.kind for one in waits(proposed)] == ["session"]
    called = replace(opened(proposed=PROPOSED, reads=(read("call"),)), session=gone())
    assert [one.kind for one in waits(called)] == ["review", "merge"]


def test_a_pull_request_the_forge_calls_conflicting_is_a_row_with_nothing_to_do() -> (
    None
):
    """`main`'s Merge.test_a_pull_request_the_forge_calls_conflicting_is_a_row_with_nothing_to_
    do: the merge row is a fault with nothing for him to do; the forge's call counts only at
    the head Lem proposed last."""
    seen = opened(proposed=PROPOSED, reads=(read("call"),))
    merge = waits(seen, frozenset((SLUG,)))[-1]
    assert (merge.verb, merge.look) == ("It conflicts with the base", "bad")
    assert merge.where.startswith("Nothing to do now")
    assert merge.acts is None
    assert waits(seen)[-1].verb == "Merge the pull request #41"
    look = forge.Look(seen={SLUG: forge.Seen(head=TIP, mergeable="CONFLICTING")})
    older = forge.Look(seen={SLUG: forge.Seen(head=NEXT, mergeable="CONFLICTING")})
    assert forge.conflicts(look, seen.record)
    assert not forge.conflicts(older, seen.record)


def test_an_open_pull_request_waits_for_him_only_when_its_merge_does() -> None:
    """`main`'s Merge.test_an_open_pull_request_waits_for_him_only_when_its_merge_does: the
    merge agent reads it, Lem merges it, a read that calls him, GitHub's refusal, and a read
    of an older tip, which is none; his own merge stays offered in each."""
    reads = opened(proposed=PROPOSED)
    merges = opened(proposed=PROPOSED, reads=(read("merge"),))
    calls = opened(proposed=CAREFUL, reads=(read("merge"),))
    turned_down = opened(
        proposed=PROPOSED, reads=(read("merge"),), refused=refused(source="github")
    )
    older = opened(proposed=PROPOSED, reads=(read("merge", tip=NEXT),))
    assert (wait_of(reads), waits(reads), placed(reads)[:2]) == (
        "reads",
        [],
        ("checks", "The merge agent reads it"),
    )
    assert (wait_of(merges), waits(merges), placed(merges)[:2]) == (
        "merges",
        [],
        ("checks", "Lem merges it"),
    )
    assert ([one.kind for one in waits(calls)], placed(calls)[0]) == (
        ["review", "merge"],
        "you",
    )
    assert ([one.kind for one in waits(turned_down)], placed(turned_down)[0]) == (
        ["merge"],
        "you",
    )
    assert (wait_of(older), waits(older)) == ("reads", [])
    for seen in (reads, merges, calls, turned_down, older):
        assert offers.merge_offered(seen)


def test_a_base_refusal_is_the_merge_agents_to_read_and_githubs_is_his() -> None:
    """`main`'s MovedBase.test_a_base_refusal_is_no_row_and_githubs_is_his."""
    base = opened(proposed=PROPOSED, refused=refused("owner"))
    assert (wait_of(base), waits(base), placed(base)[1]) == (
        "reads",
        [],
        "The merge agent reads it",
    )
    github = opened(proposed=PROPOSED, refused=refused("owner", "github"))
    assert [one.kind for one in waits(github)] == ["merge"]


def test_a_task_queued_after_one_that_landed_or_answered_starts_and_after_a_dropped_one_waits() -> (
    None
):
    """`main`'s MovedBase.test_a_dropped_task_leaves_the_task_behind_it_queued: behind a task
    that landed or was answered, the queued task goes on (it needs its session); behind a
    dropped one, it waits for his word; behind an open one, neither."""
    queued = replace(task(status="queued", after=("coupon",)), session=gone())
    for status, needs, waits_word in (
        ("landed", True, False),
        ("answered", True, False),
        ("dropped", False, True),
        ("open", False, False),
    ):
        seen = world(task("coupon", status=status), queued)
        kinds = [row.kind for row in owed.of_task(seen, SLUG)]
        assert ("session" in kinds, "after_dropped" in kinds) == (needs, waits_word), (
            status
        )


def test_a_merge_of_his_that_stands_is_the_servers() -> None:
    """`main`'s MovedBase.test_a_merge_of_his_that_stands_is_the_servers: a stand for another
    tip than the proposal's is none."""
    calls = opened(proposed=CAREFUL, reads=(read("merge"),))
    stands = standing_merge(calls)
    assert (wait_of(stands), waits(stands)) == ("merges", [])
    landing = stands.record.landing
    assert landing is not None
    assert landing.standing is not None
    other = replace(landing, standing=replace(landing.standing, tip=NEXT))
    older = replace(stands, record=replace(stands.record, landing=other))
    assert wait_of(older) == "owner"


def test_a_merge_the_moved_base_refused_is_not_offered_again_until_the_next_proposal() -> (
    None
):
    """`main`'s MovedBase.test_a_merge_the_moved_base_refused_is_not_offered_again_until_the_
    next_proposal: his merge stands, so a second press could only meet the same moved base;
    the merge agent's own merge that the moved base refused leaves his press offered; another
    round offers none; the new proposal offers it."""
    proposed = opened(proposed=CAREFUL, reads=(read("call"),))
    assert offers.merge_offered(proposed)
    his = standing_merge(
        opened(proposed=CAREFUL, reads=(read("call"),), refused=refused("owner"))
    )
    assert (wait_of(his), offers.merge_offered(his)) == ("reads", False)
    merger = opened(proposed=CAREFUL, reads=(read("call"),), refused=refused())
    assert (wait_of(merger), offers.merge_offered(merger)) == ("reads", True)
    round_read = read("call", minutes=4, base_call=merge_said.ROUND)
    landing = his.record.landing
    assert landing is not None
    another = replace(
        his,
        record=replace(
            his.record, landing=replace(landing, reads=(*landing.reads, round_read))
        ),
    )
    assert (wait_of(another), offers.merge_offered(another)) == ("relands", False)
    after = replace(
        landing,
        proposed=replace(CAREFUL, tip=NEXT),
        reads=(),
        refused=None,
    )
    fresh = replace(his, record=replace(his.record, landing=after))
    assert offers.merge_offered(fresh)


def test_a_read_with_a_verdict_answers_lems_refusal_for_the_base_and_never_githubs() -> (
    None
):
    """`main`'s MovedBase.test_a_read_on_the_checks_base_answers_lems_refusal_after_a_revert
    and MovedBase.test_a_safe_read_of_the_moved_base_answers_lems_refusal, changed: the read
    that settles with a verdict takes Lem's refusal of that tip for a moved base off the
    record (`app/landing/mergeread.noted`), on the checks' own base after a revert as on the
    moved one; a read with no verdict answers nothing; no read answers GitHub's refusal."""
    back = read(
        "merge", minutes=4, base_call="safe", why="B changed only docs/board.md"
    )
    merger = opened(proposed=PROPOSED, refused=refused())
    answered = noted(merger.record, read=back)
    landing = answered.landing
    assert landing is not None
    assert landing.refused is None
    seen = replace(merger, record=answered)
    assert (wait_of(seen), placed(seen)[1]) == ("merges", "Lem merges it")
    his = standing_merge(opened(proposed=CAREFUL, refused=refused("owner")))
    safe_call = read("call", minutes=4, base_call="safe")
    stood = replace(his, record=noted(his.record, read=safe_call))
    assert (wait_of(stood), waits(stood)) == ("merges", [])
    silent = read(None, minutes=4, attempts=2)
    mute = noted(his.record, read=silent)
    assert mute.landing is not None
    assert mute.landing.refused is not None
    github = opened(proposed=PROPOSED, refused=refused(source="github"))
    kept = noted(github.record, read=back)
    assert kept.landing is not None
    assert kept.landing.refused is not None
    assert wait_of(replace(github, record=kept)) == "owner"


def test_another_round_relands_until_the_next_proposal() -> None:
    """`main`'s MovedBase.test_another_round_relands_until_the_next_proposal: a later safe read
    answers nothing; another round with no refusal before it is the session's too; the next
    proposal forgets it."""
    round_read = read("call", minutes=3, base_call=merge_said.ROUND)
    again = opened(proposed=PROPOSED, reads=(round_read,), refused=refused(minutes=4))
    assert (wait_of(again), waits(again), placed(again)[1]) == (
        "relands",
        [],
        "Lem lands it again",
    )
    later = read("merge", minutes=5, base_call="safe")
    landing = again.record.landing
    assert landing is not None
    safe = replace(landing, reads=(round_read, later))
    assert (
        wait_of(replace(again, record=replace(again.record, landing=safe))) == "relands"
    )
    alone = opened(proposed=PROPOSED, reads=(round_read,))
    assert wait_of(alone) == "relands"
    landed = replace(landing, proposed=replace(PROPOSED, tip=NEXT))
    assert (
        wait_of(replace(again, record=replace(again.record, landing=landed))) == "reads"
    )


def test_his_standing_merge_waits_for_nobody_once_the_safe_read_is_on_record() -> None:
    """`main`'s MovedBase.test_his_standing_merge_waits_for_nobody_between_the_safe_read_and_
    its_stands_line, changed: the safe read and what it answers are one write of the record, so
    no look falls between them; from it on, his standing merge is the server's and nothing
    waits for him."""
    his = standing_merge(
        opened(proposed=CAREFUL, reads=(read("call"),), refused=refused("owner"))
    )
    safe = read("call", minutes=11, base_call="safe")
    seen = replace(his, record=noted(his.record, read=safe))
    assert (wait_of(seen), waits(seen), placed(seen)[0]) == ("merges", [], "checks")


def test_the_checks_tab_shows_the_newest_run_on_its_tip() -> None:
    """`main`'s Landing.test_a_result_on_another_tip_starts_a_new_run_of_the_checks, changed:
    the record keeps the newest run of the checks whole, on one tip, so a run on another tip
    takes the place of the last; the tab lists that run's commands and counts its red ones."""
    outcomes = (
        Outcome(
            command="make test", exit=0, last="ok", output="checks/1.log", passed=True
        ),
        Outcome(
            command="make lint", exit=0, last="ok", output="checks/2.log", passed=True
        ),
    )
    checked = Checked(
        tip=NEXT,
        tree=NEXT,
        base=BASE,
        inputs="i",
        outcome="passed",
        outcomes=outcomes,
        at=at(6),
    )
    made = task(SLUG, status="landing")
    seen = replace(made, record=replace(made.record, landing=Landing(checked=checked)))
    shown = tab.checks(world(seen), seen)
    assert [(one.command, one.tip) for one in shown.commands] == [
        ("make test", NEXT[:7]),
        ("make lint", NEXT[:7]),
    ]
    assert shown.commands_said == "2 commands green"


def behind(*waits_of: CheckWait) -> Seen:
    """The landing plugin-dir-for-the-plan-talk, whose checks wait."""
    made = task("plugin-dir-for-the-plan-talk", "the checks start", status="landing")
    journal = (*made.record.journal, *waits_of)
    return replace(made, record=replace(made.record, journal=journal))


FIRST = "fast-track-checks-documents"
SAID = f"Its checks wait behind {FIRST}, which waits longer"


def test_behind_goes_before_a_minute_after_the_last_start() -> None:
    """`main`'s WaitsBehind.test_behind_goes_before_a_minute_after_the_last_start: a wait that
    names the run it waits behind and the run it starts a minute after says the first."""
    wait = CheckWait(
        at=at(1), reason="behind", behind=FIRST, why="longer", after="keys-help"
    )
    assert telling.waiting(behind(wait).record) == SAID


def test_criterion_7_a_landing_behind_one_that_waits_longer_says_so_on_the_card() -> (
    None
):
    """`main`'s WaitsBehind.test_criterion_7_a_landing_behind_one_that_waits_longer_says_so_on_
    the_card_and_in_the_feed: the card, the large card's head and what the task waits for; the
    feed is `unit.board.views.test_activity_feed.test_criterion_7_a_landing_behind_one_that_
    waits_longer_says_so_in_the_feed`, and the load's words of the first are
    `unit.board.views.test_kanban_rules.test_landing_a_landing_that_waits_says_what_for_until_
    its_next_event`."""
    seen = behind(CheckWait(at=at(1), reason="behind", behind=FIRST, why="longer"))
    slug = seen.record.task.slug
    rows = owed.of_task(world(seen), slug)
    where_it_stands = standing.standing(seen, rows)
    title = tasks.TITLES[where_it_stands.column]
    assert telling.line(seen.record, where_it_stands, title) == SAID
    assert heads.now_head(seen) == SAID
    told = panel_waiting.waits_for(seen, rows)
    assert told is not None
    assert (told.text, told.yours) == (SAID, False)


LINE = (
    "the reviewer `codex/gpt-6.2-sol:high` gave an error: no tokens, and this project "
    "permits no fallback"
)


def test_the_block_of_a_seat_that_failed_is_his_row_with_its_line() -> None:
    """`main`'s SeatThatFailed.test_the_block_is_his_row_with_its_line: the block keeps the
    seat that failed, and a block on the base names none."""
    hold = Blocked(
        why=LINE, fix="lem seat again gift-note", seat="reviewer", since=at(5)
    )
    seen = task(status="building", hold=hold)
    rows = owed.of_task(world(seen), SLUG)
    assert [row.key for row in rows] == [f"blocked:{SLUG}"]
    assert LINE in where(seen, rows[0])
    assert standing.standing(seen, rows).column == "you"
    red = Blocked(why="the base is red", fix="x", after="fix-the-base", since=at(5))
    assert red.seat is None


SAY = release.say(SLUG, "0.1.6", "0.3.1", "0.3.0")


def released(seen: Seen) -> Seen:
    """The task of `seen` with the stop of a task two releases back."""
    hold = ReleaseHold(began="0.1.6", running="0.3.1", say=SAY, since=at(5))
    record = seen.record
    return replace(seen, record=replace(record, task=replace(record.task, hold=hold)))


def test_a_held_task_two_releases_back_stays_blocked_while_its_sessions_turn_runs() -> (
    None
):
    """`main`'s ReleaseStop.test_a_held_task_two_releases_back_stays_blocked_while_its_
    sessions_turn_runs, changed: the stop's message is where the large card says he answers,
    beside its head; its line stays the task's newest state line."""
    from lem.model.owner.looks import Session

    working = Session(live=True, since=MOMENT, working=True)
    seen = replace(released(task(status="shaping")), session=working)
    rows = owed.of_task(world(seen), SLUG)
    assert [row.key for row in rows] == [f"blocked:{SLUG}"]
    where_it_stands = standing.standing(seen, rows)
    assert (where_it_stands.column, where_it_stands.label) == ("you", "Blocked")
    card = now.now(world(seen), seen, rows, where_it_stands)
    assert (card.head, card.where) == ("It began on an older release of Lem", SAY)


def test_a_landing_two_releases_back_is_out_of_the_guard_of_a_stopped_session() -> None:
    """`main`'s ReleaseStop.test_a_landing_two_releases_back_is_out_of_the_guard_of_a_stopped_
    session, changed: the stop is a hold, and the guard watches no task with a hold
    (`unit.sessions.test_acts.test_the_guard_watches_no_task_with_a_hold`), so no stop of it
    stands on the board."""
    from lem.app.sessions.acts import Open, Stopped, Wake

    acts = (
        Open(at=MOMENT, session="S1", name=SLUG, phase="land", why="new"),
        Wake(at=at(45), session="S1", why="status"),
        Stopped(at=at(55), session="S1"),
    )
    landing = replace(task(status="landing"), acts=acts)
    assert sessions.stop_of(landing.record, acts, landing.session) is not None
    stopped = released(landing)
    assert sessions.stop_of(stopped.record, acts, stopped.session) is None


def test_a_state_after_the_stop_is_the_tasks_own_again() -> None:
    """`main`'s ReleaseStop.test_a_state_after_the_stop_is_the_tasks_own_work_again: the drop
    keeps the stop for the resume, and the task is dropped, with nothing for him."""
    seen = released(task(status="dropped"))
    rows = owed.of_task(world(seen), SLUG)
    assert rows == ()
    assert standing.standing(seen, rows).label == "Dropped"


def test_his_drop_is_the_way_on_for_a_task_two_releases_back_in_any_status() -> None:
    """The parts the board holds of `main`'s ReleaseStop.test_what_a_task_two_releases_back_
    waits_for_is_the_stops_message_in_any_status and ReleaseStop.test_an_open_task_two_
    releases_back_is_shown_blocked_with_the_message_and_stays_open: one row with the stop's
    message, his and blocked and never parked, no act of the board, and the message on the
    card and where he answers."""
    from lem.records.holds import Parked

    for status in ("open", "building", "planned", "shaping", "queued"):
        seen = released(task(status=status))
        rows = owed.of_task(world(seen), SLUG)
        assert [(row.kind, row.say) for row in rows] == [("blocked", SAY)], status
        assert where(seen, rows[0]) == SAY
        told = panel_waiting.waits_for(seen, rows)
        assert told is not None
        assert (told.yours, told.where) == (True, SAY)
        where_it_stands = standing.standing(seen, rows)
        assert (where_it_stands.column, where_it_stands.label) == ("you", "Blocked")
        assert placed(seen)[2] == f"Blocked: {SAY}"
        assert not offers.merge_offered(seen)
        assert not offers.approvable(seen.record.task)
        assert not offers.park_offered(seen.record.task)
        assert waits(seen)[0].acts is None
        assert waits_view.waits(world(seen)).parked == ()
    parked = released(task(status="building", hold=Parked(since=MOMENT)))
    assert waits_view.waits(world(parked)).parked == ()


def test_the_forges_last_look_is_read_from_the_state_folder(tmp_path: Path) -> None:
    """`main`'s ForgeLook.test_the_servers_last_look_is_read_from_the_state_folder, changed:
    no file is no look yet, and a file that does not read is a fault that names it, where
    `main` read it as none."""
    from lem.kernel.errors import Fault

    assert forge.read(tmp_path) == forge.Look()
    seen = {SLUG: {"mergeable": "CONFLICTING", "head": TIP}}
    look = {"looked": "2026-11-21T10:00:00Z", "seen": seen}
    (tmp_path / forge.LOOK).write_bytes(msgspec.json.encode(look))
    assert forge.read(tmp_path).seen[SLUG].head == TIP
    (tmp_path / forge.LOOK).write_text("half", encoding="utf-8")
    with pytest.raises(Fault) as fault:
        forge.read(tmp_path)
    assert forge.LOOK in str(fault.value)


def test_the_board_answers_no_plan_and_no_breaker_of_a_task_two_releases_back() -> None:
    """`main`'s ReleaseStop.test_the_board_answers_no_plan_and_no_breaker_of_a_task_two_
    releases_back: the plan's question and the breaker's park stay unanswered on the board,
    whose head says the task began on an older release."""
    from lem.records.holds import BreakerHold
    from lem.records.questions import Question

    plan = Question(
        id="plan:gift-note:1",
        topic="plan",
        question="Build the plan?",
        options=("build", "drop"),
        asked=MOMENT,
    )
    for seen in (
        released(task(status="planned", questions=(plan,))),
        released(task(status="building", hold=BreakerHold(number=1, since=MOMENT))),
    ):
        rows = owed.of_task(world(seen), SLUG)
        card = now.now(world(seen), seen, rows, standing.standing(seen, rows))
        assert (card.answer, card.head) == (None, "It began on an older release of Lem")
        assert waits(seen)[0].acts is None
        assert not offers.park_offered(seen.record.task)


def test_the_board_reads_a_stop_two_releases_back_and_the_forges_look_before_any_command(
    tmp_path: Path,
) -> None:
    """`main`'s ReleaseStop.test_the_mark_of_a_task_two_releases_back_stops_its_acts_before_
    any_stop_is_logged and ReleaseStop.test_the_mark_puts_a_parked_or_landing_task_where_its_
    logged_stop_would, and the board's part of ForgeLook.test_the_servers_last_look_is_read_
    from_the_state_folder: the gather shows the stop as soon as the release rule holds, with
    no command run for the task, and reads the server's last look at the forge."""
    from lem.board.views.ask import Ask
    from lem.board.views.gather import gather
    from lem.board.views.world import Clock
    from lem.records.holds import Parked
    from lem.store import tasks as store
    from unit.board.views.small import NOW, PLACE, UTC, VIEWER
    from unit.task.spaces import workspace

    where = workspace(tmp_path)
    old = replace(opened(proposed=PROPOSED).record, release="0.2.0")
    fresh = replace(
        opened(proposed=CAREFUL, reads=(read("call"),)).record, release=release.BEFORE
    )
    fresh = replace(fresh, task=replace(fresh.task, slug="fresh"))
    parked = task("parked-one", status="planned", hold=Parked(since=MOMENT)).record
    landing = task("landing-one", status="landing").record
    for made in (
        old,
        fresh,
        replace(parked, release="0.2.0"),
        replace(landing, release="0.2.0"),
    ):
        store.create(where.state, made)
    look = {
        "looked": "2026-11-25T10:30:00Z",
        "seen": {"fresh": {"head": TIP, "mergeable": "CONFLICTING"}},
    }
    (where.state / forge.LOOK).write_bytes(msgspec.json.encode(look))
    ask = Ask(
        viewer=VIEWER,
        clock=Clock(now=NOW, zone=UTC),
        version="v",
        place=PLACE,
        home=tmp_path / "home",
    )
    shown = gather(tmp_path, ask)
    rows = {(row.task, row.kind) for row in owed.rows(shown)}
    assert {
        (SLUG, "blocked"),
        ("parked-one", "blocked"),
        ("landing-one", "blocked"),
    } <= rows
    stopped = owed.seen(shown, SLUG)
    assert isinstance(stopped.record.task.hold, ReleaseHold)
    assert not offers.merge_offered(stopped)
    assert waits_view.waits(shown).parked == ()
    assert shown.forge.conflicts == frozenset(("fresh",))
    assert ("fresh", "merge") in rows
    (where.state / forge.LOOK).write_text("half", encoding="utf-8")
    broken = gather(tmp_path, ask)
    assert broken.forge.problem is not None
    assert forge.LOOK in broken.forge.problem
