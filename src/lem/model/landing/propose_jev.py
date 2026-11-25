"""Jev's one read of each finding called under the bar, before the pull request is written
(`main:land.jev_read`, `under_findings`, `jev_refused`, `jev_endings`): each item the branch
adds with `worth: no`, and each `under:` line of the notes' parts that name a finding nobody
filed. A finding Jev reads as over the bar stops `propose` once; Jev is never asked about a
finding twice, and its line in the text ends with Jev's score, or why Jev was not asked.
"""

import re
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import propose_lines
from lem.model.landing.propose_facts import small
from lem.records.base import Frozen

if TYPE_CHECKING:
    from lem.model.landing.propose_facts import Facts, Filing
    from lem.model.landing.propose_notes import Notes
    from lem.records.record import Record

# The score at or over which `propose` refuses once: the starting value of Jev's documentation
# (jev-advice.md of task backlog-refuted-items-and-jev on `main`, 2026-11-23); a guess, not
# measured on findings, of which no labeled sample exists.
OVER_AT = 0.7
UNDER = re.compile(r"(?i)(?<![\w-])under:[ \t]*(?=\S)")
PLACE = re.compile(r"`([^`]+)`")
OVER = '"{0}" (Jev: {1.score:.2f})'


class Asked(Frozen, frozen=True, kw_only=True):
    """A finding called under the bar: its key (the line, or the item's path), and where,
    its title and its text, as Jev reads them."""

    key: str
    where: str
    title: str
    what: str


class Said(Frozen, frozen=True, kw_only=True):
    """Jev's word on a finding: its score over the bar, or why it was not asked."""

    score: float | None = None
    why: str | None = None

    def over(self) -> bool:
        """Whether Jev read the finding as over the bar."""
        return self.score is not None and self.score >= OVER_AT


def line_asked(entry: tuple[str, ...]) -> Asked | None:
    """A notes entry called under the bar: the text before its `under:` is the finding,
    and the first place in backticks is where."""
    text = "\n".join(entry)
    found = UNDER.search(text)
    if found is None:
        return None
    finding = text[: found.start()].strip()
    finding = finding.lstrip("-*+ ").rstrip(" ;,")
    key, where = entry[0].strip(), where_of(finding)
    return Asked(key=key, where=where, title=finding, what=text)


def where_of(finding: str) -> str:
    """The first place in backticks of a finding's line, or none."""
    place = PLACE.search(finding)
    return place[1] if place else ""


def item_asked(filing: Filing) -> Asked:
    """An item the branch adds with `worth: no`."""
    title = filing.title or filing.path
    return Asked(key=filing.path, where=filing.path, title=title, what=filing.path)


def asked(record: Record, notes: Notes, facts: Facts) -> tuple[Asked, ...]:
    """Every finding called under the bar: the items, then the notes' lines."""
    entries = propose_lines.called(notes, small=small(record))
    lines = tuple(filter(None, map(line_asked, entries)))
    refused = (filing for filing in facts.added if filing.worth == "no")
    return (*map(item_asked, refused), *lines)


def refused(slug: str, fresh: dict[str, Said]) -> Refusal | None:
    """The refusal of the findings Jev read as over the bar on this read, each with its
    score; a finding read before never stops the step again."""
    over = [key for key in fresh if fresh[key].over()]
    if not over:
        return None
    said = [OVER.format(key, fresh[key]) for key in over]
    named = "; ".join(said)
    return Refusal(
        "jev-over",
        f"{len(over)} finding(s) called under the bar, which Jev reads as over it at "
        f"{OVER_AT} or more: {named}",
        "look at the finding again: make its item `worth: later` (a commit, so lem land "
        f"checks {slug} runs first), or keep `worth: no` with its `Decided against:` line, "
        "or keep the notes line `under:` with its reason; Jev is not asked again about it",
    )
