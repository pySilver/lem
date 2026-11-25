"""The message and receipt shapes of the owner's Plannotator Inbox."""

from lem.records.base import Frozen


class Door(Frozen, frozen=True, kw_only=True):
    """What the local Inbox reports about its two addresses."""

    running: bool = False
    url: str | None = None
    tailnet_url: str | None = None
    why: str | None = None
    said: str = ""


class Payload(Frozen, frozen=True, kw_only=True):
    """One message in a task's own thread, or a withdrawal of its question."""

    body: str
    idempotency_key: str
    project_path: str | None = None
    thread: str | None = None
    subject: str | None = None
    attachments: tuple[str, ...] = ()
    reply_to: str | None = None
    supersedes: tuple[str, ...] = ()


class Sent(Frozen, frozen=True, kw_only=True):
    """A message the Inbox received, with its thread link."""

    message_id: str
    thread_id: str | None = None
    url: str | None = None


class Author(Frozen, frozen=True, kw_only=True):
    """Who sent a message in one thread."""

    kind: str = ""


class Message(Frozen, frozen=True, kw_only=True):
    """A message's id and author, for a wake-up after a reply."""

    id: str
    author: Author


class Thread(Frozen, frozen=True, kw_only=True):
    """The thread, in order."""

    messages: tuple[Message, ...]


class Read(Frozen, frozen=True, kw_only=True):
    """The response to a read of a single thread."""

    thread: Thread
