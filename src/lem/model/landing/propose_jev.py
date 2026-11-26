"""Jev's one read of each finding called under the bar, before the pull request is written
(`main:land.jev_read`, `under_findings`, `jev_refused`, `jev_endings`): each item the branch
adds with `worth: no`, and each `under:` line of the notes' parts that name a finding nobody
filed. A finding Jev reads as over the bar stops `propose` once, and an item that still gives
no reason stops it again. A finding's text gets one score, which its line in the proposal shows.
"""

import re
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import alike, propose_lines
from lem.model.landing.items import Defect
from lem.model.landing.propose_facts import small
from lem.records.base import Frozen

if TYPE_CHECKING:
    from lem.model.landing.items import BacklogItem
    from lem.model.landing.propose_facts import Facts
    from lem.model.landing.propose_notes import Notes
    from lem.records.landing.review import JevRead
    from lem.records.record import Record

# The score at or over which `propose` refuses once: the starting value of Jev's documentation
# (jev-advice.md of task backlog-refuted-items-and-jev on `main`, 2026-11-23); a guess, not
# measured on findings, of which no labeled sample exists.
OVER_AT = 0.7
UNDER = re.compile(r"(?i)(?<![\w-])under:[ \t]*(?=\S)")
PLACE = re.compile(r"`([^`]+)`")
OVER = '"{0}" (Jev: {1:.2f})'


class Asked(Frozen, frozen=True, kw_only=True):
    """A finding called under the bar: the line or path that names it, the defect as Jev
    reads it, and whether it gives a reason."""

    label: str
    defect: Defect
    reason: bool = True

    @property
    def key(self) -> str:
        """The finding's digest without the reason it was called under the bar."""
        return alike.key_of(self.defect)


def line_asked(entry: tuple[str, ...]) -> Asked | None:
    """A notes entry called under the bar: the text before its `under:` is the finding,
    and the first place in backticks is where."""
    text = "\n".join(entry)
    found = UNDER.search(text)
    if found is None:
        return None
    before = " ".join(text[: found.start()].split())
    mark = propose_lines.LISTED.match(before)
    finding = (before[mark.end() :] if mark else before).rstrip(" ;,:-(")
    return Asked(
        label=entry[0].strip(),
        defect=Defect(where=where_of(finding), title=finding, what=finding),
    )


def where_of(finding: str) -> str:
    """The first place in backticks of a finding's line, or none."""
    place = PLACE.search(finding)
    return place[1] if place else ""


def item_asked(filing: BacklogItem) -> Asked:
    """An item the branch adds with `worth: no`."""
    defect = Defect(
        where=filing.where or "",
        title=filing.title,
        what="\n\n".join(filing.paragraphs),
    )
    return Asked(label=filing.path, defect=defect, reason=filing.reason)


def asked(record: Record, notes: Notes, facts: Facts) -> tuple[Asked, ...]:
    """Every finding called under the bar: the items, then the notes' lines."""
    entries = propose_lines.called(notes, small=small(record))
    lines = tuple(filter(None, map(line_asked, entries)))
    return (*map(item_asked, facts.under), *lines)


def blocked(finding: Asked, read: JevRead) -> float | None:
    """The score that stops the proposal, on its first refusal or while the reason is absent."""
    if read.refused and finding.reason:
        return None
    score = read.score
    return score if score is not None and score >= OVER_AT else None


def refused(slug: str, over: dict[str, float]) -> Refusal:
    """The proposal's refusal, with the score of each finding that stops it."""
    said = [OVER.format(label, score) for label, score in over.items()]
    named = "; ".join(said)
    return Refusal(
        "jev-over",
        f"{len(over)} finding(s) called under the bar, which Jev reads as over it at "
        f"{OVER_AT} or more: {named}",
        "look at the finding again: make its item `worth: later` (a commit, so lem land "
        f"checks {slug} runs first), or keep `worth: no` with its `Decided against:` line, "
        "or keep the notes line `under:` with its reason; Jev is not asked again about it",
    )
