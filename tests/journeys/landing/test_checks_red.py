"""The check that each criterion's tests pass on the task's branch and fail on the base commit
(`lem criteria red`), and its five inputs (`lem criteria inputs`), on a real repository: a task
with its worktree and one commit on its branch, each leaf called in this process through
`lem.cli.lazy.main` with `--repo` to the test's own repository, and the stop of a run in a
process of its own.

The working directory is a temporary folder in no repository, so a call that forgot `--repo`
touches nothing.
"""

import contextlib
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from fakes.records import record
from fakes.repo import RealRepo, run_git, write
from lem.cli import lazy
from lem.records.criteria import Criteria
from lem.records.criterion import Criterion, CriterionTest
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    import pytest

type Envelope = dict[str, Any]

SLUG = "fix-the-login"
BRANCH = f"fix/{SLUG}"
SETTINGS = """[branch]
base = "main"

[checks]
commands = ["true"]
"""
# The change on the branch, and a test that needs it.
FEATURE = {"feature.txt": b"the login works\n"}
NEEDS_FEATURE = b"test -f feature.txt\n"
# How long a step of a stopped run may take on a loaded machine, in seconds (unmeasured
# estimate: eight other builders share this Mac).
PATIENCE = 120.0
POLL = 0.1


@dataclass(frozen=True)
class Task:
    """The test's repository and the task's worktree on its branch."""

    repo: RealRepo
    worktree: Path

    @property
    def checkout(self) -> Path:
        return self.repo.checkout

    @property
    def state(self) -> Path:
        return self.checkout / ".lem" / "state"

    def lem(self, capsys: pytest.CaptureFixture[str], *argv: str) -> Envelope:
        """`lem --repo CHECKOUT ARGV` in this process: its envelope, with its exit code."""
        code = lazy.main(["--repo", str(self.checkout), *argv])
        out = capsys.readouterr().out
        return {**json.loads(out), "code": code}

    def red_worktrees(self) -> list[str]:
        """The check's worktrees that are left: as folders, and as git lists them."""
        folders = [path.name for path in self.worktree.parent.glob(f"{SLUG}.red-*")]
        listed = run_git(self.checkout, "worktree", "list", "--porcelain")
        return folders + [line for line in listed.splitlines() if ".red-" in line]


def held_by(command: str, *files: str) -> Criteria:
    """One criterion held by one test."""
    test = CriterionTest(command=command, files=files)
    criterion = Criterion(number=1, text="the login works", tests=(test,))
    return Criteria(criteria=(criterion,), digest="d")


def made(
    folder: Path,
    monkeypatch: pytest.MonkeyPatch,
    criteria: Criteria,
    branch_files: Mapping[str, bytes],
    settings: str = SETTINGS,
) -> Task:
    """A repository with Lem's settings on `main`, the task's record, and its worktree with one
    commit of `branch_files` on its branch."""
    files = {"README.md": b"The login.\n", ".lem/settings.toml": settings.encode()}
    repo = RealRepo.init(folder / "repo", files)
    tasks.create(
        repo.checkout / ".lem" / "state", record(SLUG, branch=BRANCH, criteria=criteria)
    )
    worktree = repo.checkout / ".lem" / "worktrees" / SLUG
    run_git(repo.checkout, "worktree", "add", "-q", "-b", BRANCH, str(worktree), "main")
    staged: dict[str, bytes | None] = dict(branch_files)
    write(worktree, staged)
    run_git(worktree, "add", "--all")
    run_git(worktree, "commit", "--quiet", "--message", "the change")
    monkeypatch.chdir(folder)
    return Task(repo=repo, worktree=worktree)


def test_a_test_that_passes_on_the_branch_and_fails_on_the_base_holds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    files = {**FEATURE, "tests/check.sh": NEEDS_FEATURE}
    task = made(
        tmp_path, monkeypatch, held_by("sh tests/check.sh", "tests/check.sh"), files
    )
    envelope = task.lem(capsys, "criteria", "red", SLUG)
    assert envelope["code"] == 0, envelope
    run = envelope["result"]
    assert run["ok"] is True
    assert run["tests"] == [
        {
            "criterion": 1,
            "command": "sh tests/check.sh",
            "files": ["tests/check.sh"],
            "on_branch": 0,
            "on_base": 1,
        }
    ]
    assert run["run_without"] == ["feature.txt"]
    assert run["inputs"]["tip"] == run_git(task.worktree, "rev-parse", "HEAD")
    kept = tasks.read(task.state, SLUG).task.criteria.red
    assert kept is not None
    assert kept.ok
    assert kept.tests[0].on_base == 1
    assert task.red_worktrees() == []


