"""The board server's record of what it sent to the owner's Inbox while he is away,
`.lem/state/inbox.json` (`board_model.inbox_look` on `main`): whether the Inbox runs, its
addresses, why it does not, and each question it holds.

The Inbox add-on writes the file; a view reads it to say where a question went. A file that
does not read is no record, and the page says nothing of the Inbox.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path

INBOX = "inbox.json"


class Sent(Frozen, frozen=True, kw_only=True):
    """A question the server put in the Inbox: its key (the row's), its task and kind, and
    the thread it is in."""

    key: str
    task: str
    kind: str
    asks: bool = False
    session: str | None = None
    tip: str | None = None
    thread_id: str | None = None
    thread_url: str | None = None


class Inbox(Frozen, frozen=True, kw_only=True):
    """The record: whether the Inbox runs, its address on this Mac and on the tailnet, why it
    does not run, and what it holds."""

    running: bool = False
    url: str | None = None
    tailnet_url: str | None = None
    why: str | None = None
    problem: str | None = None
    sent: tuple[Sent, ...] = ()


class Receipt(Frozen, frozen=True, kw_only=True):
    """The thread reported when the Inbox received the message."""

    thread_id: str | None = None
    url: str | None = None


class Delivery(Frozen, frozen=True, kw_only=True):
    """A pending or sent message for a wait."""

    wait: Sent
    sent: Receipt | None = None

    def shown(self) -> Sent:
        if self.sent is None:
            return self.wait
        return msgspec.structs.replace(
            self.wait, thread_id=self.sent.thread_id, thread_url=self.sent.url
        )


class Saved(Inbox, frozen=True, kw_only=True):
    """The add-on's door and deliveries, or the flat view saved in a board fixture."""

    door: Inbox | None = None
    entries: tuple[Delivery, ...] = ()

    def shown(self) -> Inbox:
        if self.door is None:
            return self
        sent = tuple(entry.shown() for entry in self.entries)
        return msgspec.structs.replace(self.door, problem=self.problem, sent=sent)


def read(state: Path) -> Inbox | None:
    """The record of the state folder `state`, or None when there is none or it does not
    read."""
    try:
        body = (state / INBOX).read_bytes()
    except OSError:
        return None
    try:
        return msgspec.json.decode(body, type=Saved).shown()
    except msgspec.DecodeError:
        return None
