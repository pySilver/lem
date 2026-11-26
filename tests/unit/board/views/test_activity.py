"""The view Activity (`board_pages.activity_page` on `main`): the chart Where the time went, one
row for each task of the day with a bar for each state it held, its axis, its line of now and
its legend; the feed of every task, the newest first; and the page of a new task."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from fakes.records import record
from lem.board.inputs.layout import Viewer
from lem.board.views.activity import axis, feed, new_task, stretches, ticks, view
from lem.board.views.activity.journal_told import told_of
from lem.records.journal.merge import RefusalNoted
from lem.records.journal.task import CriteriaNoted, OwnerAct, StateNoted, Summary
from lem.records.landing.merge import Refused
from unit.board.views.afternoon import world as afternoon
from unit.board.views.timed import VIEWER, at, named, seen, task, world

if TYPE_CHECKING:
    from pathlib import Path


def test_only_a_copied_entry_names_the_task_it_came_from() -> None:
    resumed = record("gift-note-2", resumed_from="gift-note").task
    carried = CriteriaNoted(
        at=at("10:01"), event="approved", by="owner", number=1, carried_from="gift-note"
    )
    later = CriteriaNoted(at=at("10:04"), event="approved", by="owner", number=2)
    ordinary = OwnerAct(at=at("10:02"), act="approve", via="local")
    refusal = Refused(
        at=at("10:03"),
        by="merger",
        source="lem",
        kind="base",
        tip="a" * 40,
        line="origin/main moved after the checks ran",
    )
    refused = RefusalNoted(at=refusal.at, refusal=refusal)
    assert told_of(carried, resumed)[0].sub == "carried over from gift-note"
    assert "carried over" not in told_of(later, resumed)[0].sub
    assert "carried over" not in told_of(ordinary, resumed)[0].sub
    assert "carried over" not in told_of(refused, resumed)[0].sub


def test_the_afternoons_chart_draws_each_task_of_the_day_from_its_first_move(
    tmp_path: Path,
) -> None:
    shown = view.activity(afternoon(tmp_path))
    assert shown.day == "today"
    assert [tick.clock for tick in shown.ticks] == [
        "05:55",
        "07:55",
        "09:55",
        "11:55",
        "13:55",
        "15:55",
        "17:55",
    ]
    assert (shown.ticks[0].first, shown.ticks[-1].last) == (True, True)
    # twelve hours from the refund line's first move at 05:55, and now at 16:00
    assert shown.now == 84.028
    assert [lane.slug for lane in shown.lanes] == [
        "refund-line-on-receipt",
        "order-date-on-invoice",
        "fee-notice-to-merchants",
        "why-export-is-slow",
        "gift-note-in-export",
        "refund-rounding",
        "footer-terms-typo",
        "stock-on-product-page",
        "coupon-has-a-slug",
        "cart-total-after-coupon",
        "export-check-by-chance",
    ]
    receipt = shown.lanes[0]
    assert receipt.task.href == (
        "/studio/shop/tasks/refund-line-on-receipt/timeline?in=activity"
    )
    assert [bar.title for bar in receipt.stretches] == [
        "Waits for you · You · 05:55 to 06:04 · 9m 00s",
        "Building · The agent · 06:04 to 08:00 · 1h 56m",
        "Ready for its checks · Lem · 08:00 to 08:01 · 1m 00s",
        "Checks and review · The checks · 08:01 to 08:32 · 31m",
        "Waits for the merge · You · 08:32 to now · 7h 28m",
    ]
    invoice = shown.lanes[1].stretches[-1]
    assert (invoice.status, invoice.dot, invoice.width, invoice.title) == (
        "landed",
        True,
        0,
        "Landed at 13:20",
    )


def test_a_bar_that_runs_moves_while_its_state_moves(tmp_path: Path) -> None:
    lanes = {lane.slug: lane for lane in view.activity(afternoon(tmp_path)).lanes}
    builds = lanes["refund-rounding"].stretches[-1]
    assert (builds.status, builds.look, builds.live) == ("building", "lead", True)
    # an open pull request's wait does not move: nobody works on it
    waits = lanes["refund-line-on-receipt"].stretches[-1]
    assert (waits.status, waits.live, waits.left + waits.width) == (
        "open",
        False,
        84.028,
    )


def test_the_legend_has_an_entry_for_each_look_and_queued_and_ready_their_own(
    tmp_path: Path,
) -> None:
    shades = view.activity(afternoon(tmp_path)).shades
    assert [(shade.look, shade.status, shade.label) for shade in shades] == [
        ("quiet", "queued", "Queued"),
        ("lead", None, "Building"),
        ("you", None, "Waits for you · Waits for the merge"),
        ("gate", "ready", "Ready for its checks"),
        ("gate", None, "Checks and review"),
        ("quiet", None, "Parked"),
    ]
    assert shades[2].title == "Waits for you: You acts\nWaits for the merge: You acts"


def test_the_feed_counts_every_row_and_lists_the_newest_first(tmp_path: Path) -> None:
    shown = view.activity(afternoon(tmp_path))
    assert shown.events == "137 events"
    first = shown.feed[0]
    assert (first.id, first.head, first.text, first.at.shown) == (
        "ev-export-check-by-chance-1",
        "Parked",
        "the owner parked it: the check waits for the new export",
        "15:54",
    )
    assert first.task is not None
    assert first.task.href == (
        "/studio/shop/tasks/export-check-by-chance/timeline?in=activity"
    )
    moments = [row.at.at for row in shown.feed]
    assert moments == sorted(moments, reverse=True)
    command = next(row for row in shown.feed if row.mono)
    assert (command.head, command.text, command.sub) == (
        "Check passed",
        "make lint",
        "All checks passed",
    )


def test_a_feed_shows_its_newest_200_rows_and_says_so() -> None:
    moves = tuple(
        StateNoted(at=at("01:00") + timedelta(minutes=minute), status="building")
        for minute in range(205)
    )
    rows, count = feed.everything(world(seen(task(*moves, status="building"))))
    assert (len(rows), count, feed.count_line(count)) == (
        200,
        205,
        "205 events · the newest 200",
    )
    assert rows[0].id == "ev-gift-note-204"
    assert feed.count_line(1) == "1 event"


def test_a_row_appears_when_a_task_writes_its_first_state() -> None:
    quiet = view.activity(world(seen(task(status="queued"))))
    assert (quiet.day, quiet.lanes, quiet.ticks, quiet.now) == ("today", (), (), None)
    assert quiet.events == "0 events"


def test_a_task_that_ended_on_another_day_has_no_row_and_one_of_today_has_no_line_of_now() -> (
    None
):
    old = named(
        "old-one",
        task(
            StateNoted(at=at("09:00") - timedelta(days=1), status="landed"),
            status="landed",
            since=at("09:00") - timedelta(days=1),
        ),
    )
    landed = task(
        StateNoted(at=at("10:00"), status="building"),
        StateNoted(at=at("10:30"), status="landed"),
        status="landed",
        since=at("10:30"),
    )
    shown = view.activity(world(seen(old), seen(landed)))
    assert [lane.slug for lane in shown.lanes] == ["gift-note"]
    # the axis ends at the last move: thirty minutes from 10:00
    assert ([tick.clock for tick in shown.ticks][::3], shown.now) == (
        ["10:00", "10:15", "10:30"],
        None,
    )


def test_a_move_to_the_state_before_it_goes_on_its_stretch() -> None:
    made = task(
        StateNoted(at=at("10:00"), status="building", line="task 1 of 2"),
        StateNoted(at=at("10:20"), status="building", line="task 2 of 2"),
        StateNoted(at=at("10:40"), status="ready"),
        status="ready",
    )
    assert stretches.stretches(made, at("11:00")) == (
        stretches.Stretch("building", at("10:00"), at("10:40")),
        stretches.Stretch("ready", at("10:40"), at("11:00"), open=True),
    )


def test_a_summary_with_a_newer_state_dates_the_stretch_from_the_run_its_past_began() -> (
    None
):
    """`main`'s Summary.test_a_summary_with_a_newer_state_dates_since_from_the_run_its_past_
    began, as far as a `Summary` still holds it: the card's `since` is the record's own
    (`Task.since`), and the stretch of a summary's last state goes on through a newer move to
    the same state, so it still dates from the run its past began."""
    past = Summary(
        at=at("12:00"),
        statuses=("building", "ready", "landing", "open", "landed"),
        last_state=StateNoted(at=at("10:15"), status="landed"),
        first=at("09:01"),
        last=at("10:15"),
        entries=60,
        pull=12,
    )
    cleaned = StateNoted(
        at=at("12:40"),
        status="landed",
        line="main: pull request 12 is merged, and the session cleaned up",
    )
    made = task(past, cleaned, status="landed", since=at("10:15"))
    assert stretches.stretches(made, at("13:00")) == (
        stretches.Stretch("landed", at("10:15"), at("12:40")),
    )


def test_an_axis_reads_well_and_names_seconds_under_six_minutes_and_a_new_days_date() -> (
    None
):
    assert [axis.nice(seconds) for seconds in (30, 61, 2700, 2701, 90000)] == [
        60.0,
        120.0,
        2700.0,
        3600.0,
        172800.0,
    ]
    # three minutes take the five of NICE_MINUTES, in ticks of 50 seconds
    short = axis.axis_of(at("10:00"), at("10:03"))
    assert [tick.clock for tick in ticks.ticks(short, UTC)][:3] == [
        "10:00:00",
        "10:00:50",
        "10:01:40",
    ]
    # six hours from 21:00, in ticks of an hour: only the first past midnight names its date
    night = axis.axis_of(at("21:00"), at("23:59") + timedelta(hours=3))
    shown = ticks.ticks(night, UTC)
    assert [(tick.date, tick.clock) for tick in shown][3:6] == [
        ("Nov 23", "00:00"),
        (None, "01:00"),
        (None, "02:00"),
    ]
    assert ticks.day(at("09:00"), at("09:00") + timedelta(days=1), UTC) == "Nov 22"
    assert axis.coarse(datetime(2026, 11, 22, 10, 0, 1, tzinfo=UTC)) == at("10:00:15")


def test_the_page_of_a_new_task_has_its_form_only_where_it_may_act() -> None:
    page = new_task.new_task(world())
    assert page.cancel.href == "/h/w/"
    assert page.form is not None
    assert (page.form.action, page.form.label, page.form.busy) == (
        "/h/w/tasks",
        "Start the task",
        "Starting…",
    )
    assert page.form.box is not None
    assert (page.form.box.name, page.form.box.id, page.form.box.rows) == (
        "words",
        "nt-words-w",
        5,
    )
    away = Viewer(host="h", workspace="w", base="/h/w", may_act=False)
    assert new_task.new_task(world(viewer=away)).form is None
    assert VIEWER.may_act
