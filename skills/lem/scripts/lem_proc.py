"""The stop of a command's process group: the one way `land.py`, `criteria.py` and
`project.py serial` end a project's own checks.

Each command of the checks starts in a process group of its own, so that what it
starts (a server a test put up, a worker) ends with it. The stop sends the group a
term, waits, and sends a kill to what is left: a test that ignores a term must not run
on with the lock free. Two waits are in use, and each caller keeps its own. The
landing waits for the whole group to end (`whole_group`), so a group that ends within
its grace gets no kill. The criteria's check and a serial run wait for the command's
first process only, and send the kill to whatever it left in the group as soon as it
ended. The grace after each signal is the caller's too: a serial wrapper's own cleanup
needs longer than a command (`SERIAL_GRACE`), and `tests/lem-serial.sh` and the
`lem-land-*` suites hold each.

It imports nothing of Lem's.
"""

import contextlib
import os
import signal
import subprocess
import time

# how often the wait for a whole group looks whether a process of it is left
POLL = 0.05


def group_gone(proc: subprocess.Popen, seconds: float) -> bool:
    """Whether no process of PROC's group is left within SECONDS: the group is asked
    each POLL seconds, and PROC reaped as soon as it ends."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            os.killpg(proc.pid, 0)
        except (ProcessLookupError, PermissionError):
            return True
        if proc.poll() is None:
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=POLL)
        else:
            time.sleep(POLL)
    return False


def stop_group(
    proc: subprocess.Popen, term_grace: float, kill_grace: float, *, whole_group: bool
) -> None:
    """End PROC's process group and everything still in it: a term, then a kill. With
    WHOLE_GROUP the kill goes only to a group that is still there TERM_GRACE seconds
    after the term; without, it goes to what is left as soon as PROC ended, or after
    TERM_GRACE seconds when PROC did not. KILL_GRACE is the wait after the kill. A group
    that is gone, or not this user's, ends the stop."""
    for sign, grace in ((signal.SIGTERM, term_grace), (signal.SIGKILL, kill_grace)):
        try:
            os.killpg(proc.pid, sign)
        except (ProcessLookupError, PermissionError):
            return
        if whole_group:
            if group_gone(proc, grace):
                return
            continue
        try:
            proc.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            continue
        # the leader ended; a process it left in the group gets the next signal too
        try:
            os.killpg(proc.pid, 0)
        except (ProcessLookupError, PermissionError):
            return
