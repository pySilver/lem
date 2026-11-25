"""What `lem proposals list` gives: each proposal with its name, kind, day, fields and record,
its verdict and drop where it has them, and the newest run of each kind."""

import msgspec

from lem.addons.proposals.record import Kind
from lem.records.base import Day, Frozen, Moment


class Listed(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """One proposal: its name, kind and day, its fields, and its record."""

    name: str
    kind: Kind
    date: Day
    number: int
    area: str
    move: str
    body: str
    source: str
    where: str
    path: str = msgspec.field(name="file")


class RefutedOne(Listed, frozen=True, kw_only=True, omit_defaults=False):
    """A refuted proposal: the reviewer's reason and day."""

    reason: str
    day: Day


class PassedOne(Listed, frozen=True, kw_only=True, omit_defaults=False):
    """A passed proposal: its item, the day, and whether the item is still there."""

    item_path: str = msgspec.field(name="item")
    day: Day
    there: bool


class DroppedOne(Listed, frozen=True, kw_only=True, omit_defaults=False):
    """A proposal whose item the owner dropped: what the record says, the day, the item."""

    said: str
    day: Day
    item_path: str = msgspec.field(name="item")


class Newest(Frozen, frozen=True, kw_only=True):
    """The newest run of a kind: its day, moment and what it read."""

    date: Day
    at: Moment
    read: str


class Read(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """Every proposal by its verdict (a `RefutedOne`, `PassedOne` or `DroppedOne` in its
    list), and the newest run of each kind (null with none)."""

    undecided: tuple[Listed, ...]
    refuted: tuple[Listed, ...]
    passed: tuple[Listed, ...]
    dropped: tuple[Listed, ...]
    newest: dict[Kind, Newest | None]
