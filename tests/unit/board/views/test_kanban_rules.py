"""The rules of the view Tasks and of the frame's counts, case by case (`main`'s
`tests/unit/test_board_model.py`: `Status`, `TopLine`, `WaitingByTask`, `Workspace`, `Landing`,
`WaitsBehind`, `Search`)."""

from datetime import timedelta
from typing import TYPE_CHECKING

from msgspec.structs import replace

from fakes.records import MOMENT
from lem.board.views import pages, tasks, telling
from lem.board.views.activity.view import activity
from lem.board.views.frame import counted, summary
from lem.board.views.frame.page import Beside, frame
from lem.records.holds import OwnerHold, Parked
from lem.records.journal.landing import CheckEnd, CheckWait
from lem.records.journal.task import StateNoted
from lem.records.landing.propose import MergeRead, Proposed
from lem.records.landing.record import Landing, Pull
from lem.records.questions import Question
from lem.records.work import Plan, Span
from unit.board.views.small import NOW, gone, task, world

if TYPE_CHECKING:
    from lem.board.views.standing import Standing
    from lem.board.views.world import Seen, World

CRITERIA = OwnerHold(
    on="criteria", line="the criteria wait for the owner", since=MOMENT
)
ASKED = Question(
    id="criterion:gift-note:20261125T100000Z",
    topic="criterion",
    question="Approve the criteria?",
    options=("yes", "no"),
    asked=MOMENT,
)
TIP = "a" * 40
BASE = "b" * 40


def placed(seen: World, slug: str) -> tuple[Standing, str]:
    """Where the task `slug` stands, and its card's line."""
    counts = counted.counted(seen)
    pair = next(pair for pair in counts.placed if pair[0].record.task.slug == slug)
    found, where = pair
    return where, telling.line(found.record, where, tasks.TITLES[where.column])


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
        why="Verdict: call. Careful.",
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


def test_status_criteria_that_wait_put_the_task_in_the_owners_column_in_his_words() -> (
    None
):
    """`Status.test_criteria_that_wait_put_the_task_in_the_owners_column_in_his_words`."""
    seen = world(
        task(
            line="the criteria wait for the owner",
            status="shaping",
            hold=CRITERIA,
            questions=(ASKED,),
        )
    )
    where, line = placed(seen, "gift-note")
    assert (where.column, where.look) == ("you", "you")
    assert line == "The criteria wait for you"
    rows = pages.page(seen).frame.sidebar.waits
    assert [(row.id, row.verb) for row in rows] == [
        ("w-criterion-gift-note-20261125T100000Z", "Approve the criteria")
    ]


def test_status_criteria_he_approved_wait_for_nothing_of_his_and_the_task_is_lems() -> (
    None
):
    """`Status.test_criteria_he_approved_with_no_lead_yet_are_lems_to_start`, changed: his yes
    clears the hold (`lem criteria approve`), so the task shapes on with no row of his."""
    seen = world(task(line="the criteria are approved", status="shaping"))
    where, line = placed(seen, "gift-note")
    assert (where.column, where.look, where.label) == ("build", "lem", "Shaping")
    assert line == "Shaping: the criteria are approved"
    assert pages.page(seen).frame.sidebar.waits == ()


def test_status_since_is_when_the_task_entered_its_status_and_the_bar_shows_its_task() -> (
    None
):
    """`Status.test_since_is_when_the_task_entered_its_status_not_its_newest_block`."""
    entered = MOMENT + timedelta(minutes=10)
    running = Span(name="task", job="task 2 of 3", start=MOMENT + timedelta(minutes=30))
    seen = world(
        task(
            line="task 2 of 3",
            status="building",
            since=entered,
            plan=Plan(path="docs/plans/p.md", tasks=3),
            spans=(running,),
        )
    )
    card = tasks.tasks(seen).columns[1].cards[0]
    assert card.since.at == entered
    assert card.progress and (card.progress.at, card.progress.of) == (2, 3)
    assert card.line == "Task 2 of 3"


def test_topline_a_building_task_whose_session_is_gone_waits_for_you_on_the_top_line() -> (
    None
):
    """`TopLine.test_a_building_task_whose_session_is_gone_waits_for_you_on_the_top_line`."""
    seen = world(replace(task(line="lead: builder", status="building"), session=gone()))
    counts = counted.counted(seen)
    assert [row.key for group in counts.stacks for row in group] == [
        "session:gift-note"
    ]
    assert summary.tasks_line(counts) == "1 waits for you, 1 builds"
    assert (counts.waits, counts.count("you")) == (1, 0)


