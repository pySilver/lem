"""The `Judge` port: Jev's word on a review's finding (the design's part 4): whether an open
backlog item already holds it, and whether it is over the bar."""

from typing import Protocol

from lem.records.base import Frozen


class Defect(Frozen, frozen=True, kw_only=True):
    """A finding as Jev reads it: where, its title, and the run that shows it."""

    where: str
    title: str
    what: str


class Score(Frozen, frozen=True, kw_only=True):
    """Jev's score: how likely the finding is over the bar, or the same as one item."""

    score: float
    path: str | None = None


class NotAsked(Frozen, frozen=True, kw_only=True):
    """Jev was not asked, and why (no key, the setting off, no answer)."""

    why: str


class Judge(Protocol):
    """Ask Jev."""

    def same_items(
        self, defect: Defect, paths: tuple[str, ...]
    ) -> tuple[Score, ...] | NotAsked: ...
    def over_bar(self, defect: Defect) -> Score | NotAsked: ...
