"""The pure rules of a task's session: whether an agent runs in a pane, a job's line, the phase a
state entry gave, a seat's form, and the guard of a stopped session."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from fakes.records import MOMENT, record
from lem.app.sessions import agents, seating
from lem.app.sessions.guard_due import due
from lem.app.sessions.guard_rule import Event, Facts, Timeline
from lem.app.sessions.phase import phase_noted
from lem.kernel.errors import Refusal
from lem.records.task import Shape

if TYPE_CHECKING:
    from lem.app.sessions.seating import Role

SHELL = "/bin/zsh"
LAUNCH = "LEM_TASK=gift-note CLAUDE_CODE_AUTO_COMPACT_WINDOW=600000 claude 'Read x.'"


@pytest.mark.parametrize(
    ("ground", "runs"),
    [
        ((SHELL, "-l", "-c", LAUNCH), True),
        (("/usr/local/bin/claude", "--resume"), True),
        (("node", "/opt/claude/bin/codex"), True),
        ((SHELL, "-lc", "make test"), False),
        ((SHELL,), False),
        ((), False),
        (None, None),
        ((SHELL, "-c", "claude 'unclosed"), True),
    ],
)
def test_an_agent_runs_in_a_pane_by_its_programs_words(
    ground: tuple[str, ...] | None, runs: object
) -> None:
    assert agents.agent_runs(ground) is runs


@pytest.mark.parametrize(
    ("ground", "line"),
    [
        (("/usr/local/bin/claude", "--model", "opus", "/lem night"), "/lem night"),
        (("claude", "/lem   night  2"), "/lem night 2"),
        (("codex", "/lem retro"), "/lem retro"),
        (("claude",), None),
        ((SHELL, "-c", "claude '/lem retro'"), None),
        (("vim", "/lem retro"), None),
        (None, None),
    ],
)
def test_a_jobs_line_is_the_last_word_of_an_agents_command(
    ground: tuple[str, ...] | None, line: str | None
) -> None:
    assert agents.job_line(ground) == line


def test_a_session_whose_agent_ended_carries_its_task_only_while_it_starts() -> None:
    later = MOMENT + timedelta(seconds=agents.STARTING)
    assert agents.live((), listed=True, opened=MOMENT, now=MOMENT)
    assert not agents.live((), listed=True, opened=MOMENT, now=later)
    assert agents.live(None, listed=True, opened=MOMENT, now=later)
    assert not agents.live(("claude",), listed=False, opened=MOMENT, now=MOMENT)


@pytest.mark.parametrize(
    ("fields", "status", "hold", "phase"),
    [
        ({}, "building", None, "build"),
        ({}, "shaping", "owner", "shape"),
        ({}, "building", "breaker", "build"),
        ({}, "queued", None, "shape"),
        ({"lead": "builder"}, "queued", None, "build"),
        (
            {"shape": Shape(type="fix", why="w", track="small")},
            "building",
            None,
            "fast",
        ),
        ({}, "landed", None, "land"),
        ({}, "building", "parked", None),
        ({}, "answered", None, None),
    ],
)
def test_a_state_entry_gives_the_phase_of_its_status_and_hold(
    fields: dict[str, object], status: str, hold: str | None, phase: str | None
) -> None:
    task = record("gift-note", **fields).task
    assert phase_noted(task, status, hold) == phase


@pytest.mark.parametrize(
    ("role", "text", "parts"),
    [
        ("session", "claude", ("claude", None, None)),
        ("session", "claude:high", ("claude", None, "high")),
        ("merger", "codex/gpt-6.2-sol", ("codex", "gpt-6.2-sol", None)),
        ("reviewer", "codex/gpt-6.2-sol:high", ("codex", "gpt-6.2-sol", "high")),
    ],
)
def test_a_seat_is_agent_model_and_effort(
    role: Role, text: str, parts: tuple[str | None, ...]
) -> None:
    shown = seating.parsed(text, role, "w", "s")
    assert (shown.agent, shown.model, shown.effort, shown.seat) == (*parts, text)


@pytest.mark.parametrize(
    ("role", "text", "code"),
    [
        ("reviewer", "claude:high", "seat"),
        ("planner", "codex/gpt:high", "seat-agent"),
        ("session", "claude/", "seat"),
        ("session", "claude:", "seat"),
        ("session", "claude opus", "seat"),
        ("session", "claude/a:b:c", "seat"),
        ("session", 3, "seat"),
    ],
)
def test_a_seat_not_in_its_form_or_of_an_agent_that_may_not_sit_is_refused(
    role: Role, text: object, code: str
) -> None:
    with pytest.raises(Refusal) as refused:
        seating.parsed(text, role, "w", "s")
    assert refused.value.code == code


def at(minutes: int) -> datetime:
    """A moment `minutes` after the task's open."""
    return MOMENT + timedelta(minutes=minutes)


def line(*events: Event) -> Timeline:
    """A timeline that starts with the task's open."""
    return Timeline(events=(Event(kind="open", at=MOMENT, why="new"), *events))


READ = Facts(guarded=True, alive=True, read=True, sign=MOMENT)
UNREAD = Facts(guarded=True, alive=True, read=False)


def status_wake(minutes: int, *, unread: bool = False) -> Event:
    return Event(kind="wake", at=at(minutes), why="status", unread=unread)


def test_a_quiet_session_gets_its_status_message_after_45_minutes() -> None:
    assert due(line(), READ, at(44)) is None
    found = due(line(), READ, at(45))
    assert found is not None
    assert (found.step, found.since) == ("status", MOMENT)


def test_no_step_for_a_task_the_guard_does_not_watch_or_a_shell_that_runs() -> None:
    for facts in (
        Facts(guarded=False, alive=True, read=True),
        Facts(guarded=True, alive=False, read=True),
        Facts(guarded=True, alive=True, shell=True, read=True),
    ):
        assert due(line(), facts, at(90)) is None


def test_after_the_message_a_readable_session_is_restarted_once_then_stopped() -> None:
    asked = line(status_wake(45))
    assert due(asked, READ, at(54)) is None
    restart = due(asked, READ, at(55))
    assert restart is not None
    assert restart.step == "restart"
    restarted = line(
        status_wake(45),
        Event(kind="open", at=at(55), why="stopped"),
        status_wake(100),
    )
    stop = due(
        restarted, Facts(guarded=True, alive=True, read=True, sign=at(55)), at(110)
    )
    assert stop is not None
    assert stop.step == "stopped"


def test_an_unreadable_session_is_stopped_at_once_and_its_stop_logged_once() -> None:
    asked = line(status_wake(45, unread=True))
    found = due(asked, UNREAD, at(55))
    assert found is not None
    assert found.step == "stopped"
    stopped = line(
        status_wake(45, unread=True),
        Event(kind="stopped", at=at(55), unread=True),
    )
    assert stopped.stop_stands() == 2
    assert due(stopped, UNREAD, at(80)) is None


def test_work_after_the_message_ends_the_stop_and_the_clock_starts_again() -> None:
    worked = line(
        status_wake(45),
        Event(kind="stopped", at=at(55)),
        Event(kind="work", at=at(56)),
    )
    assert worked.stop_stands() is None
    assert due(worked, READ, at(100)) is None
    found = due(worked, READ, at(101))
    assert found is not None
    assert (found.step, found.since) == ("status", at(56))


def test_a_turn_read_after_an_unread_message_is_put_on_record() -> None:
    asked = line(status_wake(45, unread=True))
    facts = Facts(guarded=True, alive=True, read=True, sign=at(47))
    found = due(asked, facts, at(48))
    assert found is not None
    assert (found.step, found.since) == ("worked", at(47))
