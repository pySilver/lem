"""What the board server keeps of each workspace between two ticks of its duties, in memory
only: the files hold the truth, and a server that starts again starts with none of this.

For each workspace: when it last looked at the forge and pruned, each bookkeeping of a pull
request the forge ended that ran, each duty that failed with when (it waits RETRY before its next
try), the merges this server runs, the line of each merge's end, the problems its board
shows (`serve.Workspace.forge`, `failed`, `pruned` and `session_problem` on `main`), and when
the traceback of each fault of a duty last went to the server's log. Beside them, the problem of
each loop of the server's life whose last step failed, which every board shows.
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
# How often a failure that comes again writes its traceback to the server's log, in seconds. A
# guess: one fault that never ends writes 24 tracebacks a day, whatever its words.
TRACE_EVERY = 3600.0

type Key = tuple[str, ...]


@dataclass
class Traces:
    """When the traceback of each failure last went to the server's log, and how many
    failures of it came since with none."""

    at: dict[str, float] = field(default_factory=dict)
    since: dict[str, int] = field(default_factory=dict)

    def due(self, key: str, now: float) -> int | None:
        """How many failures of `key` came since its last traceback, when one is due at the
        moment `now` (monotonic seconds); else None, and this failure is counted."""
        last = self.at.get(key)
        if last is not None and now - last < TRACE_EVERY:
            self.since[key] = self.since.get(key, 0) + 1
            return None
        self.at[key] = now
        return self.since.pop(key, 0)


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
    traces: Traces = field(default_factory=Traces)

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
    loops: dict[str, str] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def of(self, checkout: Path) -> Kept:
        """What the server keeps of the workspace of `checkout`, made at its first tick."""
        with self.lock:
            return self.kept.setdefault(checkout, Kept())

    def problems_of(self, checkout: Path) -> tuple[str, ...]:
        """The problems the workspace's board shows now: a loop of the server whose last step
        failed, which every board shows, and a look or a duty of the workspace that failed."""
        with self.lock:
            loops = tuple(self.loops.values())
        return (*loops, *self.of(checkout).problems.values())

    def looped(self, name: str, problem: str | None) -> None:
        """Keep the problem of the loop `name` of the server, or forget it."""
        with self.lock:
            if problem is None:
                self.loops.pop(name, None)
            else:
                self.loops[name] = problem

    def loop_problem(self, name: str) -> str | None:
        """The problem of the loop `name`, while its last step failed."""
        with self.lock:
            return self.loops.get(name)


MEMORY = Memory()
