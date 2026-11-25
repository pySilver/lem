"""The ports to the outside a test holds: `FakeTracker`, `RecordingNotifier` and `FakeJudge`."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lem.ports.faults import Unanswered
from lem.ports.judge import Defect, NotAsked, Score
from lem.ports.tracker import Receipt, TicketView, TrackerStep

if TYPE_CHECKING:
    from lem.ports.notifier import Wait


@dataclass
class FakeTracker:
    """Tickets, and the steps taken on them. A step on a ticket that is not there, or after
    the end it already took, is the tracker's fault, as `gh` would give."""

    tickets: dict[str, TicketView] = field(default_factory=dict)
    steps: list[tuple[str, TrackerStep, str]] = field(default_factory=list)

    def read(self, ticket: str) -> TicketView:
        if ticket not in self.tickets:
            raise Unanswered("tracker", f"no ticket {ticket}")
        return self.tickets[ticket]

    def step(self, ticket: str, step: TrackerStep, text: str) -> Receipt:
        self.read(ticket)
        self.steps.append((ticket, step, text))
        done = "closed" if step in {"land", "drop", "answer"} else "assigned"
        return Receipt(ticket=ticket, step=step, did=(done,), wrote=text)


@dataclass
class RecordingNotifier:
    """The waits the owner was told of: a wait started again while it is open is no new
    notification, and an end of a wait that is not open says nothing."""

    started_waits: list[Wait] = field(default_factory=list)
    ended_waits: list[str] = field(default_factory=list)
    open: dict[str, Wait] = field(default_factory=dict)

    def started(self, wait: Wait) -> None:
        if wait.id in self.open:
            return
        self.open[wait.id] = wait
        self.started_waits.append(wait)

    def ended(self, wait_id: str) -> None:
        if self.open.pop(wait_id, None) is not None:
            self.ended_waits.append(wait_id)


@dataclass
class FakeJudge:
    """Jev's scores, set by the test; with no key, Jev is not asked."""

    over: dict[str, float] = field(default_factory=dict)
    same: dict[str, tuple[Score, ...]] = field(default_factory=dict)
    key: bool = True
    asked: list[Defect] = field(default_factory=list)

    def same_items(
        self, defect: Defect, paths: tuple[str, ...]
    ) -> tuple[Score, ...] | NotAsked:
        if not self.key:
            return NotAsked(why="no key for Jev")
        self.asked.append(defect)
        return tuple(
            score for score in self.same.get(defect.title, ()) if score.path in paths
        )

    def over_bar(self, defect: Defect) -> Score | NotAsked:
        if not self.key:
            return NotAsked(why="no key for Jev")
        self.asked.append(defect)
        return Score(score=self.over.get(defect.title, 0.0))
