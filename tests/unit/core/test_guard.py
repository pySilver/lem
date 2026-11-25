"""No test reaches the workspace of the checkout it runs in, and the store never reads or writes
the state of the Lem before: the two guards of `lem.store.guard`."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from fakes.command import lem
from fakes.records import MOMENT, noted, record
from fakes.repo import RealRepo
from lem.kernel.errors import Fault, Refusal
from lem.records.sessions import SessionLine
from lem.store import guard, places, sessions, steps, tasks, workspace

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[3]
CHECKOUT_STATE = (
    places.common_dir(
        next(
            above / ".git"
            for above in (ROOT, *ROOT.parents)
            if (above / ".git").exists()
        )
    ).parent
    / ".lem"
    / "state"
)


def listing(state: Path) -> list[str]:
    """Every path under `state`, for a look that no write happened."""
    return sorted(str(path.relative_to(state)) for path in state.rglob("*"))


def test_a_test_starts_in_a_folder_of_no_repository_under_its_own_root() -> None:
    root = Path(os.environ[guard.TEST_ROOT]).resolve()
    assert Path.cwd().resolve().is_relative_to(root)
    with pytest.raises(Refusal) as refused:
        places.workspace(Path.cwd())
    assert refused.value.code == "no-repository"
    ran = subprocess.run(
        [sys.executable, "-I", "-c", "import os; print(os.getcwd())"],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    assert Path(ran.stdout.strip()).resolve().is_relative_to(root)


class StartsElsewhere(unittest.TestCase):
    def test_a_unittest_case_starts_under_the_root_too(self) -> None:
        root = Path(os.environ[guard.TEST_ROOT]).resolve()
        self.assertTrue(Path.cwd().resolve().is_relative_to(root))


def test_the_checkout_this_test_runs_in_is_no_workspace_of_a_test() -> None:
    with pytest.raises(Fault, match="outside its own folder"):
        places.workspace(ROOT)


def test_a_store_write_outside_the_tests_root_is_a_fault() -> None:
    outside = Path(tempfile.mkdtemp(prefix="lem-outside-", dir="/tmp"))
    try:
        with pytest.raises(Fault, match="outside its own folder"):
            tasks.create(outside, record())
        assert list(outside.iterdir()) == []
    finally:
        shutil.rmtree(outside)


def test_a_command_with_no_folder_runs_in_the_tests_own_and_never_in_the_checkout() -> (
    None
):
    before = listing(CHECKOUT_STATE) if CHECKOUT_STATE.is_dir() else []
    ran = lem("task", "open", "x", "--ask", "a probe")
    assert ran.code != 0
    after = listing(CHECKOUT_STATE) if CHECKOUT_STATE.is_dir() else []
    assert after == before
    with pytest.raises(AssertionError, match="outside the test's own folder"):
        lem("task", "open", "x", "--ask", "a probe", cwd=ROOT)


def old_state(folder: Path) -> Path:
    """A state folder of Lem 0.3: its event log and a task folder with no task.json."""
    state = folder / ".lem" / "state"
    (state / "tasks" / "old-task").mkdir(parents=True)
    (state / ".gitignore").write_text("*\n")
    (state / "events.jsonl").write_text('{"event": "task.state", "task": "old-task"}\n')
    (state / "tasks" / "old-task" / "state.md").write_text(
        "2026-11-20T10:00Z queued: x\n"
    )
    return state


def snapshot(state: Path) -> dict[str, bytes]:
    """Every file under `state` with its bytes."""
    return {
        str(path.relative_to(state)): path.read_bytes()
        for path in state.rglob("*")
        if path.is_file()
    }


def acts(state: Path) -> list[tuple[str, Callable[[], object]]]:
    """Every read and write of the store, on `state`."""
    folder = state / "tasks" / "old-task"
    line = SessionLine(
        at=MOMENT, source="startup", claude="c", transcript="t", task="old-task"
    )

    def step() -> None:
        with steps.step(state, "old-task", "base", MOMENT):
            pass

    def waited() -> None:
        with steps.waited(state, "old-task", "drop", MOMENT):
            pass

    return [
        ("read", lambda: tasks.read(state, "old-task")),
        ("every", lambda: tasks.every(state)),
        ("create", lambda: tasks.create(state, record("new-task"))),
        ("update", lambda: tasks.update(state, "old-task", noted("x"), expect=1)),
        ("claim", lambda: workspace.claimed(state, lambda _every: record("new-task"))),
        ("step", step),
        ("drop", waited),
        ("append", lambda: sessions.append(folder, line)),
        ("sessions", lambda: sessions.read(folder)),
        ("state", lambda: places.state_of(state.parents[1])),
    ]


def test_the_state_of_the_lem_before_is_neither_read_nor_written(
    tmp_path: Path,
) -> None:
    state = old_state(tmp_path)
    before = snapshot(state)
    for name, act in acts(state):
        with pytest.raises(Refusal) as refused:
            act()
        assert refused.value.code == "old-state", name
        assert "holds the state of Lem 0.3" in refused.value.why
        assert "lem doctor" in refused.value.fix
    assert snapshot(state) == before
    assert sorted(path.name for path in state.rglob("*")) == sorted(
        [".gitignore", "events.jsonl", "tasks", "old-task", "state.md"]
    )


def test_a_workspace_with_the_state_of_the_lem_before_is_refused(
    tmp_path: Path,
) -> None:
    repo = RealRepo.init(tmp_path / "repo", {"README.md": b"one\n"})
    old_state(repo.checkout)
    with pytest.raises(Refusal) as refused:
        places.workspace(repo.checkout)
    assert refused.value.code == "old-state"


@pytest.mark.parametrize("held", [(), (".gitignore",)], ids=["absent", "empty"])
def test_an_absent_or_empty_state_folder_gets_the_marker_with_the_first_task(
    tmp_path: Path, held: tuple[str, ...]
) -> None:
    state = tmp_path / "state"
    if held:
        state.mkdir()
        (state / ".gitignore").write_text("*\n")
    assert tasks.every(state) == ()
    assert not (state / guard.MARKER).exists()
    tasks.create(state, record())
    assert (state / guard.MARKER).read_bytes() == b'{"form": 1}\n'
    assert (state / ".gitignore").read_text() == "*\n"
    (state / "forge.json").write_text("{}")
    assert [found.task.slug for found in tasks.every(state)] == ["fix-the-login"]
    assert guard.form(state) == "new"
