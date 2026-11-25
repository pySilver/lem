"""A day's record of the night's or the retro's proposals, `night/DAY.json` or
`retros/DAY.json` of the state folder (`project.cmd_proposals_add` on `main`).

One file a day for each kind of run: what each run read and the proposals it added, numbered
from 1 in the order they came; then the reviewer's verdicts, each proposal refuted with its
reason or passed into an item of its area; and the owner's drops of those items. Nothing of a
record is rewritten: a second run of the day adds after the first, and a verdict or a drop adds
an entry.
"""

from typing import Annotated, Literal

import msgspec

from lem.records.base import Day, Frozen, Moment

type Kind = Literal["night", "retro"]
# An area: lower-case words joined by hyphens, as `lessons` or `board`.
type Area = Annotated[str, msgspec.Meta(pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$")]


class Proposal(Frozen, frozen=True, kw_only=True):
    """One proposal: its number in the day's record, its area, its move in one line, its
    body, its source and the place it would change."""

    number: int
    area: Area
    move: str
    body: str
    source: str
    where: str


class Run(Frozen, frozen=True, kw_only=True):
    """One run of the day: when it added, what it read, and the numbers it added."""

    at: Moment
    read: str
    proposals: tuple[int, ...] = ()


class Refuted(Frozen, frozen=True, kw_only=True):
    """The reviewer refuted a proposal on a day, with his reason."""

    number: int
    reason: str
    day: Day


class Passed(Frozen, frozen=True, kw_only=True):
    """The reviewer passed a proposal on a day into the item of its area, by its path."""

    number: int
    area: Area
    item_path: str = msgspec.field(name="item")
    day: Day


class Dropped(Frozen, frozen=True, kw_only=True):
    """The owner dropped the item a proposal passed into: its move, what the reviewer of a later
    morning reads as his no, the day, and the item's path."""

    number: int
    text: str
    said: str
    day: Day
    item_path: str = msgspec.field(name="item")


class DayRecord(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The whole record of one day and one kind, every list written, an empty one too."""

    date: Day
    kind: Kind
    runs: tuple[Run, ...]
    proposals: tuple[Proposal, ...]
    refuted: tuple[Refuted, ...]
    passed: tuple[Passed, ...]
    dropped: tuple[Dropped, ...]
