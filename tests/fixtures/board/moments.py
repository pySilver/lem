"""The clock and the names of the showcase afternoon: the minute it is now, the minutes before
it that each step ran at, and the commits, named by a word.

Today's `tests/board-showcase.py` on `main` writes its afternoon at the minute it runs; this one
keeps that minute, so that every time the board shows of it is a value a test can hold.
"""

import hashlib
from datetime import UTC, datetime, timedelta

# The minute the afternoon is looked at, and the day of its night task.
NOW = datetime(2026, 11, 25, 16, 0, tzinfo=UTC)
TODAY = NOW.date()
# The machine and the workspace of the board's addresses.
HOST = "studio"
WORKSPACE = "shop"
BASE = f"/{HOST}/{WORKSPACE}"
FORGE = "https://github.com/acme/shop"


def ago(minutes: float) -> datetime:
    """The moment `minutes` before NOW, to the second."""
    return NOW - timedelta(seconds=round(minutes * 60))


def sha(word: str) -> str:
    """A full commit id made from `word`: the same word gives the same commit."""
    return hashlib.sha1(word.encode(), usedforsecurity=False).hexdigest()


def pull(number: int) -> str:
    """The address of pull request `number` on the shop's forge."""
    return f"{FORGE}/pull/{number}"
