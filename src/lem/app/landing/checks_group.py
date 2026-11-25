"""One command in a process group of its own, so that what it starts ends with it when the run
is stopped: a term, three seconds, a kill, three seconds more; the run then exits as the signal
says (`project.cmd_serial` on `main`)."""

import os
import signal
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from lem.app.landing import checks_stop
from lem.kernel import procs

if TYPE_CHECKING:
    from collections.abc import Generator

# The signals that stop a run, and what a shell adds to a signal's number for its exit.
STOPS = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)
SIGNALLED = 128
# How long the command's group has after the term, then after the kill, in seconds.
GRACE = 3.0


@contextmanager
def trapped() -> Generator[None]:
    """The signals of `STOPS` stop the run once while it is held (`checks_stop.Stopper`), and
    are as before after."""
    stopper = checks_stop.Stopper()
    before = {sign: signal.signal(sign, stopper) for sign in STOPS}
    try:
        yield
    finally:
        for sign, action in before.items():
            signal.signal(sign, action)


def waited(proc: subprocess.Popen[bytes]) -> int:
    """The command's exit, or the exit of the signal that stopped the run."""
    try:
        return proc.wait()
    except InterruptedError as stop:
        return SIGNALLED + stop.args[0]


def argv_of(command: tuple[str, ...]) -> list[str]:
    """One word is a line for the shell; more are the command's own words."""
    if len(command) == 1:
        return ["/bin/sh", "-c", command[0]]
    return list(command)


@contextmanager
def started(argv: list[str]) -> Generator[subprocess.Popen[bytes]]:
    """The command started in a group of its own, which is stopped however the run ends; it
    keeps the caller's standard input, output and errors."""
    proc = subprocess.Popen(
        argv, cwd=Path.cwd(), env=os.environ, start_new_session=True
    )
    try:
        yield proc
    finally:
        procs.stop_group(proc, GRACE, GRACE, whole_group=False)


def exited(command: tuple[str, ...]) -> int:
    """Run the command and give its exit, its group stopped after it."""
    with trapped(), started(argv_of(command)) as proc:
        return waited(proc)
