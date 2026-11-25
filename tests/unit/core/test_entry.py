"""What the test entry runs for each level, the full run's lock, the gates' skip, and the two
commands of pyproject.toml."""

import fcntl
import os
import subprocess
import sys
import threading
from pathlib import Path
from unittest.mock import Mock

import pytest

import gates
import levels
from fakes.command import Ran, lem
from lem.hooks import versions
from lem.kernel import paths

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
    for level, given, said in (
        ("gates", ["x"], "takes no paths"),
        ("full", ["x"], "takes no paths"),
        ("unit", [str(tmp_path / "contract")], "is not in"),
        ("unit", [str(tmp_path / "unit" / "gone.py")], "does not exist"),
        ("model", [], "has no case yet"),
    ):
        with pytest.raises(levels.WrongCall, match=said):
            levels.selection(tmp_path, level, given)


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


def test_the_eslint_gate_skips_with_no_configuration_and_no_node_modules_but_in_full(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gates, "ROOT", tmp_path)
    unit, full = (
        Mock(getoption=Mock(return_value=level)) for level in ("unit", "full")
    )
    with pytest.raises(pytest.skip.Exception, match="no eslint"):
        gates.test_eslint_holds_the_javascript_to_its_style(unit)
    (tmp_path / "eslint.config.mjs").touch()
    with pytest.raises(pytest.skip.Exception, match="npm ci"):
        gates.test_eslint_holds_the_javascript_to_its_style(unit)
    with pytest.raises(pytest.fail.Exception, match="npm ci"):
        gates.test_eslint_holds_the_javascript_to_its_style(full)


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


def test_a_commands_output_is_read_as_its_envelope(tmp_path: Path) -> None:
    printed = Ran(args=("x",), code=0, stdout='{"ok":true,"result":[1,2]}', stderr="")
    assert printed.envelope() == {"ok": True, "result": [1, 2]}
    assert printed.result() == [1, 2]
    stub = lem("help", cwd=tmp_path)
    assert (stub.code, stub.stdout) == (2, "")
    with pytest.raises(AssertionError, match="printed no JSON object"):
        stub.envelope()
    with pytest.raises(AssertionError, match="gave no result"):
        Ran(args=("x",), code=1, stdout='{"ok":false}', stderr="").result()


def plugin_of(folder: Path, version: str) -> Path:
    """A plugin folder whose manifest says `version`."""
    (folder / ".claude-plugin").mkdir(parents=True)
    (folder / ".claude-plugin" / "plugin.json").write_text(
        f'{{"version": "{version}"}}'
    )
    return folder


def test_a_plugin_of_another_version_stops_every_command_but_the_first_answers(
    tmp_path: Path,
) -> None:
    own = versions.version_of(str(paths.root()))
    old = plugin_of(tmp_path / "old", "0.0.1")
    env = {**os.environ, "LEM_PLUGIN_ROOT": str(old)}
    stopped = lem("land", "checks", "fix-the-login", cwd=tmp_path, env=env)
    assert stopped.code == 1
    refused = stopped.envelope()
    assert refused["ok"] is False
    assert refused["refusal"] == {
        "code": "version",
        "why": f"lem: Lem's plugin 0.0.1 ({old}) is behind Lem's app {own}; the owner "
        "runs `claude plugin update lem@lem` and starts the session again",
        "fix": "the owner updates the half that is behind and starts the session again",
    }
    for first in ("doctor", "version", "help"):
        assert lem(first, cwd=tmp_path, env=env).code == 2
    same = plugin_of(tmp_path / "same", own)
    assert (
        lem("land", cwd=tmp_path, env={**os.environ, "LEM_PLUGIN_ROOT": str(same)}).code
        == 2
    )


def test_the_line_names_the_half_that_is_behind(tmp_path: Path) -> None:
    plugin = plugin_of(tmp_path / "plugin", "2.0.0")
    app = plugin_of(tmp_path / "app", "1.9.0")
    assert versions.behind(str(plugin), str(plugin)) is None
    assert "Lem's app 1.9.0" in (versions.behind(str(plugin), str(app)) or "")
    assert "brew upgrade" in (versions.behind(str(plugin), str(app)) or "")
    broken = tmp_path / "broken"
    (broken / ".claude-plugin").mkdir(parents=True)
    (broken / ".claude-plugin" / "plugin.json").write_text("{")
    said = versions.behind(str(broken), str(app)) or ""
    assert "are two versions" in said
    assert "unreadable" in said
