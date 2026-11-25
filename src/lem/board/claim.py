"""One foreground server's claim on Lem's home folder, held for its lifetime."""

from contextlib import contextmanager
from typing import TYPE_CHECKING

from lem.kernel import locks
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

LOCK = "serve-run.lock"


@contextmanager
def held(home: Path) -> Iterator[None]:
    """Take the home's claim before checking vacancy or binding a socket."""
    with locks.tried(home / LOCK) as stream:
        if stream is None:
            raise Refusal(
                "running",
                "the board server of this home folder runs or is at its start",
                "wait for it to start, then lem serve stop ends it",
            )
        yield


def released(home: Path) -> bool:
    """Whether the claim is free, with no file made for a server without one."""
    try:
        with (home / LOCK).open(encoding="utf-8") as stream:
            return locks.taken(stream)
    except FileNotFoundError:
        return True
