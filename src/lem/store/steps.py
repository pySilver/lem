"""The step lock of a task, `tasks/SLUG/step.lock` (`landing.md` G): it covers a whole landing
step, its effects included, and a drop's write.

The file names its holder (step, pid, since) while it is held, and is empty after; a looker reads
the name and never takes the lock. A second step is refused at once with the holder's name; a
drop waits. The lock is the open file's, so it ends with its process, and no process the step
starts holds it (`seam:step-lock-not-inherited`).
"""

import fcntl
import os
from contextlib import contextmanager
from typing import TYPE_CHECKING

import msgspec

from lem.kernel import locks
from lem.records.base import Frozen, Moment
from lem.store import guard, places, step_refusals

if TYPE_CHECKING:
    from collections.abc import Iterator
    from io import TextIOWrapper
    from pathlib import Path

LOCK = "step.lock"


class Holder(Frozen, frozen=True, kw_only=True):
    """Who holds a task's step lock: the step, its process, and since when."""

    step: str
    pid: int
    since: Moment


def alive(pid: int) -> bool:
    """Whether the process `pid` is there (another user's counts)."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def holder_of(path: Path) -> Holder | None:
    """The holder the lock file names, while its process lives; None when it names none, or a
    process that is gone (`land.running_checks` on `main`): the lock of a dead holder is free."""
    try:
        holder = msgspec.json.decode(path.read_bytes(), type=Holder)
    except OSError, msgspec.DecodeError:
        return None
    return holder if alive(holder.pid) else None


@contextmanager
def named(stream: TextIOWrapper, holder: Holder) -> Iterator[None]:
    """Write `holder` into the held lock file, and empty it when the step ends."""
    stream.truncate(0)
    stream.write(msgspec.json.encode(holder).decode())
    stream.flush()
    try:
        yield
    finally:
        stream.truncate(0)
        stream.flush()


def opened(path: Path, slug: str, step: str) -> TextIOWrapper:
    """The step lock's file, opened; a file that cannot be is refused with its repair."""
    try:
        return path.open("a+", encoding="utf-8")
    except OSError as error:
        raise step_refusals.unopened(path, slug, step, error) from error


@contextmanager
def step(state: Path, slug: str, name: str, now: Moment) -> Iterator[None]:
    """Hold the step lock of `slug` for the step `name`; refused at once while another holds
    it."""
    path = places.task_folder(state, slug) / LOCK
    guard.writable(state)
    with opened(path, slug, name) as stream:
        if not locks.taken(stream):
            raise step_refusals.refusal(slug, name, holder_of(path))
        with named(stream, Holder(step=name, pid=os.getpid(), since=now)):
            yield


@contextmanager
def waited(state: Path, slug: str, name: str, now: Moment) -> Iterator[None]:
    """Hold the step lock of `slug` for `name`, waiting for the step that holds it: a drop's
    write, after it stopped the running checks."""
    path = places.task_folder(state, slug) / LOCK
    guard.writable(state)
    with opened(path, slug, name) as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        with named(stream, Holder(step=name, pid=os.getpid(), since=now)):
            yield
