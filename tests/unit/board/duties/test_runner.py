"""The board server's runner under a failure: a duty's fault is its board's problem with its
traceback in the server's log once, and the next tick tries it again; a refusal has no
traceback; a workspace whose ports do not bind costs no other workspace; and a loop of the
server's life that fails runs again while the board keeps serving."""

import logging
import time
from datetime import timedelta
from typing import TYPE_CHECKING

import anyio

from fakes.records import MOMENT
from lem.board.duties import context, guard, prune, runner, seams
from lem.board.duties.memory import MEMORY, Kept
from lem.kernel.errors import Fault, Refusal
from unit.board.duties.world import duty_of
from unit.board.service.given import made
from unit.sessions.world import here_of

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from lem.app.sessions.here import Here
    from lem.store.places import Workspace

GUARD = "lem.board.duties.guard"
PRUNE = "lem.board.duties.prune"
FAULT = "Lem's files are neither in /gone/lem/data, as in an installed Lem"
TRACED = "the traceback of the fault of"


def traces(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    """The records of the server's log that carry a duty's traceback."""
    return [one for one in caplog.records if TRACED in one.getMessage()]


def test_a_duty_fault_is_its_boards_problem_and_the_next_tick_runs_it_again(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[int] = []

    def tick(_duty: object) -> None:
        calls.append(len(calls))
        if len(calls) <= 2:
            raise Fault(FAULT)

    monkeypatch.setattr(runner, "DUTIES", (GUARD,))
    monkeypatch.setattr(guard, "tick", tick)
    here = here_of(tmp_path)
    kept = Kept()
    caplog.set_level(logging.ERROR)

    runner.ticked(duty_of(here, MOMENT, kept))
    runner.ticked(duty_of(here, MOMENT + timedelta(seconds=20), kept))

    assert kept.problems == {"guard": f"the board's duty guard failed: Fault: {FAULT}"}
    [traced] = traces(caplog)
    assert isinstance(traced.exc_info, tuple)
    assert isinstance(traced.exc_info[1], Fault)
    assert "shop" in traced.getMessage()
    err = capsys.readouterr().err
    assert (
        err.count(f"lem serve: shop: the board's duty guard failed: Fault: {FAULT}")
        == 2
    )

    runner.ticked(duty_of(here, MOMENT + timedelta(seconds=40), kept))

    assert calls == [0, 1, 2]
    assert kept.problems == {}
    assert kept.faults == {}


def test_a_duty_refusal_is_on_the_board_with_no_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def tick(_duty: object) -> None:
        raise Refusal("no-session", "agterm does not answer", "the owner starts agterm")

    monkeypatch.setattr(runner, "DUTIES", (GUARD,))
    monkeypatch.setattr(guard, "tick", tick)
    kept = Kept()
    caplog.set_level(logging.ERROR)

    runner.ticked(duty_of(here_of(tmp_path), MOMENT, kept))

    assert kept.problems["guard"].endswith(
        "Refusal: agterm does not answer. the owner starts agterm"
    )
    assert traces(caplog) == []


def test_a_fault_of_the_keeping_is_a_line_and_its_traceback_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def tick(_duty: object) -> None:
        raise ModuleNotFoundError("No module named 'lem.store.survey'")

    monkeypatch.setattr(runner, "DUTIES", (PRUNE,))
    monkeypatch.setattr(prune, "tick", tick)
    here = here_of(tmp_path)
    kept = Kept()
    caplog.set_level(logging.ERROR)

    runner.ticked(duty_of(here, MOMENT, kept))
    runner.ticked(duty_of(here, MOMENT + timedelta(seconds=20), kept))

    assert kept.problems == {}
    assert len(traces(caplog)) == 1
    err = capsys.readouterr().err
    assert err.count("lem prune failed: ModuleNotFoundError: No module named") == 2


def test_a_workspace_whose_ports_do_not_bind_costs_no_other_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    broken = here_of(tmp_path / "broken")
    shop = here_of(tmp_path / "shop")
    ran: list[str] = []

    def spaces(_home: Path) -> list[tuple[str, Workspace]]:
        return [("broken", broken.where), ("shop", shop.where)]

    def bound(space: Workspace, _environ: object, _home: Path) -> Here:
        if space == broken.where:
            raise Fault(FAULT)
        return shop

    monkeypatch.setattr(runner, "spaces", spaces)
    monkeypatch.setattr(context, "bound", bound)
    monkeypatch.setattr(runner, "ticked", lambda duty: ran.append(duty.name))
    caplog.set_level(logging.ERROR)

    runner.tick(tmp_path / "home", MOMENT)
    runner.tick(tmp_path / "home", MOMENT + timedelta(seconds=20))

    assert ran == ["shop", "shop"]
    problems = MEMORY.problems_of(broken.where.checkout)
    assert problems == (f"the board's duties do not run: Fault: {FAULT}",)
    assert MEMORY.problems_of(shop.where.checkout) == ()
    assert len(traces(caplog)) == 1


def test_a_loop_that_fails_runs_again_and_the_board_keeps_serving(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    ticks: list[int] = []

    def tick(_home: Path) -> None:
        ticks.append(len(ticks))
        if len(ticks) == 1:
            raise Fault(FAULT)

    monkeypatch.setattr(runner, "TICK", 0.05)
    monkeypatch.setattr(runner, "tick", tick)
    caplog.set_level(logging.ERROR)
    board = made(tmp_path, None)

    with board.main() as client:
        deadline = time.monotonic() + 10
        while len(ticks) < 3 and time.monotonic() < deadline:
            time.sleep(0.05)
        assert len(ticks) >= 3
        assert client.get("/api/server").status_code == 200

    [failed] = [one for one in caplog.records if "the duties" in one.getMessage()]
    assert failed.getMessage() == (
        "lem serve: the duties of the board server failed, and runs again"
    )
    assert isinstance(failed.exc_info, tuple)
    assert isinstance(failed.exc_info[1], Fault)


def test_a_loop_that_fails_alike_logs_its_traceback_once_and_a_new_failure_again(
    caplog: pytest.LogCaptureFixture,
) -> None:
    errors = [Fault(FAULT), Fault(FAULT), OSError("the disk is full"), None]

    async def loop(stopping: anyio.Event) -> None:
        error = errors.pop(0)
        if error is None:
            stopping.set()
            return
        raise error

    async def served() -> None:
        await seams.kept_up("the watcher", loop, stopping=anyio.Event())

    caplog.set_level(logging.ERROR)
    anyio.run(served)

    assert errors == []
    failed = [
        one.exc_info[1] for one in caplog.records if isinstance(one.exc_info, tuple)
    ]
    assert [type(one) for one in failed] == [Fault, OSError]
