"""Open a session from the board: once for a task none of whose sessions carries it, never over a
session that carries it, and beside the session the guard stopped while the stop stands."""

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

from fakes.records import MOMENT
from lem.app.sessions import acts, guard_steps, here, log
from lem.board.acts import restarting
from lem.kernel import clock
from lem.ports.faults import Unanswered
from lem.records.journal.task import OwnerAct
from lem.store import places
from unit.board.acts.acts import SLUG, made, note_of, opened, read

if TYPE_CHECKING:
    from unit.board.acts.conftest import Board

SESSION = f"/tasks/{SLUG}/session"
HOUR = MOMENT + timedelta(hours=1)
LATER = HOUR + timedelta(minutes=10)
NOW = MOMENT + timedelta(hours=2)


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """The board's acts run two hours after the session opened."""
    monkeypatch.setattr(clock, "now", lambda: NOW)


def opens(board: Board) -> list[str]:
    """Why each session Lem opened for the task opened."""
    found = log.read(places.task_folder(board.state, SLUG))
    return [act.why for act in found if isinstance(act, acts.Open)]


def test_open_a_session_runs_once_for_a_task_with_none_and_never_over_one_that_runs(
    board: Board,
) -> None:
    made(board, "earlier-task", status="building", lead="builder")
    opened(board, "earlier-task", MOMENT)
    made(board, status="building", lead="builder")
    first = note_of(board.post(SESSION, {"in": "waits"}))
    assert first.state == "done"
    assert first.said.startswith("A session of the task opened in agterm")
    assert opens(board) == ["owner"]
    again = note_of(board.post(SESSION, {}))
    assert again.state == "refused"
    assert f"No session of {SLUG} was opened" in again.said
    assert opens(board) == ["owner"]
    entries = [one.act for one in read(board).journal if isinstance(one, OwnerAct)]
    assert entries == ["session"]


def test_a_task_whose_session_ended_gets_a_fresh_one_as_dead(board: Board) -> None:
    made(board, status="building", lead="builder")
    session = opened(board, at=MOMENT)
    board.terminal.end_agent(session)
    note = note_of(board.post(SESSION, {}))
    assert note.state == "done", note.said
    assert opens(board) == ["owner", "dead"]


def stopped(board: Board) -> str:
    """A task whose session the guard stopped after its status message."""
    made(board, status="building", lead="builder")
    session = opened(board, at=MOMENT)
    bound = here.bound(board.checkout)
    guard_steps.stepped(bound, SLUG, "status", session, HOUR)
    guard_steps.stepped(bound, SLUG, "stopped", session, LATER)
    return session


def test_the_button_opens_beside_the_stopped_session(board: Board) -> None:
    session = stopped(board)
    note = note_of(board.post(SESSION, {}))
    assert note.state == "done"
    assert "beside the one that stopped" in note.said
    assert (session, f"{SLUG} · replaced") in board.terminal.renamed
    assert opens(board) == ["owner", "stopped"]


def test_the_replacement_opens_even_when_agterm_cannot_rename_the_old_session(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    stopped(board)

    def rename(session: str, name: str) -> None:
        raise Unanswered("agtermctl", "the old session disappeared")

    monkeypatch.setattr(board.terminal, "rename", rename)
    note = note_of(board.post(SESSION, {}))
    assert note.state == "done"
    assert "opened in agterm" in note.said
    assert "agtermctl: the old session disappeared" in note.said
    assert "agterm now names" not in note.said
    assert opens(board) == ["owner", "stopped"]


def test_a_stopped_session_that_is_gone_takes_the_open_of_a_task_with_none(
    board: Board,
) -> None:
    session = stopped(board)
    board.terminal.end_agent(session)
    note = note_of(board.post(SESSION, {}))
    assert note.state == "done"
    assert opens(board) == ["owner", "dead"]


def test_an_open_that_finds_work_says_so_and_opens_nothing(
    board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    stopped(board)
    working = guard_steps.refused(SLUG, "session-1", "working")
    monkeypatch.setattr(guard_steps, "stepped", lambda *given: working)
    note = note_of(board.post(SESSION, {}))
    assert note.state == "refused"
    assert note.said.startswith(restarting.NOT_OPENED["working"])
    assert opens(board) == ["owner"]


def test_a_task_that_gets_no_session_is_refused_with_why(board: Board) -> None:
    made(board, status="landed")
    note = note_of(board.post(SESSION, {}))
    assert note.state == "refused"
    assert "an ended task gets no session" in note.said
