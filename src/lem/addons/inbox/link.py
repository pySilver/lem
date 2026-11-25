"""The Inbox link or its absence reason for the task's board panel."""

from typing import TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

from lem.addons.inbox import store
from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path


class Link(Frozen, frozen=True, kw_only=True):
    """One thread the owner can open, or the reason it has no link."""

    url: str | None = None
    why: str | None = None


def shown(state: Path, task: str, *, away: bool) -> Link:
    """Show the current thread on the Inbox's tailnet address while away."""
    if not away:
        return Link()
    saved = store.read(state)
    if not saved.door.tailnet_url:
        return Link(why=saved.door.why or "The Inbox has no tailnet address.")
    for entry in reversed(saved.entries):
        if entry.wait.task == task and entry.sent and entry.sent.url:
            return Link(url=external(entry.sent.url, saved.door.tailnet_url))
    return Link(why=saved.problem or "The task has no Inbox thread.")


def external(thread: str, address: str) -> str:
    """Keep the thread's path at the Inbox door's origin."""
    target = urlsplit(thread)
    base = urlsplit(address)
    return urlunsplit(
        (base.scheme, base.netloc, target.path, target.query, target.fragment)
    )
