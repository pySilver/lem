"""The load gate before the first command of the checks (`land.wait_for_load` and `gate_look`
on `main`).

A run waits until it is first in the machine's one line of the runs that wait
(`model/landing/checks_line.py`), the machine's load average is under this machine's start
number, and a minute passed since the last start under the gate, of any repository. It is in
the line from its first look to its start, by its own locked file (`checks_queue.py`), and
leaves it in a `finally` when its wait ends in any other way. The number is read again at each
look, so that a run that waits takes the developer's new number, or starts at once when he took
the gate away. Each change of why it waits, and each five minutes of the same, is told
(`checks_waits.py`).
"""

import contextlib
import dataclasses
import os
from typing import TYPE_CHECKING

from lem.app.landing import checks_machine, checks_queue, checks_waits, checks_wanted
from lem.kernel import folders, locks
from lem.model.landing import checks_line, checks_said

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from lem.store import places

# How often a run that waits looks again, and after how long the same wait is told again, in
# seconds (`LOAD_LOOK` and `LOAD_SAY` on `main`).
LOOK = 15.0
SAY = 300.0
LINE = "load.line"
LOCK = "load.lock"


@dataclasses.dataclass(kw_only=True, slots=True)
class Gate:
    """One run's wait at the gate: the task, its workspace, the machine's gauges, its place in
    the line while it waits, and the last wait it told with its moment."""

    slug: str
    workspace: places.Workspace
    gauges: checks_machine.Gauges = dataclasses.field(
        default_factory=checks_machine.Gauges
    )
    own: checks_queue.Own | None = None
    said: tuple[object, float] | None = None

    def passed(self) -> bool:
        """Wait until the run may start; whether it waited."""
        home = folders.home_for_writing(os.environ)
        with self.placed():
            while True:
                start = checks_machine.start_number(home)
                if start is None or self.looked(home, start).go:
                    return self.said is not None

    @contextlib.contextmanager
    def placed(self) -> Generator[None]:
        """The run leaves the line however its wait ends."""
        try:
            yield
        finally:
            self.left()

    def left(self) -> None:
        """The run leaves the line, when it is in it."""
        if self.own is not None:
            checks_queue.leave(self.own)
            self.own = None

    def looked(self, home: Path, start: float) -> checks_line.Look:
        """One look under the hold of `load.lock`; a wait is told, and paused."""
        levels = (self.gauges.load(), start)
        with locks.held(home / LOCK) as stream:
            own = self.joined(home)
            now = self.gauges.clock()
            found = checks_wanted.seen(stream, home / LINE, own, levels, now)
            if found.look.go:
                self.left()
        if not found.look.go:
            self.tell(waiting(found, levels), found.position)
            self.gauges.sleep(pause(found.look))
        return found.look

    def joined(self, home: Path) -> checks_queue.Own:
        """The run's place in the line, taken at its first look."""
        if self.own is None:
            entry = checks_line.Entry(
                task=self.slug,
                repo=str(self.workspace.checkout),
                since=self.gauges.clock(),
            )
            self.own = checks_queue.joined(home / LINE, entry, os.getpid())
        return self.own

    def fresh(self, key: tuple[object, ...], now: float) -> bool:
        """Whether the wait `key` is the one told last, less than SAY seconds ago."""
        said = self.said
        if said is None or said[0] != key:
            return False
        return now - said[1] < SAY

    def tell(self, wait: checks_said.Wait, position: int) -> None:
        """A new wait in the journal and `checks-wait.json` when its reason or the first in
        the line changed, or after SAY seconds of the same."""
        now = self.gauges.clock()
        key = told_as(wait)
        if self.fresh(key, now):
            return
        self.said = (key, now)
        checks_waits.waited(self.workspace.state, self.slug, wait, position, now)


def told_as(wait: checks_said.Wait) -> tuple[object, ...]:
    """What makes a wait another one: why it waits, the first in the line and why."""
    return (wait.after is None, wait.behind, wait.behind_repo, wait.why, wait.unread)


def waiting(found: checks_wanted.Seen, levels: tuple[float, float]) -> checks_said.Wait:
    """Why a run waits, from its look."""
    load, start = levels
    look = found.look
    return checks_said.Wait(
        load=load,
        start=start,
        after=look.after,
        behind=look.behind,
        behind_repo=look.behind_repo,
        why=look.why,
        unread=found.unread,
    )


def pause(look: checks_line.Look) -> float:
    """The pause before the next look: LOOK, or less when the minute after the last start ends
    sooner, and at least one second."""
    if look.reason != "after" or look.gap is None:
        return LOOK
    return min(LOOK, max(1.0, checks_line.SPACING - look.gap))
