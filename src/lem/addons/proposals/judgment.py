"""What `lem proposals verdict` gives: its day, the proposals it refuted, the item of each area
that passed, and the `worth: no` item of each refuted proposal."""

import datetime as dt

import msgspec

from lem.records.base import Frozen


class ItemMade(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The item of one area that passed: its area, title, path and the proposals in it."""

    area: str
    title: str
    path: str
    proposals: tuple[str, ...]


class Against(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The `worth: no` item of one refuted proposal: the proposal, and the item's path."""

    proposal: str
    path: str


class Judgment(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The verdicts written: the day, the names refuted, the items of the areas that passed,
    and the items decided against."""

    day: dt.date
    refuted: tuple[str, ...]
    items_made: tuple[ItemMade, ...] = msgspec.field(name="items")
    decided_against: tuple[Against, ...]