def test_a_test_that_passes_on_the_base_too_does_not_hold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    files = {**FEATURE, "tests/check.sh": b"test -f README.md\n"}
    task = made(
        tmp_path, monkeypatch, held_by("sh tests/check.sh", "tests/check.sh"), files
    )
    envelope = task.lem(capsys, "criteria", "red", SLUG)
    assert envelope["code"] == 1, envelope
    assert envelope["refusal"]["code"] == "criteria"
    assert envelope["refusal"]["why"] == (
        "criterion 1: `sh tests/check.sh` passes on the base commit too, so it does not "
        "test the change"
    )
    kept = tasks.read(task.state, SLUG).task.criteria.red
    assert kept is not None
    assert not kept.ok
    assert kept.tests[0].problem is not None
    assert task.red_worktrees() == []


def test_a_test_whose_script_the_base_lacks_does_not_start_there_and_does_not_hold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    files = {
        **FEATURE,
        "tests/check.sh": NEEDS_FEATURE,
        "tests/run.sh": b"sh tests/check.sh\n",
    }
    task = made(
        tmp_path, monkeypatch, held_by("sh tests/run.sh", "tests/check.sh"), files
    )
    envelope = task.lem(capsys, "criteria", "red", SLUG)
    assert envelope["code"] == 1, envelope
    why = envelope["refusal"]["why"]
    assert why.startswith(
        "criterion 1: `sh tests/run.sh` does not start on the base commit"
    )
    assert "its script file tests/run.sh is not on the base commit" in why
    kept = tasks.read(task.state, SLUG).task.criteria.red
    assert kept is not None
    assert kept.run_without == ("feature.txt", "tests/run.sh")


def test_a_failed_checks_setup_is_refused_with_its_exit_and_leaves_no_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    files = {**FEATURE, "tests/check.sh": NEEDS_FEATURE}
    settings = f'{SETTINGS}setup = ["exit 3"]\n'
    criteria = held_by("sh tests/check.sh", "tests/check.sh")
    task = made(tmp_path, monkeypatch, criteria, files, settings)
    envelope = task.lem(capsys, "criteria", "red", SLUG)
    assert envelope["code"] == 1, envelope
    assert envelope["refusal"]["why"] == (
        "`exit 3` of checks.setup failed in a fresh worktree of the branch (exit 3), so no "
        "test could run there; its worktrees are removed"
    )
    assert envelope["refusal"]["fix"] == "correct that command in .lem/settings.toml"
    assert task.red_worktrees() == []
    assert tasks.read(task.state, SLUG).task.criteria.red is None


def test_a_criterion_with_neither_a_test_nor_a_reason_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    criteria = Criteria(
        criteria=(Criterion(number=1, text="the login works"),), digest="d"
    )
    task = made(tmp_path, monkeypatch, criteria, FEATURE)
    envelope = task.lem(capsys, "criteria", "red", SLUG)
    assert envelope["code"] == 1, envelope
    assert envelope["refusal"]["why"].startswith("criterion 1 names no test")
    assert task.red_worktrees() == []


def test_a_named_file_that_is_a_folder_on_the_branch_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    files = {**FEATURE, "tests/check.sh": NEEDS_FEATURE}
    task = made(tmp_path, monkeypatch, held_by("sh tests/check.sh", "tests"), files)
    envelope = task.lem(capsys, "criteria", "red", SLUG)
    assert envelope["code"] == 1, envelope
    assert (
        envelope["refusal"]["why"] == "criterion 1: 'tests' is a folder on the branch"
    )


