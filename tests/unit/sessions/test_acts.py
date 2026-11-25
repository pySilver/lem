"""Wake, wait, the first line, the close of a job's session, a close a wake keeps open, the
list's agent and unanswered wake, the workspace a new session goes into, and the guard's steps,
each on the fake terminal and harness."""

import dataclasses
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import msgspec
import pytest

from fakes.records import MOMENT
from lem.app.sessions import (
    acts,
    closing,
    closing_job,
    first_line,
    guard_look,
    guard_steps,
    guard_stop,
    handing,
    listing,
    log,
    opening,
    signs,
    waits,
    waking,
)
from lem.cli.session import open as open_leaf
from lem.cli.session import wait, wake
from lem.kernel.errors import Refusal
from lem.ports.faults import Unanswered
from lem.ports.harness import Signs, Transcript
from lem.ports.terminal import Pane
from lem.records.holds import Blocked, OwnerHold, Parked, ReleaseHold
from lem.records.journal.task import StateNoted
from lem.records.sessions import SessionLine
from lem.records.task import Shape
from lem.store import sessions, tasks
from unit.sessions.harness import SigningHarness
from unit.sessions.terminal import CALLER, LookingTerminal, with_caller
from unit.sessions.world import SLUG, here_of, made

if TYPE_CHECKING:
    from pathlib import Path

    from fakes.harness import FakeHarness
    from lem.app.sessions.here import Here

LATER = MOMENT + timedelta(minutes=5)
HOUR = MOMENT + timedelta(hours=1)


def never(_seconds: float) -> None:
    """A pause the test never reaches."""
    raise AssertionError("the wait paused")


def test_a_wake_goes_to_the_live_session_with_its_head_on_record(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here, status="building", lead="builder")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    woken = waking.wake(here, SLUG, "conflict", "a" * 40, LATER)
    assert (woken.woke, woken.opened, woken.session) == (True, False, "session-1")
    assert terminal.told == [("session-1", f"lem: {SLUG} conflict")]
    wakes = [act for act in log.read(here.folder(SLUG)) if isinstance(act, acts.Wake)]
    assert [(one.why, one.head) for one in wakes] == [("conflict", "a" * 40)]


def test_a_wake_with_no_live_session_opens_one_but_for_the_inbox_and_a_parked_task(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here, status="building", lead="builder")
    inbox = waking.wake(here, SLUG, "inbox", None, MOMENT)
    assert (inbox.woke, inbox.opened, inbox.session) == (False, False, None)
    merged = waking.wake(here, SLUG, "merged", "b" * 40, MOMENT)
    assert (merged.woke, merged.opened, merged.session) == (False, True, "session-1")
    made(here, "parked-task", status="building", hold=Parked(since=MOMENT))
    parked = waking.wake(here, "parked-task", "owner", None, MOMENT)
    assert (parked.opened, parked.session) == (False, None)
    assert len(terminal.openings) == 1


def test_a_close_that_waits_ends_with_no_close_when_the_session_is_woken(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here)
    opening.open_session(here, SLUG, "new", None, MOMENT)
    terminal.select("session-1")

    def woken(_every: float) -> None:
        log.append(
            here.folder(SLUG), acts.Wake(at=LATER, session="session-1", why="queue")
        )

    asked = closing.Closing(slug=SLUG, why="handoff", when_unselected=True, every=1.0)
    got = closing.close_session(here, asked, woken, lambda: LATER)
    assert (got.closed, got.woken) == (False, True)
    assert terminal.closed == []
    assert not [
        act for act in log.read(here.folder(SLUG)) if isinstance(act, acts.Close)
    ]


