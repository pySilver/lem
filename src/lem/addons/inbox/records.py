"""One workspace's record of its Inbox door, questions and notes."""

from enum import StrEnum

from lem.addons.inbox.messages import Door, Payload, Sent
from lem.model.owner.looks import Kind
from lem.records.base import Frozen, Moment


class Wait(Frozen, frozen=True, kw_only=True):
    """The identity of what waits and the facts that make it a new message."""

    key: str
    task: str
    kind: Kind
    since: Moment
    asks: bool = False
    session: str | None = None
    tip: str | None = None
    review_digest: str | None = None


class Entry(Frozen, frozen=True, kw_only=True):
    """A sent or pending note, with its stable idempotency key."""

    wait: Wait
    key: str
    payload: Payload | None = None
    sent: Sent | None = None
    woke: tuple[str, ...] = ()


class Record(Frozen, frozen=True, kw_only=True):
    """The board's last state of the Inbox."""

    door: Door = Door()
    entries: tuple[Entry, ...] = ()
    problem: str | None = None
    looked: Moment | None = None


class Look(Frozen, frozen=True, kw_only=True):
    """The stable facts for one look at a workspace."""

    away: bool
    door: Door
    waits: tuple[Wait, ...]
    behind: frozenset[str] = frozenset()
    held: frozenset[str] = frozenset()
    known: bool = True


class Act(StrEnum):
    """The next effect for one saved entry."""

    keep = "keep"
    forget = "forget"
    withdraw = "withdraw"
    retry = "retry"


class Actions(Frozen, frozen=True, kw_only=True):
    """The rules choose effects. Effects keep their own receipts."""

    forget: tuple[Entry, ...] = ()
    withdraw: tuple[Entry, ...] = ()
    retry: tuple[Entry, ...] = ()
    send: tuple[Wait, ...] = ()