def test_criteria_inputs_gives_the_five_inputs_and_refuses_as_red_does(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    settings = f'{SETTINGS}setup = ["true"]\nserial = ["sh tests/serial"]\n'
    criteria = held_by("sh tests/check.sh", "tests/check.sh")
    task = made(tmp_path, monkeypatch, criteria, FEATURE, settings)
    envelope = task.lem(capsys, "criteria", "inputs", SLUG)
    assert envelope["code"] == 0, envelope
    assert envelope["result"] == {
        "task": SLUG,
        "inputs": {
            "tip": run_git(task.worktree, "rev-parse", "HEAD"),
            "base": run_git(task.checkout, "rev-parse", "main"),
            "setup": ["true"],
            "serial": ["sh tests/serial"],
        },
    }
    run_git(task.checkout, "worktree", "remove", "--force", str(task.worktree))
    for verb in ("inputs", "red"):
        refused = task.lem(capsys, "criteria", verb, SLUG)
        assert refused["code"] == 1, refused
        assert (
            refused["refusal"]["why"] == f"the task has no worktree at {task.worktree}"
        )


def test_a_serial_test_runs_under_the_serial_lock_on_the_branch_and_on_the_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    answers = tmp_path / "answers.txt"
    probe = tmp_path / "probe.py"
    probe.write_text(
        "import fcntl, sys\n"
        "with open(sys.argv[1], 'a+') as lock:\n"
        "    try:\n"
        "        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
        "    except BlockingIOError:\n"
        "        print('held')\n"
        "    else:\n"
        "        print('free')\n"
    )
    lock = tmp_path / "repo" / "checkout" / ".lem" / "state" / "locks" / "serial.lock"
    script = f'"{sys.executable}" -I "{probe}" "{lock}" >> "{answers}"\ntest -f feature.txt\n'
    files = {**FEATURE, "tests/serial/probe.sh": script.encode()}
    settings = f'{SETTINGS}serial = ["sh tests/serial"]\n'
    criteria = held_by("sh tests/serial/probe.sh", "tests/serial/probe.sh")
    task = made(tmp_path, monkeypatch, criteria, files, settings)
    envelope = task.lem(capsys, "criteria", "red", SLUG)
    assert envelope["code"] == 0, envelope
    assert envelope["result"]["tests"][0]["on_base"] == 1
    assert answers.read_text().split() == ["held", "held"]


def test_a_stopped_run_ends_its_tests_removes_its_worktrees_and_frees_the_serial_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pids, marker = tmp_path / "pids.txt", tmp_path / "running"
    script = (
        "trap '' TERM\n"
        "sleep 600 &\n"
        f'echo $$ $! $PPID > "{pids}"\n'
        f'touch "{marker}"\n'
        "wait\n"
    )
    files = {**FEATURE, "tests/serial/stubborn.sh": script.encode()}
    settings = f'{SETTINGS}serial = ["sh tests/serial"]\n'
    criteria = held_by("sh tests/serial/stubborn.sh", "tests/serial/stubborn.sh")
    task = made(tmp_path, monkeypatch, criteria, files, settings)
    said = tmp_path / "said.json"
    argv = [sys.executable, "-I", "-B", "-m", "lem", "--repo", str(task.checkout)]
    with said.open("wb") as output:
        proc = subprocess.Popen(
            [*argv, "criteria", "red", SLUG],
            cwd=tmp_path,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    started: list[int] = []
    try:
        waited_for(marker.exists)
        started = [int(word) for word in pids.read_text().split()]
        proc.send_signal(signal.SIGTERM)
        assert proc.wait(timeout=PATIENCE) == 1
        envelope = json.loads(said.read_text())
        assert envelope["refusal"]["why"] == (
            "the check was stopped, and its commands are ended; its worktrees are removed"
        )
        for pid in started:
            waited_for(lambda pid=pid: gone(pid))
        # each is gone, so the cleanup below must not reach a process that took its number
        started.clear()
        assert task.red_worktrees() == []
        free = subprocess.run(
            [*argv, "serial", "--", "true"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=PATIENCE,
            check=False,
        )
        assert free.returncode == 0, free.stderr
        assert "holds the lock" not in free.stderr
    finally:
        ended(proc, started)


def waited_for(done: Callable[[], bool]) -> None:
    """Wait until `done` holds; the case fails when it does not within PATIENCE."""
    deadline = time.monotonic() + PATIENCE
    while not done():
        assert time.monotonic() < deadline, "waited too long"
        time.sleep(POLL)


def gone(pid: int) -> bool:
    """Whether no process `pid` is left."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


def ended(proc: subprocess.Popen[bytes], pids: list[int]) -> None:
    """End what the case started, whatever is left of it."""
    if proc.poll() is None:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
    for pid in pids:
        with contextlib.suppress(ProcessLookupError):
            os.kill(pid, signal.SIGKILL)