def test_topline_a_task_whose_merge_review_calls_you_is_one_on_the_top_line_and_in_the_sidebar() -> (
    None
):
    """`TopLine.test_a_task_whose_merge_review_calls_you_is_one_on_the_top_line_and_in_the_sidebar`
    and `WaitingByTask.test_a_task_whose_merge_review_calls_the_owner_is_one_entry_of_its_two_things_and_counts_once`."""
    seen = world(calling("logo-eyes", 73, 10))
    counts = counted.counted(seen)
    assert counts.things == 2
    assert summary.tasks_line(counts) == "1 waits for you"
    assert (counts.waits, counts.count("you")) == (1, 1)
    side = frame(seen, Beside()).sidebar
    assert (side.waits_count, side.waits_title) == (1, "2 things you do, in 1 task")
    assert side.waits[0].things == 2


def test_waiting_by_task_nothing_waits_no_task_and_a_count_of_0() -> None:
    """`WaitingByTask.test_nothing_waits_no_task_and_a_count_of_0`."""
    side = frame(world(task(line="lead: builder", status="building")), Beside()).sidebar
    assert (side.waits, side.waits_count) == ((), 0)
    assert side.views[1].rail_title == "Nothing waits for you"


def test_workspace_done_shows_the_newest_first_and_keeps_every_ended_task_past_its_20() -> (
    None
):
    """`Workspace.test_done_shows_the_newest_first_and_a_task_with_no_block_has_no_card` and the
    column's part of `Workspace.test_done_keeps_every_ended_task_and_the_ones_after_its_newest_20_are_the_older`."""
    ended = [
        task(
            f"task-{number}",
            "merged",
            status="landed",
            since=MOMENT + timedelta(minutes=number),
        )
        for number in range(21)
    ]
    done = tasks.tasks(world(*ended)).columns[3]
    assert [card.slug for card in done.cards] == [f"task-{n}" for n in range(20, 0, -1)]
    assert done.older and done.older.label == "1 older"
    assert done.older.href == "/studio/shop/done"


def checking(*entries: object) -> Seen:
    """A landing whose journal has `entries` after its state."""
    made = task("coupon", "the checks start", status="landing")
    journal = (*made.record.journal, *entries)
    return replace(made, record=replace(made.record, journal=journal))


def test_landing_a_landing_that_waits_says_what_for_until_its_next_event() -> None:
    """`Landing.test_a_landing_that_waits_says_what_for_until_its_next_event`,
    `WaitsBehind.test_each_why_has_its_words`, `WaitsBehind.test_a_first_of_another_repository_is_named_with_its_folder`
    and `Landing.test_a_landing_that_waits_with_no_task_ahead_keeps_its_load_and_after_words`."""
    at = MOMENT + timedelta(minutes=1)
    behind = CheckWait(at=at, reason="behind", behind="receipt", why="longer")
    other = CheckWait(
        at=at, reason="behind", behind="logo", behind_repo="/work/site", why="wanted"
    )
    after = CheckWait(at=at, reason="after", after="receipt")
    load = CheckWait(at=at, reason="load", load=7.5, start_below=6.0)
    ended = CheckEnd(
        at=at + timedelta(minutes=1), outcome="passed", say="The checks passed"
    )
    said = {
        "behind": placed(world(checking(behind)), "coupon")[1],
        "other": placed(world(checking(other)), "coupon")[1],
        "after": placed(world(checking(after)), "coupon")[1],
        "load": placed(world(checking(load)), "coupon")[1],
        "ended": placed(world(checking(behind, ended)), "coupon")[1],
    }
    assert said == {
        "behind": "Its checks wait behind receipt, which waits longer",
        "other": "Its checks wait behind logo of site, which another task waits for",
        "after": "Its checks wait a minute after the checks of receipt started",
        "load": "Waits for the load: 7.5, starts below 6.0",
        "ended": "The checks start",
    }
    feed = activity(world(checking(other))).feed
    assert next(event.text for event in feed if event.head == "The checks wait") == (
        "behind logo of site, which another task waits for"
    )


