"""The guard of a stopped session and the row of its stop, on the events of 2026-11-22
(merge-leaves-board-lock, #37), and a held task whose session works on the owner's answer
(`main`'s `tests/unit/test_board_model.py`: `StoppedSession`, `StoppedRow`, `SessionAtWork`):
each test names the old case it stands for.

The checks of #37 ended at 10:54, its session stayed live with an agent in its pane, and its own
newest turn was at 10:15:42. `main`'s step came with the agterm session it acts on; the rebuild's
guard acts on the task's newest open (`guard_look.looked`), so a step here is its kind and the
moment it is due from.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from msgspec.structs import replace

from fakes.records import record
from lem.app.owner import scope
from lem.app.sessions import guard_look
from lem.app.sessions.acts import Close, Open, Stopped, Wake, Worked
from lem.app.sessions.guard_due import due
from lem.app.sessions.guard_rule import ANSWER_SECONDS, GUARDED, QUIET_SECONDS, Facts
from lem.board.views import owed, sessions, standing, tasks, telling
from lem.board.views.panel import heads, now, opening
from lem.board.views.panel import waiting as panel_waiting
from lem.board.views.waits import view as waits_view
from lem.board.views.world import Seen
from lem.model.owner.looks import Session
from lem.records.holds import BreakerHold, OwnerHold, Parked
from lem.records.journal.landing import CheckWait
from lem.records.journal.task import OwnerAct, StateNoted
from unit.board.views.small import world

if TYPE_CHECKING:
    from lem.app.sessions.acts import Act, WakeWhy
    from lem.board.inputs.waits import Wait
    from lem.records.journal.entry import Entry

SLUG = "gift-note"
NEWEST_TURN = "10:15:42"


def hm(text: str) -> datetime:
    """A moment of 2026-11-22 in UTC, `HH:MM` or `HH:MM:SS`."""
    parts = [int(part) for part in text.split(":")]
    hour, minute, second = (*parts, 0)[:3]
    return datetime(2026, 11, 22, hour, minute, second, tzinfo=UTC)


def work(text: str) -> StateNoted:
    """An entry of the task's journal at `text`: work of the task."""
    return StateNoted(at=hm(text), status="landing", line="the checks run")


def opened(text: str, session: str, why: str) -> Open:
    return Open(at=hm(text), session=session, name=SLUG, phase="land", why=why)


def wake(
    text: str, session: str = "S1", *, unread: bool = False, why: WakeWhy = "status"
) -> Wake:
    return Wake(at=hm(text), session=session, why=why, unread=unread)


def stop(text: str, session: str = "S1", *, unread: bool = False) -> Stopped:
    return Stopped(at=hm(text), session=session, unread=unread)


def worked(text: str, turn: str) -> Worked:
    return Worked(at=hm(text), session="S1", turn=hm(turn))


# The landing of #37: its session opened at 01:33, the checks ran from 10:15 and ended at 10:54.
LANDING: tuple[Act | Entry, ...] = (
    opened("01:33", "S1", "handoff"),
    work("10:15"),
    work("10:18"),
    work("10:22"),
    work("10:54"),
)
WOKEN = (*LANDING, wake("11:39"))
UNREAD_WOKEN = (*LANDING, wake("11:39", unread=True))
RESTARTED = (*WOKEN, opened("11:49", "S2", "stopped"), wake("11:49", why="replaced"))
UNREAD_STOPPED = (*UNREAD_WOKEN, stop("11:49", unread=True))
# The fresh session's own status message at 12:34, and its stop at 12:44.
STOPPED = (*RESTARTED, wake("12:34", "S2"), stop("12:44", "S2"))


def split(events: tuple[Act | Entry, ...]) -> tuple[tuple[Act, ...], tuple[Entry, ...]]:
    """Lem's acts on the task's sessions, and the entries of its journal."""
    found: list[Act] = []
    entries: list[Entry] = []
    for one in events:
        if isinstance(one, Open | Close | Stopped | Wake | Worked):
            found.append(one)
        else:
            entries.append(one)
    return tuple(found), tuple(entries)


