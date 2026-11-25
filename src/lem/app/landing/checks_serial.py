"""`lem serial -- COMMAND...`: one command under the repository's one lock for the tests that two
tasks cannot run at the same time (`checks.serial`), with its exit status given back
(`project.cmd_serial` on `main`).

Another run that holds the lock is waited for, and the wait says on standard error who holds it.
The lock is the kernel's, so it goes with its process however that ends: a stale lock file of a
dead process blocks nothing. The command runs in a process group of its own
(`checks_group.py`).
"""

import fcntl
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import IO, TYPE_CHECKING

from lem.app.landing import checks_group
from lem.kernel import clock, locks
from lem.kernel.errors import Refusal
from lem.store import guard, places

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

LOCK = "serial.lock"


def words_of(words: Sequence[str]) -> tuple[str, ...]:
    """The command's words, past a leading `--`; a call with none is refused."""
    leading = words[:1] == ("--",)
    found = tuple(words[1:] if leading else words)
    blank = not "".join(found).strip()
    if blank:
        raise Refusal(
            "serial-call",
            "lem serial takes the command to run, and this call gives none",
            "lem serial -- COMMAND ..., or one quoted line for the shell",
        )
    return found


@contextmanager
def holding(path: Path, shown: str) -> Generator[None]:
    """Hold the serial lock, waiting for its holder, with this run's line in it while held."""
    with path.open("a+", encoding="utf-8") as stream:
        if not locks.taken(stream):
            waits(stream)
        named(stream, holder_line(shown))
        try:
            yield
        finally:
            named(stream, "")


def holder_line(shown: str) -> str:
    """Who holds the lock: this process, since when, where, and its command."""
    since = clock.minute(clock.now())
    return f"pid {os.getpid()}, since {since}, in {Path.cwd()}: {shown}"


def waits(stream: IO[str]) -> None:
    """Say who holds the lock, then wait for it."""
    stream.seek(0)
    holder = stream.read().strip() or "its holder wrote no line yet"
    sys.stderr.write(
        f"lem: another serial test holds the lock ({holder}); this one waits\n"
    )
    sys.stderr.flush()
    fcntl.flock(stream, fcntl.LOCK_EX)


def named(stream: IO[str], line: str) -> None:
    """Write the holder's line, or empty it."""
    stream.seek(0)
    stream.truncate()
    stream.write(line)
    stream.flush()


def ran(folder: Path, words: Sequence[str]) -> int:
    """Run the command under the lock of the repository `folder` is in, and give its exit."""
    command = words_of(words)
    state = places.workspace(folder).state
    guard.writable(state)
    shown = " ".join(command)
    with holding(places.locks_folder(state) / LOCK, shown):
        code = checks_group.exited(command)
    return code if code >= 0 else checks_group.SIGNALLED - code
