"""What `lem waiting` prints: the owner's presence first, then each group of what waits for him,
the board's rows and its stacks, what the list knows of the sessions and the forge, last night's
report, the parked tasks, and the count of tasks that wait (`project.cmd_waiting` on `main`)."""

import msgspec

from lem.app.owner.entries import Entry, Keyed, Stacked
from lem.model.decisions.pending import Waits
from lem.records.base import Day, Frozen, Moment


class OwnerNow(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """Whether he said he is away, since when and in which words, and the number of changes
    in the machine's mark, from which a watch of it starts."""

    away: bool
    since: Moment | None
    words: str | None
    seen: int


class Known(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """Whether the task sessions are known, and why not."""

    known: bool
    said: str | None


class ForgeSeen(Frozen, frozen=True, kw_only=True):
    """When the board's server last looked at the forge, or why its look could not be read."""

    looked: Moment | None
    said: str | None = None


class NightReport(Frozen, frozen=True, kw_only=True):
    """The report of the last night: its day and its file."""

    date: Day
    path: str = msgspec.field(name="file")


class Waiting(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """Everything that waits for the owner, in its groups, and the board's rows and stacks."""

    owner: OwnerNow
    breakers: tuple[Waits, ...]
    no_session: tuple[Entry, ...]
    stopped: tuple[Entry, ...]
    criteria: tuple[Entry, ...]
    held: tuple[Entry, ...]
    cards: tuple[Entry, ...]
    after_dropped: tuple[Entry, ...]
    blocked: tuple[Entry, ...]
    plans: tuple[Entry, ...]
    reviews: tuple[Entry, ...]
    pull_requests: tuple[Entry, ...]
    rows: tuple[Keyed, ...]
    tasks: tuple[Stacked, ...]
    sessions: Known
    forge: ForgeSeen
    night_report: NightReport | None
    parked: tuple[Entry, ...]
    count: int