def made(events: tuple[Act | Entry, ...], **task: object) -> Seen:
    """The task with the journal and Lem's acts of `events`, in `landing` unless named, with a
    live session."""
    found, entries = split(events)
    fields: dict[str, object] = {
        "status": "landing",
        "opened": hm("01:33"),
        "since": hm("10:15"),
    } | task
    made_record = record(SLUG, **fields)
    return Seen(
        record=replace(made_record, journal=entries),
        acts=found,
        session=Session(live=True, since=hm("01:33")),
    )


def step(
    events: tuple[Act | Entry, ...],
    *,
    at: str,
    sign: str | None = NEWEST_TURN,
    read: bool = True,
    shell: bool = False,
    alive: bool = True,
) -> tuple[str, datetime] | None:
    """The guard's step due at `at` and the moment it is due from, or None, with the signs
    of the session as `lem session list` gives them."""
    seen = made(events)
    line = guard_look.timeline(seen.record, seen.acts)
    facts = Facts(
        guarded=True,
        alive=alive,
        shell=shell,
        read=read,
        sign=hm(sign) if sign else None,
    )
    found = due(line, facts, hm(at))
    return (found.step, found.since) if found else None


def stands(events: tuple[Act | Entry, ...]) -> bool:
    """Whether the task's newest stop stands."""
    seen = made(events)
    return guard_look.timeline(seen.record, seen.acts).stop_stands() is not None


LIVE = Session(live=True, since=hm("01:33"))


def board(
    events: tuple[Act | Entry, ...], session: Session = LIVE, **task: object
) -> Seen:
    """The task as the board sees it: its session and the stop that stands over it."""
    seen = replace(made(events, **task), session=session)
    found = sessions.stop_of(seen.record, seen.acts, seen.session)
    return replace(seen, stop=found)


def rows(seen: Seen, at: str) -> list[tuple[str, str]]:
    """The rows of the task of `seen` at `at`: each kind and key."""
    return [(row.kind, row.key) for row in owed.rows(world(seen, now=hm(at)))]


def waits(seen: Seen, at: str) -> list[Wait]:
    """The rows of Waits for you of the task of `seen` at `at`."""
    shown = waits_view.waits(world(seen, now=hm(at)))
    return [one for stack in shown.stacks for one in stack.waits]


UNREAD = {"sign": None, "read": False}


def test_45_minutes_after_the_newest_sign_the_status_message_is_due() -> None:
    """`main`'s StoppedSession.test_45_minutes_after_the_newest_sign_the_status_message_is_due:
    the newest sign is the end of the checks, newer than the session's own turn at 10:15, and
    a newer turn moves the clock."""
    assert step(LANDING, at="11:38:59") is None
    assert step(LANDING, at="11:39") == ("status", hm("10:54"))
    assert step(LANDING, at="15:37") == ("status", hm("10:54"))
    assert step(LANDING, at="11:39", sign="11:30") is None
    assert step(LANDING, at="12:15", sign="11:30") == ("status", hm("11:30"))


def test_a_fresh_session_that_stops_too_is_stopped_once_and_not_restarted() -> None:
    """`main`'s StoppedSession.test_a_fresh_session_that_stops_too_is_logged_once_and_not_
    restarted."""
    again = (*RESTARTED, wake("12:37", "S2"))
    assert step(again, at="12:46", sign="11:52") is None
    assert step(again, at="12:47", sign="11:52") == ("stopped", hm("12:37"))
    stopped = (*again, stop("12:47", "S2"))
    for at in ("12:47:20", "13:40", "17:00"):
        assert step(stopped, at=at, sign="11:52") is None, at


def test_a_quiet_task_whose_signs_do_not_read_is_woken() -> None:
    """`main`'s StoppedSession.test_a_quiet_task_whose_signs_do_not_read_is_woken_or_shown:
    #37 as it ran, its signs unread all day, nearly five hours after its checks ended."""
    assert step(LANDING, at="15:37", **UNREAD) == ("status", hm("10:54"))


def test_a_second_unread_period_gets_its_own_record_once() -> None:
    """`main`'s StoppedSession.test_a_second_unread_period_gets_its_own_record_once."""
    again = (
        *UNREAD_STOPPED,
        worked("11:56", "11:55"),
        wake("12:40", unread=True),
        stop("12:50", unread=True),
    )
    assert rows(board(again), "12:51") == [("stopped", f"stopped:{SLUG}")]
    assert step(again, at="13:01", sign="13:00") == ("worked", hm("13:00"))
    twice = (*again, worked("13:01", "13:00"))
    assert step(twice, at="13:02", sign="13:00") is None
    assert rows(board(twice), "13:02") == []


