"""Each verdict read against its record, and the areas that passed with the title of each: what
`lem proposals verdict` checks in full before it writes anything."""

from typing import TYPE_CHECKING, Literal

from lem.addons.proposals import item_files, names, verdicts
from lem.addons.proposals.record import Proposal
from lem.kernel.errors import Refusal
from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path

    from lem.addons.proposals.item_text import Entry

type Word = Literal["refuted", "passed"]
type Areas = dict[str, list[Entry]]


class Judged(Frozen, frozen=True, kw_only=True):
    """One verdict, checked: the proposal's name and place, refuted or passed, the reason or
    the area, and the proposal."""

    name: str
    named: names.Named
    word: Word
    said: str
    proposal: Proposal


def judged_all(
    state: Path, given: verdicts.VerdictsGiven
) -> tuple[tuple[Judged, ...], verdicts.Records]:
    """Every verdict checked against its record, and the records read; refused at the first
    verdict that does not hold, and for no verdict at all."""
    if not given.verdicts:
        raise Refusal(
            "verdict-none",
            "`verdicts` is empty: a verdict file judges one proposal at least",
            f"give {verdicts.FORM}",
        )
    records: verdicts.Records = {}
    seen: set[names.Named] = set()
    every = tuple(
        judged_one(state, verdict, seen, records) for verdict in given.verdicts
    )
    return every, records


def judged_one(
    state: Path,
    verdict: verdicts.VerdictGiven,
    seen: set[names.Named],
    records: verdicts.Records,
) -> Judged:
    """One verdict checked against its record."""
    word, said = verdicts.call_of(verdict)
    named = verdicts.named_of(verdict, seen)
    record = verdicts.record_of(state, named, records)
    return Judged(
        name=names.name_of(named.kind, named.day, named.number),
        named=named,
        word="refuted" if word == "refuted" else "passed",
        said=said.strip(),
        proposal=verdicts.proposal_of(named, record),
    )


def areas_of(every: tuple[Judged, ...]) -> Areas:
    """The proposals that passed, by their area, in the order of the verdicts."""
    areas: Areas = {}
    for one in every:
        if one.word == "passed":
            areas.setdefault(one.said, []).append((one.name, one.proposal))
    return areas


def titled(areas: Areas, titles: dict[str, str]) -> dict[str, str]:
    """The title of each area's item, its spaces made one; refused for an area with no title
    or no word to name its file by, and for a title of an area that did not pass."""
    worded = {area for area, title in titles.items() if item_files.slug_of(title)}
    wrong = set(titles).difference(areas)
    wrong.update(area for area in areas if area not in worded)
    if wrong:
        named = ", ".join(sorted(wrong))
        raise Refusal(
            "verdict-titles",
            f"`titles` does not give each area that passed one title with a word: {named}",
            "give each area that passed one title, and no other: each area becomes one "
            "item with that title",
        )
    return {area: " ".join(titles[area].split()) for area in areas}
