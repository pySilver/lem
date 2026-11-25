"""A command's process group, and its stop.

Each command of a project's checks starts in a process group of its own, so that what it starts
(a server a test put up, a worker) ends with it. The stop sends the group a term, waits, and
sends a kill to what is left: a test that ignores a term must not run on with a lock free. Two
waits are in use, and each caller keeps its own: the landing waits for the whole group to end
(`whole_group`), the criteria's check and a serial run for the command's first process only.
"""

import contextlib
import os
import signal
import subprocess
import time
from typing import IO, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

type Environment = Mapping[str, str]
type Output = IO[bytes] | int | None

# How often the wait for a whole group looks whether a process of it is left, in seconds.
POLL = 0.05


def start_group(
    argv: list[str], cwd: Path, env: Environment, output: Output
) -> subprocess.Popen[bytes]:
    """Start `argv` in `cwd` as the leader of a new process group, its output and errors both
    to `output` (a file, a `subprocess` constant, or None for the caller's), and nothing on its
    standard input."""
    return subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=output,
        stderr=None if output is None else subprocess.STDOUT,
        start_new_session=True,
    )


def group_gone(proc: subprocess.Popen[bytes], seconds: float) -> bool:
    """Whether no process of the group of `proc` is left within `seconds`."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            os.killpg(proc.pid, 0)
        except ProcessLookupError, PermissionError:
            return True
        if proc.poll() is None:
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=POLL)
        else:
            time.sleep(POLL)
    return False


def signalled(proc: subprocess.Popen[bytes], sign: int) -> bool:
    """Send `sign` to the group of `proc` (0 only asks whether it is there); False when the
    group is gone or not this user's."""
    try:
        os.killpg(proc.pid, sign)
    except ProcessLookupError, PermissionError:
        return False
    return True


def leader_ended(proc: subprocess.Popen[bytes], grace: float) -> bool:
    """Whether `proc` ended within `grace` seconds and left no process in its group."""
    try:
        proc.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        return False
    return not signalled(proc, 0)


def stop_group(
    proc: subprocess.Popen[bytes],
    term_grace: float,
    kill_grace: float,
    *,
    whole_group: bool,
) -> None:
    """End the group of `proc`: a term, then a kill. With `whole_group` the kill goes only to a
    group still there `term_grace` seconds after the term; without, it goes to what is left as
    soon as `proc` ended. `kill_grace` is the wait after the kill."""
    for sign, grace in ((signal.SIGTERM, term_grace), (signal.SIGKILL, kill_grace)):
        if not signalled(proc, sign):
            return
        ended = group_gone(proc, grace) if whole_group else leader_ended(proc, grace)
        if ended:
            return