def test_a_shell_command_that_runs_is_work_and_a_session_that_is_not_live_gets_nothing() -> (
    None
):
    """`main`'s StoppedSession.test_a_shell_command_that_runs_is_work_and_a_session_that_is_
    not_live_gets_nothing: the checks of a landing run for 50 minutes with no entry, and
    their shell command is the sign."""
    checks = LANDING[:3]
    assert step(checks, at="11:08", shell=True) is None
    assert step(checks, at="11:08") == ("status", hm("10:18"))
    assert step(LANDING, at="15:37", alive=False) is None


def test_a_sign_in_the_10_minutes_ends_that_stop() -> None:
    """`main`'s StoppedSession.test_a_sign_in_the_10_minutes_ends_that_stop: a turn or an
    entry of the task answers the message, in its second too; the owner's act is no work;
    a later quiet of 45 minutes is a new stop with its own message."""
    assert step(WOKEN, at="11:49", sign="11:41") is None
    assert step((*WOKEN, work("11:44")), at="11:49") is None
    assert step(WOKEN, at="11:49", sign="11:39") is None
    clicked = OwnerAct(at=hm("11:45"), act="open", via="local")
    assert step((*WOKEN, clicked), at="11:49") == ("restart", hm("11:39"))
    assert step(WOKEN, at="12:26", sign="11:41") == ("status", hm("11:41"))


def test_a_stop_stands_until_an_entry_of_the_task_or_a_session_opens() -> None:
    """`main`'s StoppedSession.test_a_stop_stands_until_a_work_event_or_a_session_opens: the
    owner's click is no work and no open."""
    stopped = (*RESTARTED, wake("12:37", "S2"), stop("12:47", "S2"))
    assert stands(stopped)
    assert stands((*stopped, OwnerAct(at=hm("12:50"), act="open", via="local")))
    assert not stands((*stopped, opened("12:50", "S3", "stopped")))
    assert not stands((*stopped, work("12:50")))
    assert not stands(RESTARTED)


def test_the_guard_watches_building_ready_and_landing_only() -> None:
    """`main`'s StoppedSession.test_a_task_out_of_building_ready_and_landing_gets_nothing: a
    task in any other status gets no step; one in these three with a hold neither
    (`unit.sessions.test_acts.test_the_guard_watches_no_task_with_a_hold`)."""
    assert frozenset(("building", "ready", "landing")) == GUARDED
    unwatched = Facts(guarded=False, alive=True, read=True, sign=hm(NEWEST_TURN))
    seen = made(LANDING)
    line = guard_look.timeline(seen.record, seen.acts)
    assert due(line, unwatched, hm("15:37")) is None


def test_a_turn_answers_only_the_status_message_that_the_standing_stop_followed() -> (
    None
):
    """`main`'s StoppedSession.test_a_turn_answers_only_the_status_message_that_the_standing_
    stop_followed: the unread message at 11:39 and its stop at 11:49; a turn at 11:55; the
    readable clock's message at 12:40 and its stop at 12:50. The turn came before the
    message of 12:40, so it answers nothing that stands, recorded or not."""
    twice = (*UNREAD_STOPPED, wake("12:40"), stop("12:50"))
    assert step(twice, at="17:00", sign="11:55") is None
    assert stands(twice)
    assert rows(board(twice), "17:00") == [("stopped", f"stopped:{SLUG}")]
    logged = (*twice, worked("12:51", "11:55"))
    assert stands(logged)
    assert rows(board(logged), "17:00") == [("stopped", f"stopped:{SLUG}")]
    assert step(logged, at="17:00", sign="11:55") is None
    assert step(twice, at="13:00", sign="12:55") is None


