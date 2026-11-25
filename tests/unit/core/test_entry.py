"""What the test entry runs for each level, the full run's lock, the gates' skip, and the two
commands of pyproject.toml."""

import fcntl
import subprocess
import sys
import threading
from pathlib import Path

import pytest

import gates
import levels

BIN = Path(sys.executable).parent


def test_gates_runs_the_gates_file_and_full_every_level_with_a_folder(
    tmp_path: Path,
) -> None:
    for name in ("unit", "contract"):
        (tmp_path / name).mkdir()
    gates_file = str(tmp_path / "gates.py")
    assert levels.selection(tmp_path, "gates", []) == [gates_file]
    assert levels.selection(tmp_path, "full", []) == [
        gates_file,
        str(tmp_path / "unit"),
        str(tmp_path / "contract"),
    ]


def test_a_level_runs_its_folder_or_the_paths_inside_it(tmp_path: Path) -> None:
    case = tmp_path / "unit" / "core" / "test_a.py"
    case.parent.mkdir(parents=True)
    case.touch()
    assert levels.selection(tmp_path, "unit", []) == [str(tmp_path / "unit")]
    assert levels.selection(tmp_path, "unit", [str(case), f"{case}::test_b[1]"]) == [
        str(case.resolve()),
        f"{case.resolve()}::test_b[1]",
    ]


def test_a_selection_the_entry_cannot_run_is_refused_with_its_fix(
    tmp_path: Path,
) -> None:
    (tmp_path / "unit").mkdir()
    (tmp_path / "contract").mkdir()
    for level, paths, said in (
        ("gates", ["x"], "takes no paths"),
        ("full", ["x"], "takes no paths"),
        ("unit", [str(tmp_path / "contract")], "is not in"),
        ("unit", [str(tmp_path / "unit" / "gone.py")], "does not exist"),
        ("model", [], "has no case yet"),
    ):
        with pytest.raises(levels.WrongCall, match=said):
            levels.selection(tmp_path, level, paths)


def test_only_a_full_run_takes_the_machine_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert Path("/tmp/lem-full-run.lock") == levels.FULL_LOCK
    lock = tmp_path / "full.lock"
    monkeypatch.setattr(levels, "FULL_LOCK", lock)
    with levels.lock_of("unit"):
        assert not lock.exists()
    with (
        levels.lock_of("full"),
        lock.open("a") as other,
        pytest.raises(BlockingIOError),
    ):
        fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)


def test_a_full_run_waits_while_another_holds_the_lock(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    lock = tmp_path / "full.lock"
    entered = threading.Event()

    def second_run() -> None:
        with levels.full_run_lock(lock):
            entered.set()

    with lock.open("a") as first:
        fcntl.flock(first, fcntl.LOCK_EX)
        waiting = threading.Thread(target=second_run)
        waiting.start()
        assert not entered.wait(0.5)
        fcntl.flock(first, fcntl.LOCK_UN)
    assert entered.wait(30)
    waiting.join()
    assert f"waits for the full run that holds {lock}" in capfd.readouterr().err


def test_the_eslint_gate_is_a_skip_with_no_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gates, "ROOT", tmp_path)
    with pytest.raises(pytest.skip.Exception, match="no eslint"):
        gates.test_eslint_holds_the_javascript_to_its_style()
    (tmp_path / "eslint.config.mjs").touch()
    with pytest.raises(pytest.fail.Exception, match="npm ci"):
        gates.test_eslint_holds_the_javascript_to_its_style()


def test_the_two_commands_run_their_stubs_and_say_nothing() -> None:
    for command, code in (("lem", 2), ("lem-hook", 0)):
        ran = subprocess.run(
            [BIN / command], capture_output=True, text=True, check=False, timeout=30
        )
        assert (command, ran.returncode, ran.stdout, ran.stderr) == (
            command,
            code,
            "",
            "",
        )
