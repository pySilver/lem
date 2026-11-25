"""`lem owner watch`: wait for the owner's next word (`project.cmd_owner_watch` on `main`).

It reads the machine's mark once every few seconds and ends with his presence as soon as the mark
holds another number of changes than the one the caller saw (`owner.seen` of `lem waiting`): at
once when that is so at the start, so that no word is lost between the caller's read and this
start. The count is the cursor, never a time: an away and a back can share one second, and each
word adds a change. It writes nothing. A stop ends it with a refusal, which asks for no second
watch.
"""

import os
import signal
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

from lem.kernel import paths
from lem.kernel.errors import Refusal
from lem.records.base import Frozen, Moment
from lem.store import owner

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    type Sleep = Callable[[float], None]

# How many seconds the watch waits between two looks at the mark: a guess (2026-11-19 on
# `main`), not a measurement; an away typed in another repository reaches an interview within
# seconds, and one read of a small file every 5 seconds costs nothing.
EVERY = 5
STOPS = (signal.SIGTERM, signal.SIGINT)


class Seen(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """His presence when the watch ended, and the number of changes it saw."""

    away: bool
    since: Moment | None
    words: str | None
    seen: int


class StoppedError(Exception):
    """The watch was stopped by a signal."""


def watched(seen: int | None, every: int, sleep: Sleep = time.sleep) -> Seen:
    """Wait until the mark holds another number of changes than `seen`, then give his
    presence."""
    if seen is None or seen < 0:
        raise Refusal(
            "seen",
            f"--seen is the number of changes in the owner's mark, 0 or more, not {seen}",
            "lem waiting gives it as owner.seen; run lem owner watch --seen N with it",
        )
    if every < 1:
        raise Refusal("every", f"--every is 1 second or more, not {every}", "--every 5")
    home = paths.home(os.environ)
    presence = owner.read(home)
    with stoppable():
        while presence.seen == seen:
            sleep(every)
            presence = owner.read(home)
    return Seen(
        away=presence.away,
        since=presence.since,
        words=presence.words,
        seen=presence.seen,
    )


def stopped(*_: object) -> None:
    """A signal's handler: end the watch."""
    raise StoppedError


@contextmanager
def stoppable() -> Generator[None]:
    """Turn a stop by a signal into a refusal, and put the handlers back after."""
    before = [signal.signal(number, stopped) for number in STOPS]
    try:
        yield
    except StoppedError:
        raise Refusal(
            "stopped",
            "the watch of the owner's mark was stopped",
            "start no other watch until the reason for the stop is gone",
        ) from None
    finally:
        for number, kept in zip(STOPS, before, strict=True):
            signal.signal(number, kept)
