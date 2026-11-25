"""What `lem corrections list` gives: whether the machine collects, the failures, and each
unreviewed group."""

import msgspec

from lem.addons.corrections import queue
from lem.records.base import Frozen


class Failures(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The errors of the log, each a message nobody judged, and the newest."""

    count: int
    newest: queue.LogLine | None


class Group(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """One group: its id, entries, sessions and days, Jev's highest probability, and the
    owner's words and the agent's before them, cut short."""

    gid: str = msgspec.field(name="id")
    entries: int
    sessions: int
    days: tuple[str, ...]
    p_lesson_max: float | None
    owner: str
    answered: str


class Listing(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """Whether the machine collects, the failures, the count of entries, and the groups."""

    collect: bool
    failures: Failures
    entries: int
    groups: tuple[Group, ...]