def test_a_jobs_session_closes_once_he_left_it_and_a_tasks_or_his_own_never(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    terminal.panes["S-JOB"] = Pane(
        id="S-JOB", name="night", workspace="W-1", selected=True
    )
    terminal.grounds["S-JOB"] = ("/usr/local/bin/claude", "/lem night 2")
    terminal.grounds[CALLER.id] = ("/usr/local/bin/claude",)
    here = here_of(tmp_path, terminal)
    made(here)
    opening.open_session(here, SLUG, "new", None, MOMENT)
    with pytest.raises(Refusal) as task:
        closing_job.close_job(here, "session-1", 0.0, never)
    assert task.value.code == "task-session"
    with pytest.raises(Refusal) as his:
        closing_job.close_job(here, None, 0.0, never)
    assert his.value.code == "not-a-job"
    got = closing_job.close_job(
        here, "S-JOB", 2.0, lambda _: terminal.select(CALLER.id)
    )
    assert (got.closed, got.job) == (True, "/lem night 2")
    assert terminal.closed == ["S-JOB"]
    assert not [
        act for act in log.read(here.folder(SLUG)) if isinstance(act, acts.Close)
    ]


def test_the_first_line_comes_with_the_read_and_never_for_a_nights_task(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    shape = Shape(type="fix", why="the login drops", track="small")
    made(here, status="shaping", ask='fix "the" login', shape=shape)
    got = first_line.first_line(here, (SLUG, 0.0, 600.0), lambda: MOMENT, never)
    assert got.say == f"{SLUG} · fix: \"fix 'the' login\". Fast track: the login drops"
    made(here, "night-task", shape=shape, night=MOMENT.date())
    night = first_line.first_line(
        here, ("night-task", 0.0, 600.0), lambda: MOMENT, never
    )
    assert (night.say, night.gone) == (None, False)
    assert "night" in (night.why or "")
    hold = OwnerHold(on="order", line="which task?", since=MOMENT)
    made(here, "order-task", status="shaping", hold=hold)
    order = first_line.first_line(
        here, ("order-task", 0.0, 600.0), lambda: MOMENT, never
    )
    assert "order" in (order.why or "")


def test_the_first_line_wait_ends_at_its_bound_and_when_the_session_is_gone(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here, status="shaping")
    moments = iter((MOMENT, MOMENT, LATER))
    got = first_line.first_line(
        here, (SLUG, 1.0, 60.0), lambda: next(moments), lambda _: None
    )
    assert (got.say, got.gone) == (None, False)
    assert "1 minutes" in (got.why or "")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    terminal.close("session-1", when_unselected=False)
    gone = first_line.first_line(here, (SLUG, 1.0, 60.0), lambda: LATER, never)
    assert gone.gone is True


def test_wait_ends_at_a_status_a_new_entry_and_a_gone_session(tmp_path: Path) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here, status="building", lead="builder")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    asked = waits.Asked(slug=SLUG, until=("building",), every=0.0)
    assert waits.wait_for(here, asked, lambda: LATER, never).status == "building"
    by_kind = waits.Asked(slug=SLUG, event="wake", every=0.0)

    def woke(_every: float) -> None:
        log.append(
            here.folder(SLUG), acts.Wake(at=LATER, session="session-1", why="owner")
        )

    found = waits.wait_for(here, by_kind, lambda: LATER, woke)
    assert found.entry is not None
    assert b'"why":"owner"' in bytes(found.entry)
    terminal.end_agent("session-1")
    until = waits.Asked(slug=SLUG, until=("ready",), every=0.0)
    gone = waits.wait_for(here, until, lambda: HOUR, never)
    assert (gone.gone, gone.session) == (True, "session-1")
    assert "--why dead" in (gone.say or "")


def test_wait_ends_when_a_companion_is_gone_or_a_file_stays_quiet(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    made(here, status="building", lead="builder")
    companion = waits.Asked(slug=SLUG, until=("ready",), companion="S-PAIR", every=0.0)
    got = waits.wait_for(here, companion, lambda: LATER, never)
    assert (got.gone, got.companion) == (True, "S-PAIR")
    quiet = waits.Asked(
        slug=SLUG, until=("ready",), quiet=str(tmp_path / "x.md"), every=0.0
    )
    moments = iter((MOMENT, MOMENT, HOUR))
    found = waits.wait_for(here, quiet, lambda: next(moments), lambda _: None)
    assert found.quiet == str(tmp_path / "x.md")


def signed(here_harness: FakeHarness, path: str, signs: Signs) -> None:
    """A transcript of the task's session with its signs."""
    one = Transcript(path=path, claude="c1")
    here_harness.by_task[SLUG] = (one,)
    here_harness.signs_of[path] = signs


def test_the_list_says_whether_an_agent_runs_and_how_a_wake_went_unanswered(
    tmp_path: Path,
) -> None:
    terminal, harness = with_caller(), SigningHarness()
    here = here_of(tmp_path, terminal, harness)
    made(here, status="building", lead="builder")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    line = SessionLine(
        at=MOMENT,
        source="startup",
        claude="c1",
        transcript="t",
        pane="SESSION-1",
        task=SLUG,
    )
    sessions.append(here.folder(SLUG), line)
    signed(harness, "t", Signs(sign=MOMENT, turn="ended"))
    waking.wake(here, SLUG, "merged", None, LATER)
    entry = listing.list_sessions(here, HOUR)[0]
    assert (entry.agent, entry.signs, entry.turn) == (True, True, "ended")
    assert entry.unheard is not None
    assert (entry.unheard.why, entry.unheard.line) == ("merged", "waits")
    terminal.taken.add(f"lem: {SLUG} merged")
    taken = listing.list_sessions(here, HOUR)[0].unheard
    assert taken is not None
    assert taken.line == "taken"
    terminal.end_agent("session-1")
    ended = listing.list_sessions(here, HOUR)[0]
    assert (ended.live, ended.agent, ended.signs, ended.sign) == (
        True,
        False,
        False,
        None,
    )


def test_a_new_session_goes_to_the_callers_workspace_before_the_after_tasks(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    terminal.panes["S-HIS"] = Pane(id="S-HIS", name="notes", workspace="W-2")
    here = here_of(tmp_path, terminal)
    made(here, "first-task", status="landed")
    first = acts.Open(
        at=MOMENT,
        session="S-X",
        name="first-task",
        phase="build",
        why="new",
        workspace="W-2",
    )
    log.append(here.folder("first-task"), first)
    made(here, after="first-task", lead="builder")
    assert opening.open_session(here, SLUG, "queue", None, LATER).workspace == "W-1"
    made(here, "third", lead="builder")
    away = dataclasses.replace(here, caller=None)
    assert opening.open_session(away, "third", "queue", None, MOMENT).workspace == "W-1"
    made(here, "fourth", lead="builder")
    lonely = here_of(tmp_path / "other", with_caller())
    made(lonely, "fourth", lead="builder")
    with pytest.raises(Refusal) as refused:
        opening.open_session(
            dataclasses.replace(lonely, caller=None), "fourth", "new", None, MOMENT
        )
    assert refused.value.code == "no-workspace"


def test_the_guard_sends_its_status_message_only_when_it_is_due(tmp_path: Path) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here, status="building", lead="builder")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    early = guard_steps.stepped(here, SLUG, "status", "session-1", LATER)
    assert (early.acted, early.why) == (False, "working")
    other = guard_steps.stepped(here, SLUG, "status", "S-OTHER", HOUR)
    assert (other.acted, other.why) == (False, "gone")
    sent = guard_steps.stepped(here, SLUG, "status", "session-1", HOUR)
    assert sent.acted is True
    assert terminal.told == [("session-1", f"lem: {SLUG} status")]
    wakes = [act for act in log.read(here.folder(SLUG)) if isinstance(act, acts.Wake)]
    assert [(one.why, one.unread) for one in wakes] == [("status", True)]


def test_the_guard_stops_an_unreadable_session_and_the_owners_open_restarts_it(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here, status="building", lead="builder")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    guard_steps.stepped(here, SLUG, "status", "session-1", HOUR)
    later = HOUR + timedelta(minutes=10)
    stopped = guard_steps.stepped(here, SLUG, "stopped", "session-1", later)
    assert stopped.acted is True
    duty = guard_steps.stepped(here, SLUG, "restart", "session-1", later)
    assert (duty.acted, duty.why) == (False, "unread")
    owner = guard_steps.stepped(here, SLUG, "restart", None, later)
    assert (owner.acted, owner.opened) == (True, "session-2")
    assert ("session-1", f"{SLUG} · replaced") in terminal.renamed
    assert ("session-1", f"lem: {SLUG} replaced") in terminal.told


def test_the_guard_watches_no_task_with_a_hold(tmp_path: Path) -> None:
    here = here_of(tmp_path)
    hold = OwnerHold(on="criteria", line="the criteria wait", since=MOMENT)
    made(here, status="building", lead="builder", hold=hold)
    opening.open_session(here, SLUG, "new", None, MOMENT)
    got = guard_steps.stepped(here, SLUG, "status", "session-1", HOUR)
    assert (got.acted, got.why) == (False, "status")
    assert tasks.read(here.where.state, SLUG).task.hold == hold


def test_a_sessions_signs_are_its_own_transcripts_newest_and_any_shell(
    tmp_path: Path,
) -> None:
    harness = SigningHarness()
    here = here_of(tmp_path, with_caller(), harness)
    made(here, status="building", lead="builder")
    assert signs.read_signs(here, SLUG, "SESSION-1") == signs.Read()
    for claude, pane in (
        ("c1", "session-1"),
        ("c2", "SESSION-1"),
        ("c3", "S-OLD"),
        ("c4", None),
    ):
        line = SessionLine(
            at=MOMENT,
            source="startup",
            claude=claude,
            transcript=claude,
            pane=pane,
            task=SLUG,
        )
        sessions.append(here.folder(SLUG), line)
    harness.by_task[SLUG] = tuple(
        Transcript(path=one, claude=one) for one in ("c1", "c2", "c3", "c4")
    )
    harness.signs_of["c1"] = Signs(sign=MOMENT, turn="ended", shell=True)
    harness.signs_of["c2"] = Signs(sign=LATER, turn="runs")
    harness.signs_of["c3"] = Signs(sign=HOUR, turn="ended")
    harness.signs_of["c4"] = Signs(sign=HOUR, turn="ended")
    read = signs.read_signs(here, SLUG, "Session-1")
    assert read == signs.Read(sign=LATER, shell=True, signs=True, turn="runs")


def test_wait_ends_at_a_hold_its_until_names_as_mains_states_did(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    block = Blocked(
        why="the planner's seat failed",
        fix="lem seat again",
        seat="planner",
        since=MOMENT,
    )
    made(here, status="building", lead="builder", hold=block)
    asked = waits.Asked(slug=SLUG, until=("planned", "held", "blocked"), every=0.0)
    got = waits.wait_for(here, asked, lambda: LATER, never)
    assert (got.status, got.hold) == ("building", "blocked")
    assert wait.statuses("planned,held,blocked") == ("planned", "held", "blocked")
    with pytest.raises(Refusal) as refused:
        wait.statuses("planned,waiting")
    assert refused.value.code == "until"


def test_a_companion_whose_agent_ended_is_gone_once_the_wait_has_started(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    terminal.panes["S-PAIR"] = Pane(id="S-PAIR", name="pair", workspace="W-1")
    terminal.grounds["S-PAIR"] = ()
    here = here_of(tmp_path, terminal)
    made(here, status="building", lead="builder")
    asked = waits.Asked(slug=SLUG, until=("ready",), companion="S-PAIR", every=0.0)
    moments = iter((MOMENT, MOMENT, MOMENT + timedelta(seconds=61)))
    looks: list[float] = []
    got = waits.wait_for(here, asked, lambda: next(moments), looks.append)
    assert (got.gone, got.companion, looks) == (True, "S-PAIR", [0.0])


def test_a_task_two_releases_back_gets_no_wake_but_its_merged_one(
    tmp_path: Path,
) -> None:
    terminal = with_caller()
    here = here_of(tmp_path, terminal)
    made(here, status="open", lead="builder")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    stop = ReleaseHold(
        began="0.1.0", running="1.0.0", say="began two releases back", since=LATER
    )
    current = tasks.read(here.where.state, SLUG)
    tasks.update(
        here.where.state,
        SLUG,
        lambda one: msgspec.structs.replace(
            one, task=msgspec.structs.replace(one.task, hold=stop)
        ),
        current.revision,
    )
    with pytest.raises(Refusal) as refused:
        waking.wake(here, SLUG, "conflict", "c" * 40, LATER)
    assert refused.value.code == "release"
    assert terminal.told == []
    with pytest.raises(Refusal):
        handing.hand_on(here, SLUG, same=True, now=LATER)
    merged = waking.wake(here, SLUG, "merged", None, LATER)
    assert merged.woke is True


def test_session_goes_only_with_the_guards_own_steps() -> None:
    with pytest.raises(Refusal) as woken:
        wake.run(wake.Call(slug=SLUG, why="conflict", session="S-OLD"))
    with pytest.raises(Refusal) as opened:
        open_leaf.run(open_leaf.Call(slug=SLUG, why="new", session="S-OLD"))
    assert (woken.value.code, opened.value.code) == ("session-option", "session-option")


def stopped_task(here: Here) -> datetime:
    """A building task whose unreadable session got its status message an hour ago and no
    answer: the moment its stop is due."""
    made(here, status="building", lead="builder")
    opening.open_session(here, SLUG, "new", None, MOMENT)
    guard_steps.stepped(here, SLUG, "status", "session-1", HOUR)
    return HOUR + timedelta(minutes=10)


def test_work_in_the_moment_of_the_stop_leaves_nothing_waiting_and_says_so(
    tmp_path: Path,
) -> None:
    here = here_of(tmp_path)
    later = stopped_task(here)
    looked = guard_look.looked(here, SLUG, later)
    current = tasks.read(here.where.state, SLUG)
    work = StateNoted(at=later, status="building", line="the build goes on")
    tasks.update(
        here.where.state,
        SLUG,
        lambda one: msgspec.structs.replace(one, journal=(*one.journal, work)),
        current.revision,
    )
    got = guard_stop.stopped(here, SLUG, looked, later)
    assert (got.acted, got.stands, got.read) == (True, False, False)
    assert "nothing waits for the owner" in got.say
    stood = guard_steps.stepped(here, SLUG, "stopped", "session-1", later)
    assert stood.acted is False


class GoneTerminal(LookingTerminal):
    """A terminal whose old session is gone the moment Lem names it replaced."""

    def rename(self, session: str, name: str) -> None:
        raise Unanswered("agtermctl", f"no session {session}")


def test_a_restart_whose_old_pane_is_gone_says_so_and_keeps_its_fresh_session(
    tmp_path: Path,
) -> None:
    terminal = GoneTerminal(panes={CALLER.id: CALLER})
    here = here_of(tmp_path, terminal)
    later = stopped_task(here)
    guard_steps.stepped(here, SLUG, "stopped", "session-1", later)
    got = guard_steps.stepped(here, SLUG, "restart", None, later)
    assert (got.acted, got.opened, got.told) == (True, "session-2", False)
    assert "no session session-1" in (got.problem or "")
    opens = [
        act.session for act in log.read(here.folder(SLUG)) if isinstance(act, acts.Open)
    ]
    assert opens == ["session-1", "session-2"]


def test_the_turn_is_the_one_of_the_transcript_whose_main_thread_wrote_the_newest_turn(
    tmp_path: Path,
) -> None:
    harness = SigningHarness()
    here = here_of(tmp_path, with_caller(), harness)
    made(here, status="building", lead="builder")
    for claude in ("c1", "c2"):
        line = SessionLine(
            at=MOMENT,
            source="startup",
            claude=claude,
            transcript=claude,
            pane="S-1",
            task=SLUG,
        )
        sessions.append(here.folder(SLUG), line)
    harness.by_task[SLUG] = tuple(
        Transcript(path=one, claude=one) for one in ("c1", "c2")
    )
    # c1's main thread ended first; a subagent of it wrote the newest sign of all
    harness.signs_of["c1"] = Signs(sign=HOUR, turn="ended")
    harness.mains["c1"] = MOMENT
    harness.signs_of["c2"] = Signs(sign=LATER, turn="runs")
    read = signs.read_signs(here, SLUG, "S-1")
    assert (read.sign, read.turn) == (HOUR, "runs")
