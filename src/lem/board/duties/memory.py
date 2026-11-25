"""What the board server keeps of each workspace between two ticks of its duties, in memory
only: the files hold the truth, and a server that starts again starts with none of this.

For each workspace: when it last looked at the forge and pruned, each bookkeeping of a pull
request the forge ended that ran, each duty that failed with when (it waits RETRY before its next
try), the merges this server runs, the line of each merge's end, and the problems its board
shows (`serve.Workspace.forge`, `failed`, `pruned` and `session_problem` on `main`).
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.owner.forge import Look

# How long a duty that failed waits before its next try. A guess (2026-11-21): long beside a
# tick, so a missing agterm does not run a command every tick, and short beside the owner's day;
# the board's "no session" row tells him meanwhile.
RETRY_SECONDS = 300
RETRY = timedelta(seconds=RETRY_SECONDS)

type Key = tuple[str, ...]


@dataclass(kw_only=True)
class Kept:
    """What the server keeps of one workspace between ticks."""

    looked: datetime | None = None
    look: Look | None = None
    pruned: datetime | None = None
    done: set[Key] = field(default_factory=set)
    failed: dict[Key, datetime] = field(default_factory=dict)
    merging: dict[str, threading.Thread] = field(default_factory=dict)
    owner_tips: dict[str, str] = field(default_factory=dict)
    said: dict[str, str] = field(default_factory=dict)
    problems: dict[str, str] = field(default_factory=dict)

    merge_lock: threading.Lock = field(default_factory=threading.Lock)

    def start_merge(
        self, slug: str, thread: threading.Thread, *, owner_tip: str | None = None
    ) -> bool:
        """Start one merge per task, whether a duty or the owner asked for it."""
        with self.merge_lock:
            current = self.merging.get(slug)
            if current is not None and current.is_alive():
                return False
            thread.start()
            self.merging[slug] = thread
            if owner_tip is None:
                self.owner_tips.pop(slug, None)
            else:
                self.owner_tips[slug] = owner_tip
            return True

    def approvals(self) -> dict[str, str]:
        """The tips the owner approved in this server's live workers."""
        with self.merge_lock:
            return {
                slug: tip
                for slug, tip in self.owner_tips.items()
                if self.merging[slug].is_alive()
            }

    def due(self, key: Key, now: datetime) -> bool:
        """Whether the duty `key` may run now: it never failed, or RETRY has passed since."""
        failed = self.failed.get(key)
        return failed is None or now - failed >= RETRY

    def owed(self, key: Key, now: datetime) -> bool:
        """Whether the duty `key`, done once for good, is still to do, and may run now."""
        return key not in self.done and self.due(key, now)

    def ended(self, key: Key, now: datetime, *, ran: bool) -> None:
        """Keep how the duty `key` ended: a failure waits RETRY, a run forgets it."""
        if ran:
            self.failed.pop(key, None)
        else:
            self.failed[key] = now

    def running(self) -> frozenset[str]:
        """The tasks whose merge this server runs now."""
        with self.merge_lock:
            return frozenset(
                slug for slug, run in self.merging.items() if run.is_alive()
            )


@dataclass
class Memory:
    """The server's memory of every workspace, by its main checkout."""

    kept: dict[Path, Kept] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def of(self, checkout: Path) -> Kept:
        """What the server keeps of the workspace of `checkout`, made at its first tick."""
        with self.lock:
            return self.kept.setdefault(checkout, Kept())

    def problems_of(self, checkout: Path) -> tuple[str, ...]:
        """The problems the workspace's board shows now: a look or a duty that failed."""
        return tuple(self.of(checkout).problems.values())


MEMORY = Memory()
