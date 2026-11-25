"""A lock file, held with `flock` by one open file at a time.

The lock is the open file's: another open of the same file waits for it, in another process or
in a thread of this one, and the lock ends when the file is closed or its process ends. Python
opens a file that no child inherits, and `subprocess` closes the rest, so a process that a holder
starts never holds the lock (`seam:step-lock-not-inherited`).
"""

import fcntl
from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from io import TextIOWrapper
    from pathlib import Path


@contextmanager
def held(path: Path) -> Iterator[TextIOWrapper]:
    """Hold the lock of `path`, waiting for another holder; its folder must exist."""
    with path.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield stream


@contextmanager
def tried(path: Path) -> Iterator[TextIOWrapper | None]:
    """Hold the lock of `path` when nobody holds it, else give None at once: what a hook and a
    look take, which never wait."""
    with path.open("a+", encoding="utf-8") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield None
            return
        yield stream
