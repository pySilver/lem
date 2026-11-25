"""The typed response to the GitHub pull request queue query."""

from datetime import datetime

import msgspec

from lem.adapters.forge_gh_shell import Oid

CAMEL = "camel"


class Entry(msgspec.Struct, frozen=True, rename=CAMEL):
    """The pull request's active queue entry."""

    head_commit: Oid | None


class Event(msgspec.Struct, frozen=True, rename=CAMEL):
    """The most recent addition or removal on the pull request's timeline."""

    typename: str = msgspec.field(name="__typename")
    created_at: datetime | None = None
    reason: str | None = None
    before_commit: Oid | None = None


class Timeline(msgspec.Struct, frozen=True):
    """The latest queue event, if GitHub shows one."""

    nodes: tuple[Event | None, ...]


class QueueView(msgspec.Struct, frozen=True, rename=CAMEL):
    """The queue state and event, read together to recognize a later requeue."""

    merge_queue_entry: Entry | None
    timeline_items: Timeline


class Repository(msgspec.Struct, frozen=True, rename=CAMEL):
    """The pull request in the configured repository."""

    pull_request: QueueView | None


class Response(msgspec.Struct, frozen=True):
    """The GraphQL response to the queue query."""

    response: dict[str, Repository | None] = msgspec.field(name="data")
