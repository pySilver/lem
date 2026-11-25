"""The kernel: a moment, a file written whole, an artifact published once, a lock, a
process group's stop, a fault's log line, and the places of Lem's own files."""

import os
import signal
import subprocess
import sys
from datetime import UTC, datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pytest

from lem.kernel import clock, files, locks, logs, paths, procs
from lem.kernel.errors import Fault, Refusal

if TYPE_CHECKING:
    from pathlib import Path

MOMENT = datetime(2026, 11, 24, 10, 18, 18, tzinfo=UTC)


def test_a_moment_is_utc_to_the_second_and_shown_two_ways() -> None:
    now = clock.now()
    assert (now.tzinfo, now.microsecond) == (UTC, 0)
    east = MOMENT.astimezone(timezone(timedelta(hours=2)))
    assert clock.minute(east) == "2026-11-24T10:18Z"
    assert clock.compact(east) == "20261124T101818Z"


def test_a_file_is_written_whole_and_leaves_no_temporary_file(tmp_path: Path) -> None:
    path = tmp_path / "pr.md"
    files.write_whole(path, b"first")
    files.write_whole(path, b"second")
    assert path.read_bytes() == b"second"
    assert [found.name for found in tmp_path.iterdir()] == ["pr.md"]


def test_an_artifact_is_published_once_and_never_changed(tmp_path: Path) -> None:
    path = tmp_path / "reviews" / "review-1.json"
    digest = files.publish(path, b"{}")
    assert digest == files.digest(b"{}")
    assert len(digest) == 64
    assert files.publish(path, b"{}") == digest
    with pytest.raises(Fault, match="published already"):
        files.publish(path, b"[]")
    assert path.read_bytes() == b"{}"


def test_a_tried_lock_gives_none_while_held_and_the_lock_after(tmp_path: Path) -> None:
    path = tmp_path / "merge.lock"
    with locks.held(path), locks.tried(path) as other:
        assert other is None
    with locks.tried(path) as other:
        assert other is not None


def test_a_group_stop_ends_what_the_command_left_behind(tmp_path: Path) -> None:
    left = tmp_path / "left.pid"
    script = (
        "import subprocess, sys, time\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        f"open({str(left)!r}, 'w').write(str(child.pid))\n"
        "time.sleep(60)\n"
    )
    proc = procs.start_group(
        [sys.executable, "-I", "-c", script], tmp_path, dict(os.environ), None
    )
    try:
        while not left.exists() or not left.read_text():
            assert proc.poll() is None
        child = int(left.read_text())
        procs.stop_group(proc, 5, 5, whole_group=True)
        assert procs.group_gone(proc, 5)
        with pytest.raises(ProcessLookupError):
            os.kill(child, 0)
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()


def test_a_leader_that_ignores_a_term_gets_the_kill(tmp_path: Path) -> None:
    script = "import signal, time\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)\nprint('ready', flush=True)\ntime.sleep(60)\n"
    proc = procs.start_group(
        [sys.executable, "-I", "-c", script],
        tmp_path,
        dict(os.environ),
        subprocess.PIPE,
    )
    assert proc.stdout is not None
    assert proc.stdout.readline() == b"ready\n"
    procs.stop_group(proc, 0.5, 5, whole_group=False)
    assert proc.wait(timeout=5) == -signal.SIGKILL
    proc.stdout.close()


def test_a_fault_goes_to_the_log_and_the_owner_reads_its_first_line(
    tmp_path: Path,
) -> None:
    log = tmp_path / "home" / "lem.log"
    try:
        raise Fault("the record broke\nmore detail")
    except Fault as error:
        failed = logs.fault(log, error, ["land", "checks", "a task"])
    assert (failed.line, failed.log) == ("the record broke", str(log))
    written = log.read_text()
    assert " lem land checks 'a task'\n" in written
    assert "Traceback" in written
    assert "lem.kernel.errors.Fault: the record broke" in written


def test_lems_home_folder_follows_xdg_and_refuses_a_relative_one(
    tmp_path: Path,
) -> None:
    assert paths.home({"XDG_CONFIG_HOME": str(tmp_path)}) == tmp_path / "lem"
    assert paths.home({"HOME": str(tmp_path)}) == tmp_path / ".config" / "lem"
    with pytest.raises(Refusal) as refused:
        paths.home({"XDG_CONFIG_HOME": "relative"})
    assert refused.value.code == "config-home"


def test_the_plugins_files_are_in_the_installed_data_or_the_checkout(
    tmp_path: Path,
) -> None:
    assert (paths.root() / "skills" / "lem" / "SKILL.md").is_file()
    installed = tmp_path / "site" / "lem"
    (installed / "data").mkdir(parents=True)
    assert paths.root(installed) == installed / "data"
    with pytest.raises(Fault, match="installs Lem again"):
        paths.root(tmp_path / "nowhere" / "src" / "lem")