def test_a_turn_read_after_an_unread_stop_is_put_on_record_once_and_the_stop_goes() -> (
    None
):
    """`main`'s StoppedSession.test_a_turn_read_after_an_unread_stop_is_logged_once_and_the_
    stop_goes, with the record the rebuild writes (`main` held it back one release): the
    look after the turn records it, and the clock counts from the turn."""
    logged = (*UNREAD_STOPPED, worked("11:56", "11:55"))
    assert not stands(logged)
    assert rows(board(logged), "11:57") == []
    assert step(UNREAD_STOPPED, at="11:54") is None
    assert step(UNREAD_STOPPED, at="11:56", sign="11:55") == ("worked", hm("11:55"))
    for at in ("11:57", "12:39"):
        assert step(logged, at=at, sign="11:55") is None, at
    assert step(logged, at="12:40", sign="11:55") == ("status", hm("11:55"))
    assert step(logged, at="12:39:59", **UNREAD) is None
    assert step(logged, at="12:40", **UNREAD) == ("status", hm("11:55"))
    answered = (*logged, wake("12:40"))
    assert rows(board(answered), "13:00") == []


def test_a_turn_read_between_two_unread_looks_keeps_the_stop_from_coming() -> None:
    """`main`'s StoppedSession.test_a_turn_read_between_two_unread_looks_keeps_the_stop_from_
    being_logged: a look at 11:45 reads a turn at 11:40, one at 11:49 does not read."""
    logged = (*UNREAD_WOKEN, worked("11:45", "11:40"))
    assert step(logged, at="11:49", **UNREAD) is None
    assert step(UNREAD_WOKEN, at="11:45", sign="11:40") == ("worked", hm("11:40"))
    assert step(logged, at="12:24:59", **UNREAD) is None
    assert step(logged, at="12:25", **UNREAD) == ("status", hm("11:40"))
    assert step(UNREAD_WOKEN, at="11:45", sign="11:39") == ("worked", hm("11:39"))
    assert step(UNREAD_WOKEN, at="11:45", sign="11:30") is None
    assert step(UNREAD_WOKEN, at="11:49", **UNREAD) == ("stopped", hm("11:39"))


def test_an_entry_after_the_restart_makes_a_new_restart_possible() -> None:
    """`main`'s StoppedSession.test_a_work_event_after_the_restart_makes_a_new_restart_
    possible."""
    later = (*RESTARTED, work("11:55"), work("11:58"), wake("12:43", "S2"))
    assert step(later, at="12:53", sign="11:58") == ("restart", hm("12:43"))


def test_after_the_record_a_quiet_session_gets_a_stop_never_a_restart() -> None:
    """`main`'s StoppedSession.test_after_the_record_a_quiet_session_gets_a_stop_never_a_
    restart: in the run of work in which a stop of the task stood, Lem opens no fresh session
    by itself; a readable session with no stop before keeps its restart."""
    logged = (*UNREAD_STOPPED, worked("12:01", "12:00"), wake("12:45"))
    assert step(logged, at="12:54:59", sign="12:00") is None
    assert step(logged, at="12:55", sign="12:00") == ("stopped", hm("12:45"))
    assert step(WOKEN, at="11:49") == ("restart", hm("11:39"))


def test_criterion_1_signs_that_do_not_read_get_the_message_45_minutes_after_the_newest_entry() -> (
    None
):
    """`main`'s StoppedSession.test_criterion_1_signs_that_do_not_read_get_the_message_45_
    minutes_after_the_newest_event: a turn's time beside signs that do not read is no sign;
    no agent in the pane, or a shell command that runs, gets nothing."""
    assert step(LANDING, at="11:38:59", **UNREAD) is None
    assert step(LANDING, at="11:39", **UNREAD) == ("status", hm("10:54"))
    assert step(LANDING, at="11:39", sign="11:30", read=False) == (
        "status",
        hm("10:54"),
    )
    assert step(LANDING, at="11:39", alive=False, **UNREAD) is None
    assert step(LANDING, at="11:39", shell=True, **UNREAD) is None


def test_criterion_2_ten_minutes_after_the_message_signs_that_do_not_read_give_the_stop() -> (
    None
):
    """`main`'s StoppedSession.test_criterion_2_ten_minutes_after_the_message_signs_that_do_
    not_read_give_the_stop_never_a_restart: once, and a stop that stands is no restart when
    the signs read again."""
    assert step(UNREAD_WOKEN, at="11:48:59", **UNREAD) is None
    assert step(UNREAD_WOKEN, at="11:49", **UNREAD) == ("stopped", hm("11:39"))
    assert step(UNREAD_WOKEN, at="15:37", **UNREAD) == ("stopped", hm("11:39"))
    for at in ("11:49:20", "11:50", "17:00"):
        assert step(UNREAD_STOPPED, at=at, **UNREAD) is None, at
    assert step(UNREAD_STOPPED, at="11:50") is None
    assert stands(UNREAD_STOPPED)


