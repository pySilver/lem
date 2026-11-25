"""The board server's watcher of the board's notifications: every LOOK seconds it reads each
workspace's list of what waits for the owner, and when a list gained a row it sends one push to
each device that wants that workspace (`push.Watcher` on `main`).

The memory of each list is in `push.json` (`news.gained`), so a restart of the server neither
sends again what was sent nor misses what came while it was down. A send is never on a request's
path, and a failure is one line in the server's log and the `problem` of `GET /api/server`, never
a stop of the server.
"""

import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

import anyio
import msgspec

from lem.adapters import notify_push_devices as devices
from lem.board.push import said, waits

if TYPE_CHECKING:
    from pathlib import Path

    from lem.adapters.notify_push import PushNotifier

# How often the watcher looks, in seconds. A guess: a phone needs no fresher news
# (`push.LOOK_SECONDS` on `main`).
LOOK = 5.0


@dataclass
class Watcher:
    """The watcher of Lem's home folder `home`, its notifier, and what it last failed at."""

    home: Path
    host: str
    notifier: PushNotifier
    problem: str | None = None

    def look(self, now: float) -> int:
        """One look at every workspace: the memory kept, and one push of the news; how
        many devices it went to."""
        news = self.remembered(now)
        if not news:
            return 0
        named = tuple(dict.fromkeys(name for name, _, _ in news))
        push = said.said_of(self.host, news)
        return len(self.notifier.told(push, named))

    def remembered(self, now: float) -> list[waits.New]:
        """The new rows of every workspace, with each list's memory kept."""
        found = waits.every(self.home, self.host)
        with devices.changing(self.home) as held:
            seen = dict(held[-1].seen)
            news = waits.news_of(seen, found, now)
            held.append(msgspec.structs.replace(held[-1], seen=seen))
        return news

    def told(self, problem: str | None) -> None:
        """One line in the log for each new problem, none while it stays the same."""
        if problem is not None and problem != self.problem:
            sys.stderr.write(f"the board's notifications: {problem}\n")
        self.problem = problem

    async def loop(self, stopping: anyio.Event) -> None:
        """Look every LOOK seconds, off the event loop, until the server stops."""
        while not stopping.is_set():
            with anyio.move_on_after(LOOK):
                await stopping.wait()
            if stopping.is_set():
                return
            try:
                await anyio.to_thread.run_sync(self.look, self.notifier.now())
            except waits.FAILED as error:
                self.told(f"{type(error).__name__}: {error}")
            else:
                self.told(None)
