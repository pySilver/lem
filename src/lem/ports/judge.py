"""The `Judge` port: Jev's word on a review's finding (the design's part 4): whether an open
backlog item already holds it, and whether it is over the bar.

Jev reads each item as the caller gives it, which is the item as the tip's commit holds it,
never a builder's edit on disk (`land.cmd_alike` reads HEAD on `main`)."""

from typing import Protocol

from lem.records.base import Frozen


class Defect(Frozen, frozen=True, kw_only=True):
    """A finding as Jev reads it: where, its title, and the run that shows it."""

    where: str
    title: str
    what: str


class Candidate(Frozen, frozen=True, kw_only=True):
    """A backlog item that may hold the finding, as Jev reads it: its path in the repository,
    its title, its `where`, and the first line of its body."""

    path: str
    title: str
    where: str | None = None
    first: str | None = None


class Score(Frozen, frozen=True, kw_only=True):
    """Jev's score: how likely the finding is over the bar, or the same as the item at
    `path`."""

    score: float
    path: str | None = None


class NotAsked(Frozen, frozen=True, kw_only=True):
    """Jev was not asked, and why (no key, the setting off, no answer)."""

    why: str


class Judge(Protocol):
    """Ask Jev."""

    def same_items(
        self, defect: Defect, candidates: tuple[Candidate, ...]
    ) -> tuple[Score, ...] | NotAsked: ...
    def over_bar(self, defect: Defect) -> Score | NotAsked: ...