def test_criterion_3_an_entry_of_the_task_ends_the_wait_and_in_one_second_comes_after_the_stop() -> (
    None
):
    """`main`'s StoppedSession.test_criterion_3_a_work_event_ends_the_wait_and_the_guards_own_
    message_is_none, changed: in one second Lem's acts come before the task's entries
    (`guard_look.timeline`), where `main` read the log's order."""
    block = work("11:42")
    assert step((*UNREAD_WOKEN, block), at="11:49", **UNREAD) is None
    assert step((*UNREAD_WOKEN, block), at="12:26:59", **UNREAD) is None
    assert step((*UNREAD_WOKEN, block), at="12:27", **UNREAD) == ("status", hm("11:42"))
    assert rows(board((*UNREAD_WOKEN, block)), "11:49") == []
    raced = (*UNREAD_WOKEN, work("11:49"), stop("11:49", unread=True))
    assert not stands(raced)
    assert rows(board(raced), "11:50") == []
    assert step(raced, at="12:33:59", **UNREAD) is None
    assert step(raced, at="12:34", **UNREAD) == ("status", hm("11:49"))


def test_criterion_4_a_readable_stop_and_a_newer_turn_still_give_the_status_message() -> (
    None
):
    """`main`'s StoppedSession.test_criterion_4_a_readable_stop_and_a_newer_turn_still_give_
    the_status_message."""
    stopped = (*RESTARTED, wake("12:37", "S2"), stop("12:47", "S2"))
    assert step(stopped, at="13:44", sign="13:00") is None
    assert step(stopped, at="13:45", sign="13:00") == ("status", hm("13:00"))


def test_each_clock_counts_only_the_status_message_it_sent() -> None:
    """`main`'s StoppedSession.test_each_clock_counts_only_the_status_message_it_sent: the
    message before a stop that stands counts for both clocks."""
    assert step(UNREAD_WOKEN, at="11:49", sign="11:30") is None
    assert step(UNREAD_WOKEN, at="12:15", sign="11:30") == ("status", hm("11:30"))
    assert step(WOKEN, at="12:40", sign="12:30", read=False) == ("status", hm("10:54"))
    again = (*WOKEN, wake("12:40", unread=True))
    assert step(again, at="12:49:59", sign="12:30", read=False) is None
    assert step(again, at="12:50", sign="12:30", read=False) == ("stopped", hm("12:40"))
    stopped = (*RESTARTED, wake("12:37", "S2"), stop("12:47", "S2"))
    for at in ("13:40", "17:00"):
        assert step(stopped, at=at, **UNREAD) is None, at


def test_the_fresh_sessions_clock_starts_at_its_open() -> None:
    """`main`'s StoppedSession.test_the_fresh_sessions_clock_starts_at_its_open."""
    assert step(RESTARTED, at="11:49:20", sign=None) is None
    assert step(RESTARTED, at="11:59", sign=None) is None
    assert step(RESTARTED, at="12:34", sign=None) == ("status", hm("11:49"))
    assert step(RESTARTED, at="12:37", sign="11:52") == ("status", hm("11:52"))


def test_the_numbers_are_the_owners() -> None:
    """`main`'s StoppedSession.test_the_numbers_are_the_owners: 45 minutes, then 10."""
    assert (QUIET_SECONDS, ANSWER_SECONDS) == (45 * 60, 10 * 60)


def test_the_record_of_a_turn_changes_no_step_of_the_landing_and_no_fact_of_its_card() -> (
    None
):
    """`main`'s StoppedSession.test_the_record_of_a_turn_changes_no_step_of_the_landing and
    StoppedSession.test_the_record_of_a_turn_is_no_work_and_no_fact_of_the_card, changed: the
    record of a turn is an act of Lem on the task's sessions, beside its journal, so no
    reader of the journal folds it; the guard's timeline holds it as no work."""
    load = CheckWait(at=hm("10:19"), reason="load", load=12, start_below=5)
    waiting = (
        *LANDING[:3],
        load,
        wake("11:39", unread=True),
        stop("11:49", unread=True),
    )
    record_of_turn = worked("11:56", "11:55")
    said = []
    for events in (waiting, (*waiting, record_of_turn)):
        seen = made(events)
        where = standing.standing(seen, ())
        line = telling.line(seen.record, where, tasks.TITLES[where.column])
        said.append((where, line, heads.now_head(seen)))
    assert said[0] == said[1]
    assert said[0][2] == "Waits for the load: 12, starts below 5"
    seen = made((*UNREAD_STOPPED, record_of_turn))
    kinds = [one.kind for one in guard_look.timeline(seen.record, seen.acts).events]
    assert kinds.count("work") == 4
    assert kinds[-1] == "worked"


