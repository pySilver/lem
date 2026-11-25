"""The guard of a stopped session, as a rule over the task's timeline: which step is due now
(`board_model.stop_due` on `main`).

The timeline holds the task's work (every entry of its journal but the owner's acts), and Lem's
acts on its sessions: the opens, the status wakes (each with whether the session's signs did not
read when it was sent), the stops, and the turns the guard saw after a status message it sent
while it could not read the signs (`worked`). Entries of one second keep the acts before the
work, so that work in the second of a wake or a stop counts as after it.

For a task the guard watches (building, ready or landing, with no hold) whose session lives with
an agent in its pane and runs no shell command, the newest sign of work is the newest of its
work, its newest open, the turn of its newest `worked`, and the session's own sign when its
signs read. Then: `worked` when the signs read and show a turn at or after a status wake the
unread clock sent; `status` QUIET_SECONDS after that sign with no status wake of its clock since;
`restart` ANSWER_SECONDS after that wake, with signs that read, once for a run of work; `stopped`
ANSWER_SECONDS after it, once. The owner's numbers, 2026-11-22: "lets try 45min" and "I agree
with 10min". `main` held the `worked` step back for one release (`WRITES_WORKED`); this release
reads no record of the one before, so it takes the step.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from lem.records.base import Frozen

type Kind = Literal["work", "open", "wake", "stopped", "worked"]
type Step = Literal["worked", "status", "restart", "stopped"]

STOPPED: Kind = "stopped"
WORK: Kind = "work"
OPEN: Kind = "open"
QUIET_SECONDS = 2700
ANSWER_SECONDS = 600
GUARDED = frozenset(("building", "ready", "landing"))


class Event(Frozen, frozen=True, kw_only=True):
    """One entry of the timeline: its kind and moment, an open's why, a wake's why and
    whether it was sent unread, and a `worked`'s turn."""

    kind: Kind
    at: datetime
    why: str | None = None
    unread: bool = False
    turn: datetime | None = None

    def status_wake(self) -> bool:
        """Whether this is a status message of the guard."""
        return self.kind == "wake" and self.why == "status"


class Facts(Frozen, frozen=True, kw_only=True):
    """What the guard reads of the task now: whether it watches it, whether its session lives
    with an agent in its pane, whether a shell command of it runs, whether its signs read, and
    its newest sign."""

    guarded: bool
    alive: bool
    shell: bool = False
    read: bool = False
    sign: datetime | None = None

    def working(self) -> bool:
        """Whether the guard reads the session: it lives with an agent and runs no shell."""
        return self.guarded and self.alive and not self.shell


class Due(Frozen, frozen=True, kw_only=True):
    """The step due, and the moment it is due from."""

    step: Step
    since: datetime


@dataclass(frozen=True, slots=True)
class Timeline:
    """The task's timeline, oldest first."""

    events: tuple[Event, ...]

    def places(self, kind: Kind) -> list[int]:
        """The places of the events of `kind`."""
        return [place for place, one in enumerate(self.events) if one.kind == kind]

    def has(self, kind: Kind, start: int, end: int | None = None) -> bool:
        """Whether an event of `kind` is between `start` and `end`."""
        kinds = (one.kind for one in self.events[start:end])
        return kind in kinds

    def wake_before(self, place: int) -> int:
        """The place of the newest status wake before `place`, or `place` with none."""
        wakes = [at for at in range(place) if self.events[at].status_wake()]
        return wakes[-1] if wakes else place

    def stop_stands(self) -> int | None:
        """The place of the task's newest stop while it stands: no work came after the status
        wake before it, and no open and no turn that answered that wake came after it."""
        stops = self.places(STOPPED)
        if not stops:
            return None
        last = stops[-1]
        wake = self.wake_before(last)
        if self.has(WORK, wake + 1) or self.answered(last, wake):
            return None
        return last

    def answered(self, place: int, wake: int) -> bool:
        """Whether an open, or a turn at or after the wake at `wake`, came after `place`."""
        asked = self.events[wake].at
        later = self.events[place + 1 :]
        turns = [one.turn for one in later if one.turn]
        opened = self.has(OPEN, place + 1)
        return opened or any(turn >= asked for turn in turns)

    def stood(self, place: int) -> bool:
        """Whether the event at `place` is a stop that stood: no work came between the status
        wake before it and it."""
        if self.events[place].kind != STOPPED:
            return False
        return not self.has(WORK, self.wake_before(place) + 1, place)

    def status_after(self, since: datetime) -> list[int]:
        """The places of the status wakes after `since`."""
        wakes = (place for place, one in enumerate(self.events) if one.status_wake())
        return [place for place in wakes if self.events[place].at > since]


def run_start(line: Timeline) -> int:
    """The place where the task's run of work since its newest work and its newest open
    begins."""
    works = line.places(WORK) or [-1]
    opens = line.places(OPEN) or [0]
    return max(works[-1] + 1, opens[-1])


def restarted(line: Timeline) -> bool:
    """Whether the guard opened a fresh session in a stopped one's place after the task's
    newest work."""
    works = line.places(WORK) or [-1]
    after = line.events[works[-1] + 1 :]
    opens = (one for one in after if one.kind == OPEN)
    return any(one.why == STOPPED for one in opens)
