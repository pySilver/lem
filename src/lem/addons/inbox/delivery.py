"""Apply one Inbox look, preserving the payload before any call can send it."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import msgspec

from lem.addons.inbox import payload, rules, store
from lem.addons.inbox.effects import attempt, replies
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from lem.addons.inbox.client import Inbox
    from lem.addons.inbox.records import Entry, Look, Record, Wait
    from lem.records.base import Moment


@dataclass(slots=True, kw_only=True)
class Delivery:
    """One workspace's held record and its session and Inbox effects."""

    state: Path
    now: Moment
    service: Inbox
    wake: Callable[[str], bool]
    prepare: Callable[[Wait], Entry]
    saved: Record
    problems: list[str] = field(default_factory=list)

    def run(self, look: Look, live: dict[str, str]) -> Record:
        """Persist the outcome of each effect and continue after a refusal."""
        steps = rules.decide(look, self.saved.entries)
        self.problems.clear()
        self.save(msgspec.structs.replace(self.saved, door=look.door))
        for entry in steps.forget:
            self.update(entry, None)
        for entry in steps.retry:
            attempt(self.problem, self.send, entry)
        for entry in steps.withdraw:
            self.withdraw(entry, look)
        for wait in steps.send:
            self.new(wait)
        if look.door.running:
            replies(self, live)
        problem = "; ".join(self.problems) or None
        self.save(msgspec.structs.replace(self.saved, problem=problem))
        return self.saved

    def new(self, wait: Wait) -> None:
        """A failed withdrawal keeps its row and prevents a replacement send."""
        if any(entry.wait.key == wait.key for entry in self.saved.entries):
            return
        try:
            entry = self.prepare(wait)
        except Refusal as error:
            self.problem(error.why)
            return
        self.update(entry, entry)
        attempt(self.problem, self.send, entry)

    def send(self, entry: Entry) -> None:
        """On a receipt, keep the link and forget the retried payload."""
        if entry.payload is None:
            return
        sent = self.service.send(entry.payload, entry.wait.session)
        self.update(entry, msgspec.structs.replace(entry, payload=None, sent=sent))
        if entry.wait.session:
            self.wake(entry.wait.task)

    def withdraw(self, entry: Entry, look: Look) -> None:
        """An already answered question leaves the record without a new message."""
        replaced = rules.can_send(look) and any(
            wait.key == entry.wait.key for wait in look.waits
        )
        try:
            self.service.send(
                payload.withdrawal(entry, replaced=replaced), entry.wait.session
            )
        except Refusal as error:
            if entry.sent is None or not payload.answered(
                entry.sent.message_id, error.why
            ):
                self.problem(error.why)
                return
        self.update(entry, None)

    def problem(self, why: str) -> None:
        """The latest failure reaches the board and leaves the payload for retry."""
        self.problems.append(why)

    def update(self, old: Entry, new: Entry | None) -> None:
        """Replace the entry for one row and publish the record."""
        kept = tuple(
            entry for entry in self.saved.entries if entry.wait.key != old.wait.key
        )
        entries = kept if new is None else (*kept, new)
        after = msgspec.structs.replace(self.saved, entries=entries)
        self.save(after)

    def save(self, after: Record) -> None:
        """Keep the last form on disk, including its look time."""
        state, now = self.state, self.now
        self.saved = store.write(state, self.saved, after, now)
