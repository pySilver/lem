"""The board server's runner and loops under a failure: a duty's fault is its board's problem
with its traceback in the server's log at most once an hour, and the next tick tries it again;
a refusal has no traceback; a workspace whose ports do not bind costs no other workspace; and a
loop of the server's life whose step fails is every board's problem until a step runs, while
the board keeps serving."""

import itertools
import logging
import time
from datetime import timedelta
from typing import TYPE_CHECKING

import anyio

from fakes.records import MOMENT
from lem.board import turns
from lem.board.duties import context, guard, memory, prune, runner
from lem.board.duties.memory import MEMORY, Kept, Traces
from lem.kernel.errors import Fault, Refusal
from unit.board.duties.world import duty_of
from unit.board.service.given import made
from unit.sessions.world import here_of

if TYPE_CHECKING:
    from collections.abc import Callable
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


def test_a_duty_fault_whose_words_change_writes_one_traceback_an_hour(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    calls: list[int] = []

    def tick(_duty: object) -> None:
        calls.append(len(calls))
        raise Fault(f"the fault of call {len(calls)}")

    monkeypatch.setattr(runner, "DUTIES", (GUARD,))
    monkeypatch.setattr(guard, "tick", tick)
    here = here_of(tmp_path)
    kept = Kept()
    caplog.set_level(logging.ERROR)
    for step in range(3):
        runner.ticked(duty_of(here, MOMENT + timedelta(seconds=20 * step), kept))
    assert kept.problems["guard"].endswith("Fault: the fault of call 3")
    assert len(traces(caplog)) == 1

    monkeypatch.setattr(memory, "TRACE_EVERY", 0.0)
    runner.ticked(duty_of(here, MOMENT + timedelta(hours=2), kept))

    [_, later] = traces(caplog)
    assert "(2 more failures of it since its last traceback)" in later.getMessage()


def test_a_trace_is_due_once_in_each_hour_with_the_count_of_failures_since() -> None:
    held = Traces()
    assert held.due("guard", 0.0) == 0
    assert held.due("guard", 10.0) is None
    assert held.due("guard", 3599.0) is None
    assert held.due("guard", 3600.0) == 2
    assert held.due("forge", 3600.0) == 0
    assert held.due("guard", 3601.0) is None


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


def test_a_loop_that_fails_is_every_boards_problem_until_a_step_runs_and_the_board_serves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    ticks: list[int] = []
    failing = [True]

    def tick(_home: Path) -> None:
        ticks.append(len(ticks))
        if failing[0]:
            raise Fault(FAULT)

    monkeypatch.setattr(runner, "TICK", 0.05)
    monkeypatch.setattr(runner, "tick", tick)
    caplog.set_level(logging.ERROR)
    board = made(tmp_path, None)
    said = "the duties of the board server failed, and runs again every 0.05 s"

    with board.main() as client:
        waited(lambda: len(ticks) >= 3)
        assert client.get("/api/server").status_code == 200
        assert f"{said}: Fault:" in client.get("/studio/shop/").text
        failing[0] = False
        waited(lambda: MEMORY.loop_problem(runner.NAME) is None)
        assert said not in client.get("/studio/shop/").text

    [failed] = [one for one in caplog.records if "the duties" in one.getMessage()]
    assert failed.getMessage() == (
        "lem serve: the duties of the board server failed, and runs again "
        "(0 more failures of it since its last traceback)"
    )
    assert isinstance(failed.exc_info, tuple)
    assert isinstance(failed.exc_info[1], Fault)


def waited(done: Callable[[], bool]) -> None:
    """Wait until `done` holds, ten seconds at most."""
    deadline = time.monotonic() + 10
    while not done() and time.monotonic() < deadline:
        time.sleep(0.02)
    assert done()


def test_a_step_that_fails_at_once_waits_its_period_and_logs_one_traceback(
    caplog: pytest.LogCaptureFixture,
) -> None:
    errors: list[Exception | None] = [Fault(FAULT), OSError("the disk is full"), None]
    moments: list[float] = []

    async def served() -> None:
        stopping = anyio.Event()

        def step() -> None:
            moments.append(time.monotonic())
            error = errors.pop(0)
            if error is not None:
                raise error
            anyio.from_thread.run_sync(stopping.set)

        turn = turns.Turn(name="the watcher", every=0.2, step=step)
        with anyio.fail_after(10):
            await turns.kept_up(turn, stopping)

    caplog.set_level(logging.ERROR)
    anyio.run(served)

    assert errors == []
    assert all(later - first >= 0.2 for first, later in itertools.pairwise(moments))
    failed = [
        one.exc_info[1] for one in caplog.records if isinstance(one.exc_info, tuple)
    ]
    assert [type(one) for one in failed] == [Fault]
    assert MEMORY.loop_problem("the watcher") is None
