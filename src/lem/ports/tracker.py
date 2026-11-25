"""The `Tracker` port: the ticket a task came from, and the steps Lem takes on it (the design's
part 4). GitHub Issues goes through `gh`; Linear through the agent's own tools, which
`task ticket` records."""

from typing import Literal, Protocol

from lem.records.base import Frozen

type TrackerStep = Literal["start", "land", "drop", "answer"]


class TicketView(Frozen, frozen=True, kw_only=True):
    """A ticket as the tracker shows it: id, title, body, state, address, assignees."""

    id: str
    title: str
    body: str
    state: str
    url: str
    assignees: tuple[str, ...] = ()


class Receipt(Frozen, frozen=True, kw_only=True):
    """What a step did on the ticket: the step, what changed, what it wrote, and the address."""

    ticket: str
    step: TrackerStep
    did: tuple[str, ...] = ()
    wrote: str | None = None
    url: str | None = None


class Tracker(Protocol):
    """Read a ticket, and take a step on it."""

    def read(self, ticket: str) -> TicketView: ...
    def step(self, ticket: str, step: TrackerStep, text: str) -> Receipt: ...
