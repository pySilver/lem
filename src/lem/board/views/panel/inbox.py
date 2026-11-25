"""What a task's page says of the owner's Inbox (`board_model.inbox_of` on `main`): only while
his mark says away, the task has a row of what waits for him, and the server's record says
something of it. Then the address of the task's thread at the Inbox's tailnet address, whether a
question went there (he answers in either place) or only a note no session can take a reply to,
or why there is no link. The merge review and the merge of a task are its merge's one thing."""

import re
from typing import TYPE_CHECKING, NamedTuple
from urllib.parse import quote

from lem.board.views.panel import inbox_words
from lem.board.views.panel.inbox_sent import sent_of

if TYPE_CHECKING:
    from lem.board.views.inbox_read import Inbox, Sent
    from lem.board.views.world import World
    from lem.model.owner.looks import Rows

ADDRESS = re.compile(r"https?://[^\s/#?]+")
SLASHED = re.compile(r"https?://[^/]+/")
# The rows whose thing the Inbox holds as a note no session can take a reply to.
GONE = frozenset(("session", "stopped", "after_dropped"))


class Said(NamedTuple):
    """The task's thread in the Inbox, whether a question went there, whether only a note
    went, or why there is no link."""

    thread: str | None = None
    asks: bool = False
    gone: bool = False
    why: str | None = None


def inbox_of(world: World, slug: str, rows: Rows) -> Said | None:
    """What the page of task `slug` says of the Inbox, with its rows of what waits for the
    owner; None while it changes nothing of today's lines."""
    record = world.inbox
    if not world.presence.away or not rows or record is None:
        return None
    sent = sent_of(record, slug, rows)
    if not record.running or record.tailnet_url is None:
        return closed(record, there=any(one.thread_id for one in sent))
    return opened(record, record.tailnet_url, sent)


def opened(record: Inbox, tailnet: str, sent: list[Sent]) -> Said | None:
    """What the page says while the phone can reach the Inbox: the thread, or that the
    server could not send the task's thing yet."""
    there = [one for one in sent if one.thread_id]
    link = thread_link(tailnet, there[0].thread_id) if there else None
    if link is None:
        unsent = record.problem and any(not one.thread_id for one in sent)
        return Said(why=inbox_words.UNSENT) if unsent else None
    asks = any(one.asks for one in there)
    gone = not asks and any(one.kind in GONE for one in there)
    return Said(thread=link, asks=asks, gone=gone)


def closed(record: Inbox, *, there: bool) -> Said | None:
    """Why the phone cannot reach the Inbox, or None when the record says no why."""
    why = record.why
    if not why:
        return None
    said = (inbox_words.WHY_SENT if there else inbox_words.WHY).get(why)
    if said is not None:
        return Said(why=said)
    went = (
        "A message of this task went to the Inbox, and"
        if there
        else "No question went to the Inbox:"
    )
    flat = " ".join(why.split())
    return Said(why=f"{went} its last look said “{flat}”.")


def thread_link(tailnet: str, thread: str | None) -> str | None:
    """The address of a thread through the Inbox's tailnet address, `TAILNET#thread=ID`;
    None unless the address is http or https."""
    if not ADDRESS.match(tailnet) or not thread:
        return None
    base = tailnet.split("#", 1)[0]
    if not SLASHED.match(base):
        base = f"{base}/"
    return f"{base}#thread={quote(thread, safe='')}"
