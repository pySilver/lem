"""The serve lock, `serve.lock` in Lem's home folder: it spaces two starts or stops of the
board server at one moment. A command takes it only once it decided to act."""

import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

from lem.board import halt, start
from lem.kernel import locks
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

LOCK = "serve.lock"
# The most a call waits for another start: its stop and its start.
LOCK_WAIT = halt.STOP_WAIT + start.START_WAIT


@contextmanager
def serve_lock(home: Path) -> Iterator[None]:
    """Hold the serve lock, waiting at most LOCK_WAIT for another start."""
    home.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + LOCK_WAIT
    path = home / LOCK
    with path.open("a+", encoding="utf-8") as stream:
        while not locks.taken(stream):
            if time.monotonic() > deadline:
                raise Refusal(
                    "serve-lock",
                    f"another start of the board server holds {path} for over "
                    f"{LOCK_WAIT:g} s",
                    "wait a moment, then run this again",
                )
            time.sleep(start.POLL)
        yield
