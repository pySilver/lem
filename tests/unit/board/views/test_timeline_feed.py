"""The rows of a task's tab Timeline (`board_task.feed_card` and `timeline_tab` on `main`): every
row of the task, the newest first, each with its time; the newest move names only its state; and
a task whose journal became one summary has its tab say that its timeline went with it."""

from lem.app.sessions.acts import Open, Stopped, Wake
from lem.board.views.timeline import view
from lem.records.journal.landing import CheckEnd
from lem.records.journal.task import StateNoted, Summary
from unit.board.views.timed import at, seen, task, world

TIP = "5ccc53d36" + "0" * 31


def guarded() -> view.Timeline:
    """The Timeline of #37 at 13:00 (`main`'s StoppedRow.stopped): the landing's checks ended at
    10:54, the status message at 11:39, a fresh session at 11:49, its status message at 12:34
    and its stop at 12:44."""
    made = task(
        StateNoted(
            at=at("10:15"),
            status="landing",
            line="the base moved: the checks run again",
        ),
        CheckEnd(at=at("10:54"), outcome="passed", say="", seconds=2156, tip=TIP),
        status="landing",
    )
    acts = (
        Open(
            at=at("01:33"), session="S1", name="gift-note", phase="land", why="handoff"
        ),
        Wake(at=at("11:39"), session="S1", why="status"),
        Open(
            at=at("11:49"), session="S2", name="gift-note", phase="land", why="stopped"
        ),
        Wake(at=at("11:49"), session="S1", why="replaced"),
        Wake(at=at("12:34"), session="S2", why="status"),
        Stopped(at=at("12:44"), session="S2"),
    )
    return view.timeline(world(seen(made, *acts)), "gift-note")


def test_the_timeline_says_each_act_of_the_guard_with_its_time() -> None:
    """`main`'s StoppedRow.test_the_timeline_says_each_act_of_the_guard_with_its_time: the status
    message, the fresh session that took the task over, the notice to the old one, and the stop,
    each once with its time in the task's rows."""
    rows = guarded().feed
    said = {(row.head, row.at.shown): row for row in rows}
    status = said["The board’s server asked the task’s session for its status", "11:39"]
    assert status.text is not None
    assert "no sign of work for 45 minutes" in status.text
    fresh = said["A fresh session took the task over", "11:49"]
    assert fresh.sub is not None
    assert "beside the one that stopped" in fresh.sub
    assert (
        "The board’s server told the old session that a fresh one replaced it",
        "11:49",
    ) in said
    stop = said["The task’s session stopped", "12:44"]
    assert stop.look == "bad"
    assert [row.at.shown for row in rows].count("12:44") == 1


def test_the_rows_are_the_newest_first_and_the_newest_move_names_only_its_state() -> (
    None
):
    shown = guarded()
    # six acts, the move, and the checks' end
    assert shown.events == "8 events"
    assert [row.id for row in shown.feed][:2] == ["tev-7", "tev-6"]
    move = next(row for row in shown.feed if row.head == "Checks and review")
    assert (move.text, move.sub, move.task) == (None, None, None)


def test_a_summarized_task_says_its_timeline_went_with_its_events() -> None:
    past = Summary(
        at=at("12:00"),
        statuses=("building", "landed"),
        last_state=StateNoted(at=at("10:15"), status="landed"),
        first=at("09:01"),
        last=at("10:15"),
        entries=60,
    )
    shown = view.timeline(world(seen(task(past, status="landed"))), "gift-note")
    assert (shown.time, shown.feed, shown.events) == (None, (), None)
    assert shown.went is not None
    assert shown.went.said.startswith(
        "Its timeline and its events went with its events"
    )
    assert shown.went.artifacts.href == "/h/w/tasks/gift-note/artifacts"