def test_a_stop_is_a_row_with_the_button_that_opens_a_fresh_session() -> None:
    """`main`'s StoppedRow.test_a_stop_is_a_row_with_the_button_that_opens_a_fresh_session:
    the owner acts on the board, so the verb opens the task and never jumps to the stopped
    pane."""
    seen = board(STOPPED)
    assert rows(seen, "13:00") == [("stopped", f"stopped:{SLUG}")]
    (row,) = waits(seen, "13:00")
    assert (row.verb, row.look, row.since.at, row.since.title) == (
        "Its session stopped: open a fresh one",
        "bad",
        hm("12:44"),
        "since Lem logged the stop",
    )
    assert row.href == "/studio/shop/tasks/gift-note?in=waits"
    assert row.jump is None
    assert "Open a session here or on the task’s header" in row.where
    assert row.acts is not None
    assert [form.label for form in row.acts.forms] == ["Open a session"]
    assert opening.opens(world(seen), seen)
    found = owed.of_task(world(seen, now=hm("13:00")), SLUG)
    told = panel_waiting.waits_for(seen, found)
    assert told is not None
    assert "Open a session here" in (told.where or "")


def test_a_stop_over_a_standing_stop_names_no_fresh_session_and_one_after_a_restart_does() -> (
    None
):
    """`main`'s StoppedRow.test_a_stop_over_a_standing_unread_stop_names_no_fresh_session: the
    unread stop of 11:49, the readable message at 12:45 and a newer stop at 12:55, and no fresh
    session ever opened; a stop after the spent restart keeps its words. The timeline's words
    are `unit.board.views.test_activity_feed.test_a_readable_stop_that_no_fresh_session_
    preceded_says_lem_opened_none`."""
    events = (*UNREAD_STOPPED, wake("12:45"), stop("12:55"))
    (row,) = waits(board(events), "13:00")
    assert row.where == (
        "The task’s session showed no sign of work in the 10 minutes after Lem asked it for "
        "its status, and Lem opened no fresh session by itself, since the task already "
        "stopped once after its last work. Open a session here or on the task’s header: a "
        "fresh agent reads the task’s state and goes on from there, and the old pane stays "
        "open in agterm."
    )
    (after,) = waits(board(STOPPED), "13:00")
    assert "and neither did the fresh session that took its place" in after.where


def test_a_stop_takes_the_place_of_a_wake_nobody_took() -> None:
    """`main`'s StoppedRow.test_a_stop_takes_the_place_of_a_wake_nobody_took."""
    deaf = Session(live=True, since=hm("11:49"), unanswered=True)
    assert rows(board(STOPPED, deaf), "13:00") == [("stopped", f"stopped:{SLUG}")]


def test_a_stopped_session_that_is_gone_is_the_no_session_row_alone() -> None:
    """`main`'s StoppedRow.test_a_stopped_session_that_is_gone_is_the_no_session_row_alone:
    the old pane closed after the stop."""
    seen = board(STOPPED, Session(live=False, since=hm("11:49")))
    assert seen.stop is None
    assert rows(seen, "13:00") == [("session", f"session:{SLUG}")]
    (row,) = waits(seen, "13:00")
    assert row.verb == "No session runs this task"
    assert opening.opens(world(seen), seen)


def test_a_task_out_of_its_phase_has_no_row_whatever_its_stop() -> None:
    """`main`'s StoppedRow.test_a_task_out_of_its_phase_has_no_row_whatever_its_stop: the
    owner parked it after the stop."""
    seen = board(STOPPED, hold=Parked(since=hm("12:50"), words="later"))
    assert (seen.stop, rows(seen, "13:00")) == (None, [])


