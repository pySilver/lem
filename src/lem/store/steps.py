"""The step lock of a task, `tasks/SLUG/step.lock` (`landing.md` G): it covers a whole landing
step, its effects included, and a drop's write.

The file names its holder (step, pid, since) while it is held, and is empty after; a looker reads
the name and never takes the lock. A second step is refused at once with the holder's name; a
drop waits. The lock is the open file's, so it ends with its process, and no process the step
starts holds it (`seam:step-lock-not-inherited`).
"""

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING

import msgspec

from lem.kernel import clock, locks
from lem.kernel.errors import Refusal
from lem.records.base import Frozen, Moment
from lem.store import places

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


def holder_of(path: Path) -> Holder | None:
    """The holder the lock file names, or None when it names none."""
    try:
        return msgspec.json.decode(path.read_bytes(), type=Holder)
    except FileNotFoundError, msgspec.DecodeError:
        return None


def refusal(slug: str, step: str, holder: Holder | None) -> Refusal:
    """The refusal of `step` while another holds the lock."""
    if holder is None:
        why = f"another step of {slug} holds its lock"
    else:
        since = clock.minute(holder.since)
        why = (
            f"lem land {holder.step} {slug} (since {since}, process {holder.pid}) runs"
        )
    return Refusal(
        "step-held", why, f"wait for it to end, then run lem land {step} {slug}"
    )


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


@contextmanager
def step(state: Path, slug: str, name: str, now: Moment) -> Iterator[None]:
    """Hold the step lock of `slug` for the step `name`; refused at once while another holds
    it."""
    path = places.task_folder(state, slug) / LOCK
    with locks.tried(path) as stream:
        if stream is None:
            raise refusal(slug, name, holder_of(path))
        with named(stream, Holder(step=name, pid=os.getpid(), since=now)):
            yield


@contextmanager
def waited(state: Path, slug: str, name: str, now: Moment) -> Iterator[None]:
    """Hold the step lock of `slug` for `name`, waiting for the step that holds it: a drop's
    write, after it stopped the running checks."""
    path = places.task_folder(state, slug) / LOCK
    with (
        locks.held(path) as stream,
        named(stream, Holder(step=name, pid=os.getpid(), since=now)),
    ):
        yield
