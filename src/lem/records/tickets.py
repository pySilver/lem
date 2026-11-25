"""A task's ticket in the tracker, and the steps Lem took on it.

A ticket stays claimed by a landed task for good, and by a dropped or answered task while it
owes the ticket a step (`project.released`, `holder_refusal` on `main`): the steps owed are the
end's steps less those on record.
"""

from typing import Literal

from lem.records.base import Frozen, Moment

type Tracker = Literal["github", "linear"]
# `assigned` is written before the act, `unassigned` only after an `assigned`. `ticked` is in the
# form before release 1.0, after which a new word would take two releases; no step writes it yet.
type TicketAct = Literal[
    "started",
    "assigned",
    "unassigned",
    "commented",
    "ticked",
    "landed",
    "dropped",
    "answered",
]


class TicketStep(Frozen, frozen=True, kw_only=True):
    """One step on the ticket, written once; `login` names whom `assigned` gave it to."""

    act: TicketAct
    at: Moment
    login: str | None = None
    url: str | None = None


class Ticket(Frozen, frozen=True, kw_only=True):
    """`MBZ-12` or `#42`; `repo` (`OWNER/REPO`) for a GitHub issue, and the steps taken."""

    tracker: Tracker
    id: str
    repo: str | None = None
    steps: tuple[TicketStep, ...] = ()
