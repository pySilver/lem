"""The items a verdict will write, planned in full before anything is written: one item for each
area that passed, under the title the reviewer gives it, and one `worth: no` item for each
refuted proposal.

A refuted proposal's item is found again by its `proposals` line when a verdict was cut off
between its items and its records, and written again in place; a retry that passes it instead
removes it (`project.refuted_items` on `main`).
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.addons.proposals import heads, item_files, item_text, judging
from lem.addons.proposals.judgment import Against, ItemMade

if TYPE_CHECKING:
    import datetime as dt
    from pathlib import Path

    from lem.addons.proposals import verdicts


type Left = dict[str, list[Path]]


@dataclass(frozen=True, kw_only=True, slots=True)
class Plan:
    """Every verdict checked, the records read, the items to write with their texts, and the
    refuted items a verdict that passes their proposal removes."""

    judged: tuple[judging.Judged, ...]
    records: verdicts.Records
    made: tuple[tuple[ItemMade, str], ...]
    against: tuple[tuple[Against, str], ...]
    left: Left


def planned(
    folder: Path, state: Path, given: verdicts.VerdictsGiven, today: dt.date
) -> Plan:
    """The plan of the verdicts `given`, read against the records of `state` and the items
    of `folder`; refused at the first verdict that does not hold."""
    every, records = judging.judged_all(state, given)
    taken = item_files.taken_names(folder)
    left = heads.refuted_items(folder)
    return Plan(
        judged=every,
        records=records,
        made=passed_items(every, given.titles, today, taken),
        against=refuted_items(every, today, left, taken),
        left=left,
    )


def passed_items(
    every: tuple[judging.Judged, ...],
    titles: dict[str, str],
    today: dt.date,
    taken: set[str],
) -> tuple[tuple[ItemMade, str], ...]:
    """The item of each area that passed, with its text."""
    areas = judging.areas_of(every)
    named = judging.titled(areas, titles)
    return tuple(
        passed_item(area, named[area], today, entries, taken)
        for area, entries in areas.items()
    )


def passed_item(
    area: str,
    title: str,
    today: dt.date,
    entries: list[item_text.Entry],
    taken: set[str],
) -> tuple[ItemMade, str]:
    """The item of one area that passed, at a name not taken, and its text."""
    path = item_files.recorded(item_files.free_name(item_files.slug_of(title), taken))
    proposals = tuple(named for named, _ in entries)
    text = item_text.passed_text(title, area, today, entries)
    return ItemMade(area=area, title=title, path=path, proposals=proposals), text


def refuted_items(
    every: tuple[judging.Judged, ...],
    today: dt.date,
    left: Left,
    taken: set[str],
) -> tuple[tuple[Against, str], ...]:
    """The `worth: no` item of each refuted proposal, with its text."""
    refuted = (one for one in every if one.word == "refuted")
    return tuple(refuted_item(one, today, left, taken) for one in refuted)


def refuted_item(
    one: judging.Judged, today: dt.date, left: Left, taken: set[str]
) -> tuple[Against, str]:
    """The item of one refuted proposal: the one a cut-off verdict left, else at a name not
    taken; and its text."""
    found = left.get(one.name)
    name = found[0].name if found else fresh_name(one, taken)
    text = item_text.refuted_text(one.name, one.proposal, one.said, today)
    return Against(proposal=one.name, path=item_files.recorded(name)), text


def fresh_name(one: judging.Judged, taken: set[str]) -> str:
    """A name not taken for a refuted proposal's item, from its move."""
    stem = item_files.slug_of(one.proposal.move) or "refuted"
    return item_files.free_name(stem, taken)