def test_landing_a_refused_run_says_that_a_builder_repairs_it_and_a_passed_one_says_nothing() -> (
    None
):
    """`Landing.test_a_refused_run_says_that_a_builder_repairs_it_and_a_passed_one_says_nothing`
    and `Landing.test_a_stopped_run_of_the_checks_is_lems_wait_for_his_word_and_no_row_of_his`."""
    at = MOMENT + timedelta(minutes=1)
    refused = world(checking(CheckEnd(at=at, outcome="refused", say="")))
    stopped = world(checking(CheckEnd(at=at, outcome="stopped", say="")))
    passed = world(checking(CheckEnd(at=at, outcome="passed", say="The checks passed")))
    where, line = placed(refused, "coupon")
    assert (where.look, where.label) == ("lem", "Checks refused")
    assert (
        line == "The checks refused the change; a builder repairs it, nothing for you"
    )
    where, line = placed(stopped, "coupon")
    assert where.label == "Checks stopped"
    assert line == (
        "The checks were stopped; the landing waits for your word. In the task's session, "
        "/lem land starts them again and /lem drop coupon drops the task"
    )
    assert counted.counted(stopped).waits == 0
    assert placed(passed, "coupon")[1] == "The checks start"


def test_waits_behind_a_stop_while_it_waited_ends_the_wait_and_reads_as_the_stopped_checks() -> (
    None
):
    """`WaitsBehind.test_a_stop_while_it_waited_ends_the_wait_and_reads_as_the_stopped_checks_with_no_count`
    and `WaitsBehind.test_behind_goes_before_a_minute_after_the_last_start`."""
    at = MOMENT + timedelta(minutes=1)
    wait = CheckWait(at=at, reason="behind", behind="receipt", why="first")
    stop = CheckEnd(at=at + timedelta(minutes=2), outcome="stopped", say="")
    where, line = placed(world(checking(wait, stop)), "coupon")
    assert where.label == "Checks stopped"
    assert line.startswith("The checks were stopped")
    later = CheckWait(
        at=at + timedelta(minutes=3), reason="behind", behind="logo", why="first"
    )
    assert placed(world(checking(wait, later)), "coupon")[1] == (
        "Its checks wait behind logo, which is first in the line"
    )


def test_search_lists_the_columns_then_the_parked_then_every_ended_task_newest_first() -> (
    None
):
    """The tasks' part of `Search.test_criterion_4_the_order_the_columns_then_the_parked_then_every_ended_task_newest_first_then_the_backlog_by_worth`,
    `Search.test_criterion_2_every_task_a_parked_one_and_an_ended_one_done_draws_no_card_for_and_every_backlog_item`
    and `Search.test_criterion_5_each_chip_says_its_place_and_its_state_in_the_color_of_its_column`."""
    ended = [
        task(
            f"old-{number}",
            "merged",
            status="landed",
            since=MOMENT + timedelta(minutes=number),
        )
        for number in range(21)
    ]
    parked = task("put-aside", "parked", status="building", hold=Parked(since=MOMENT))
    seen = world(
        task("builds", "lead: builder", status="building"),
        task("checks", "the checks start", status="landing"),
        task(
            "asks",
            "the criteria wait for the owner",
            status="shaping",
            hold=CRITERIA,
            questions=(replace(ASKED, id="criterion:asks:20261125T100000Z"),),
        ),
        parked,
        *ended,
    )
    rows = pages.page(seen).frame.search.rows
    keys = [row.key for row in rows]
    assert keys[:4] == ["asks", "builds", "checks", "put-aside"]
    assert keys[4:] == [f"old-{n}" for n in range(20, -1, -1)]
    chips = {row.key: (row.chip, row.look, row.open) for row in rows[:5]}
    assert chips == {
        "asks": ("Waits for you · shaping", "you", True),
        "builds": ("Building · building", "lead", True),
        "checks": ("Checks and review · landing", "gate", True),
        "put-aside": ("parked", "quiet", True),
        "old-20": ("landed 2026-11-25", "done", False),
    }


def test_the_frames_line_counts_the_owners_waits_as_the_sidebar_does() -> None:
    """The top line counts the tasks with a row of what waits, never the column: a card of the
    session waits for him while its task still builds."""
    card = Question(
        id="card:builds:PAGE",
        topic="card",
        question="Which one?",
        options=("a", "b"),
        asked=NOW - timedelta(minutes=5),
    )
    seen = world(task("builds", "lead: builder", status="building", questions=(card,)))
    counts = counted.counted(seen)
    assert (counts.waits, counts.count("you"), counts.count("build")) == (1, 0, 1)
    state = StateNoted(at=MOMENT, status="building")
    assert state.line is None
