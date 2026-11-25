"""What the board server keeps of a workspace between ticks: a duty that failed waits five
minutes for its next try, one done for good is not done again, and the board's problems."""

import threading
from datetime import timedelta
from typing import TYPE_CHECKING

from fakes.records import MOMENT
from lem.board.duties.memory import RETRY, Kept, Memory

if TYPE_CHECKING:
    from pathlib import Path

KEY = ("wake", "gift-note", "queue")


def test_a_failed_duty_waits_five_minutes_and_one_that_ran_is_forgotten() -> None:
    kept = Kept()
    assert kept.due(KEY, MOMENT) is True
    kept.ended(KEY, MOMENT, ran=False)
    assert kept.due(KEY, MOMENT + RETRY - timedelta(seconds=1)) is False
    assert kept.due(KEY, MOMENT + RETRY) is True
    kept.ended(KEY, MOMENT + RETRY, ran=True)
    assert kept.failed == {}
    assert timedelta(minutes=5) == RETRY


def test_a_duty_done_for_good_is_owed_no_more() -> None:
    kept = Kept()
    assert kept.owed(KEY, MOMENT) is True
    kept.done.add(KEY)
    assert kept.owed(KEY, MOMENT + RETRY) is False


def test_only_a_merge_whose_thread_lives_runs() -> None:
    gate = threading.Event()
    alive = threading.Thread(target=gate.wait)
    alive.start()
    ended = threading.Thread(target=lambda: None)
    ended.start()
    ended.join()
    kept = Kept(merging={"runs": alive, "ended": ended})
    assert kept.running() == frozenset({"runs"})
    gate.set()
    alive.join()


def test_each_workspace_has_its_own_keeping_and_its_boards_problems(
    tmp_path: Path,
) -> None:
    memory = Memory()
    first = memory.of(tmp_path / "shop")
    assert memory.of(tmp_path / "shop") is first
    assert memory.of(tmp_path / "other") is not first
    first.problems["forge"] = "the board cannot ask GitHub"
    assert memory.problems_of(tmp_path / "shop") == ("the board cannot ask GitHub",)
    assert memory.problems_of(tmp_path / "other") == ()