def test_criterion_2_an_unread_stop_is_the_row_that_says_lem_cannot_read_the_session() -> (
    None
):
    """`main`'s StoppedRow.test_criterion_2_an_unread_stop_is_the_row_stopped_that_says_lem_
    cannot_read_the_session: an entry of the task after the stop removes the row; the readable
    stop keeps its own verb."""
    events = (*LANDING, wake("11:39", unread=True), stop("11:49", unread=True))
    seen = board(events)
    (row,) = waits(seen, "11:50")
    assert (row.id, row.verb, row.since.at, row.look, row.since.title) == (
        f"wait-stopped-{SLUG}",
        "Its session stopped, and Lem cannot read it: open a fresh one",
        hm("11:49"),
        "bad",
        "since Lem logged the stop",
    )
    for words in (
        "Lem cannot read whether the task’s session works",
        "the status message after 45 minutes with no event of the task",
        "no event of the task in the 10 minutes after it",
        "Lem opens no second session by itself",
        "open a session here or on the task’s header",
    ):
        assert words in row.where
    assert "fresh session that took its place" not in row.where
    assert row.acts is not None
    assert [form.label for form in row.acts.forms] == ["Open a session"]
    told = panel_waiting.waits_for(
        seen, owed.of_task(world(seen, now=hm("11:50")), SLUG)
    )
    assert told is not None
    assert "Lem cannot read whether" in (told.where or "")
    assert rows(board((*events, work("11:55"))), "11:56") == []
    assert [one.verb for one in waits(board(STOPPED), "13:00")] == [
        "Its session stopped: open a fresh one"
    ]


def test_lem_waiting_lists_the_stop_as_the_board_has_it_and_whether_lem_can_read_it() -> (
    None
):
    """`main`'s StoppedRow.test_lem_project_waiting_lists_the_stop_as_the_board_has_it and
    StoppedRow.test_lem_project_waiting_says_that_lem_cannot_read_the_stopped_session: the
    group `stopped` of `lem waiting` names the command that opens a fresh session."""
    unread = (*LANDING, wake("11:39", unread=True), stop("11:49", unread=True))
    for events, at, cannot in ((STOPPED, "13:00", False), (unread, "11:50", True)):
        seen = world(board(events), now=hm(at))
        found = owed.rows(seen)
        looks = {SLUG: owed.look_of(seen.tasks[0], frozenset())}
        groups = scope.grouped(scope.Scope(rows=found, slug=None, looks=looks))
        assert [(one.task, one.open, one.unread) for one in groups["stopped"]] == [
            (SLUG, f"lem session open {SLUG} --why stopped", cannot)
        ]
        assert (groups["no_session"], len(found)) == ((), 1)


def test_no_row_before_the_stop_or_after_a_session_opens_or_the_agent_works() -> None:
    """`main`'s StoppedRow.test_no_row_before_the_stop_is_logged_or_after_a_session_opens_or_
    the_agent_works: the record of his click is no work and no open."""
    assert rows(board(STOPPED[:-1]), "12:43") == []
    reopened = board((*STOPPED, opened("12:50", "S3", "stopped")))
    assert rows(reopened, "13:00") == []
    assert rows(board((*STOPPED, work("12:50"))), "13:00") == []
    clicked = OwnerAct(at=hm("12:50"), act="session", via="local")
    assert rows(board((*STOPPED, clicked)), "13:00") == [("stopped", f"stopped:{SLUG}")]


CRITERIA = OwnerHold(
    on="criteria", line="the criteria wait for the owner", since=hm("11:39:31")
)


def at_work(*, working: bool, hold: OwnerHold | BreakerHold = CRITERIA) -> Seen:
    """A held task whose live session's newest turn runs (`working`) or ended."""
    session = Session(live=True, since=hm("09:53:42"), working=working)
    return replace(made((), status="shaping", hold=hold), session=session)


