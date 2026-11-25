"""Reconcile Inbox replies with the live replacement session."""

from functools import partial
from typing import TYPE_CHECKING

import msgspec

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.addons.inbox.delivery import Delivery
    from lem.addons.inbox.messages import Message, Read
    from lem.addons.inbox.records import Entry

type ReplyIds = tuple[str, ...]
type InboxAct = Callable[[Entry], None]
type InboxProblem = Callable[[str], None]


def replies(delivery: Delivery, live: dict[str, str]) -> None:
    """A reply to an older session can wake the live replacement once."""
    for entry in delivery.saved.entries:
        current = live.get(entry.wait.task)
        if (
            entry.sent
            and entry.wait.session
            and current
            and current != entry.wait.session
        ):
            attempt(delivery.problem, partial(reply, delivery), entry)


def reply(delivery: Delivery, entry: Entry) -> None:
    """Keep the ids of replies the live session already heard about."""
    if entry.sent is None:
        return
    message = entry.sent.message_id
    found = delivery.service.read(message)
    fresh = replies_after(found, message, entry.woke)
    if fresh and delivery.wake(entry.wait.task):
        delivery.update(
            entry, msgspec.structs.replace(entry, woke=(*entry.woke, *fresh))
        )


def attempt(report: InboxProblem, act: InboxAct, entry: Entry) -> None:
    """A failed effect leaves its saved entry in place."""
    try:
        act(entry)
    except Refusal as error:
        report(error.why)


def replies_after(found: Read, message: str, woke: ReplyIds) -> ReplyIds:
    """Read only the owner's messages after the question that was sent."""
    messages = found.thread.messages
    ids = tuple(entry.id for entry in messages)
    if message not in ids:
        return ()
    begin = ids.index(message) + 1
    following = messages[begin:]
    return tuple(entry.id for entry in following if is_new(entry, woke))


def is_new(entry: Message, woke: tuple[str, ...]) -> bool:
    """One owner reply the workspace did not send to the new session yet."""
    return entry.author.kind == "person" and entry.id not in woke
