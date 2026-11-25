"""The step lock and the workspace lock: a step refused while another holds the lock, its holder
named, no child process holding it, a drop that waits, and a claim's scan and publication
under one lock."""

import subprocess
import sys
import threading
from typing import TYPE_CHECKING

import pytest

from fakes.records import MOMENT, record
from lem.kernel import locks
from lem.kernel.errors import Refusal
from lem.store import steps, tasks, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

PROBE = """\
import fcntl, sys
with open(sys.argv[1], "a+") as stream:
    try:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("held")
    else:
        print("free")
"""


def probe(path: Path) -> str:
    """Whether another process finds `path` locked."""
    ran = subprocess.run(
        [sys.executable, "-I", "-c", PROBE, str(path)],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return ran.stdout.strip()


def test_a_second_step_is_refused_with_the_holder_named(tmp_path: Path) -> None:
    tasks.create(tmp_path, record())
    lock = tmp_path / "tasks" / "fix-the-login" / "step.lock"
    with steps.step(tmp_path, "fix-the-login", "checks", MOMENT):
        holder = steps.holder_of(lock)
        assert holder is not None
        assert (holder.step, holder.since) == ("checks", MOMENT)
        assert probe(lock) == "held"
        with (
            pytest.raises(Refusal) as refused,
            steps.step(tmp_path, "fix-the-login", "base", MOMENT),
        ):
            pass
        assert refused.value.code == "step-held"
        assert "lem land checks fix-the-login (since 2026-11-25T10:00Z" in (
            refused.value.why
        )
        assert (
            refused.value.fix
            == "wait for it to end, then run lem land base fix-the-login"
        )
    assert steps.holder_of(lock) is None
    assert probe(lock) == "free"


def test_a_process_the_step_starts_does_not_hold_the_step_lock(tmp_path: Path) -> None:
    tasks.create(tmp_path, record())
    lock = tmp_path / "tasks" / "fix-the-login" / "step.lock"
    with steps.step(tmp_path, "fix-the-login", "checks", MOMENT):
        server = subprocess.Popen(
            [sys.executable, "-I", "-c", "import time; time.sleep(60)"]
        )
    try:
        assert server.poll() is None
        assert probe(lock) == "free"
    finally:
        server.terminate()
        server.wait(timeout=30)


def test_a_drop_waits_for_the_step_and_then_holds_the_lock(tmp_path: Path) -> None:
    tasks.create(tmp_path, record())
    lock = tmp_path / "tasks" / "fix-the-login" / "step.lock"
    dropped = threading.Event()

    def drop() -> None:
        with steps.waited(tmp_path, "fix-the-login", "drop", MOMENT):
            dropped.set()
            holder = steps.holder_of(lock)
            assert holder is not None
            assert holder.step == "drop"

    with steps.step(tmp_path, "fix-the-login", "checks", MOMENT):
        waiting = threading.Thread(target=drop)
        waiting.start()
        assert not dropped.wait(0.5)
    assert dropped.wait(30)
    waiting.join()


def test_a_lock_named_by_no_holder_is_refused_without_a_name(tmp_path: Path) -> None:
    refusal = steps.refusal("fix-the-login", "base", None)
    assert refusal.why == "another step of fix-the-login holds its lock"


def test_two_claims_of_one_ticket_publish_one_task(tmp_path: Path) -> None:
    claimed: list[str] = []
    refused: list[str] = []
    start = threading.Barrier(2)

    def claim_for(slug: str) -> None:
        def rule(every: tuple[Record, ...]) -> Record:
            if any(found.task.ask == "ticket MBZ-12" for found in every):
                raise Refusal("ticket-held", "MBZ-12 is held", "pick another ticket")
            return record(slug, ask="ticket MBZ-12")

        start.wait()
        try:
            workspace.claimed(tmp_path, rule)
        except Refusal:
            refused.append(slug)
        else:
            claimed.append(slug)

    threads = [
        threading.Thread(target=claim_for, args=(slug,)) for slug in ("one", "two")
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert (len(claimed), len(refused)) == (1, 1)
    assert [found.task.slug for found in tasks.every(tmp_path)] == claimed


def test_the_claim_holds_the_workspace_lock_while_it_scans(tmp_path: Path) -> None:
    lock = tmp_path / "locks" / "workspace.lock"
    seen: list[str] = []

    def rule(every: tuple[Record, ...]) -> Record:
        seen.append(probe(lock))
        return record("first")

    workspace.claimed(tmp_path, rule)
    assert seen == ["held"]
    with locks.tried(lock) as stream:
        assert stream is not None