def test_criterion_1_while_the_turn_runs_the_task_is_its_sessions_work_and_no_row() -> (
    None
):
    """`main`'s SessionAtWork.test_criterion_1_while_the_turn_runs_the_task_is_lems_work_and_
    no_row: the kanban, the card's line, the large card, its eyebrow and the line of Tasks say
    that its session works on his answer. The Inbox's part is the server's (`addons-outside`)."""
    from lem.board.views.frame import counted, summary

    seen = world(at_work(working=True), now=hm("11:43"))
    found = owed.seen(seen, SLUG)
    assert owed.rows(seen) == ()
    where = standing.standing(found, ())
    assert (where.column, where.label, where.who) == (
        "build",
        "Works on your answer",
        "The task's session",
    )
    line = telling.line(found.record, where, tasks.TITLES[where.column])
    assert line == (
        "Works on your answer: it waits for you again when the session's turn ends"
    )
    card = now.now(seen, found, (), where)
    assert (card.head, card.who, card.where) == (
        "Its session works on your answer",
        "The task's session acts",
        None,
    )
    assert summary.tasks_line(counted.counted(seen)) == (
        "1 whose session works on your answer"
    )


def test_criterion_2_when_the_turn_ends_the_row_is_back_since_its_hold() -> None:
    """`main`'s SessionAtWork.test_criterion_2_when_the_turn_ends_on_the_same_model_the_row_is_
    back_since_11_39, changed: each page reads the world afresh, so the row comes back with
    the turn's end, since the hold's own moment (11:39:31)."""
    seen = world(at_work(working=False), now=hm("11:43:33"))
    (row,) = owed.rows(seen)
    assert (row.kind, row.key, row.since) == (
        "criteria",
        f"held:{SLUG}",
        hm("11:39:31"),
    )
    where = standing.standing(owed.seen(seen, SLUG), (row,))
    assert (where.column, where.since) == ("you", hm("11:39:31"))


def test_criterion_3_with_no_turn_lem_can_read_the_task_waits_as_without_one() -> None:
    """`main`'s SessionAtWork.test_criterion_3_with_no_turn_lem_can_read_the_task_waits_as_
    today: the terminal not asked, no session, a session whose turn does not read, no agent in
    its pane, not in agterm."""
    cases = {
        "the terminal not asked": None,
        "no session of the task": Session(live=False, since=hm("09:53:42")),
        "no transcript Lem reads": Session(live=True, since=hm("09:53:42")),
        "no agent in its pane": Session(live=False, since=hm("09:53:42"), working=True),
    }
    for why, session in cases.items():
        seen = world(replace(at_work(working=True), session=session), now=hm("11:43"))
        assert (
            "criteria",
            f"held:{SLUG}",
        ) in [(row.kind, row.key) for row in owed.rows(seen)], why


def test_a_breakers_held_task_follows_the_turn_and_a_blocked_task_keeps_its_row() -> (
    None
):
    """`main`'s SessionAtWork.test_a_breakers_held_task_follows_the_turn_and_a_blocked_task_
    keeps_its_row."""
    from lem.records.holds import Blocked

    breaker = BreakerHold(number=1, since=hm("11:00"))
    runs = world(at_work(working=True, hold=breaker), now=hm("11:43"))
    assert owed.rows(runs) == ()
    assert heads.now_head(owed.seen(runs, SLUG)) == "Its session works on your answer"
    ended = world(at_work(working=False, hold=breaker), now=hm("11:43"))
    assert [row.key for row in owed.rows(ended)] == [f"breaker:{SLUG}:1"]
    block = Blocked(why="the fixture needs a login", fix="x", since=hm("11:00"))
    session = Session(live=True, since=hm("09:53:42"), working=True)
    blocked = replace(made((), status="building", hold=block), session=session)
    assert [row.key for row in owed.rows(world(blocked, now=hm("11:43")))] == [
        f"blocked:{SLUG}"
    ]


def test_a_demo_takes_its_session_from_lems_acts_alone() -> None:
    """`main`'s Sessions.test_a_demo_reads_a_session_from_the_log_alone: on a board of example
    tasks the newest session Lem opened lives until Lem closed it, and a task whose session
    Lem closed lacks one."""
    from lem.app.sessions.acts import Close

    opens = (opened("09:00", "S1", "new"),)
    building = made((), status="building", opened=hm("08:00"), since=hm("08:00"))
    alive = sessions.from_acts(building.record, opens)
    assert alive.live
    shown = replace(building, acts=opens, session=alive)
    assert rows(shown, "13:00") == []
    closes = (*opens, Close(at=hm("09:30"), session="S1", why="owner"))
    asleep = sessions.from_acts(building.record, closes)
    gone_now = replace(building, acts=closes, session=asleep)
    (row,) = waits(gone_now, "13:00")
    assert (row.kind, row.verb) == ("session", "No session runs this task")
