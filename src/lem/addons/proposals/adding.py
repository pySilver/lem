"""`lem proposals add`: one run of the night or the retro added to the record of its day, which
this makes when it is not there (`project.cmd_proposals_add` on `main`).

What the run read, and its proposals with the numbers after those already there. Nothing of the
record is rewritten: a second run of the day keeps the numbers, the verdicts and the drops of the
first. A run that is not in the form is refused before anything is written.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.addons.proposals import days, names
from lem.addons.proposals.given import Given, RunGiven, checked
from lem.addons.proposals.record import DayRecord, Kind, Proposal, Run
from lem.records.base import Day, Frozen, Moment
from lem.store import reviewer_items

if TYPE_CHECKING:
    import datetime as dt
    from pathlib import Path


class Added(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """What one add wrote: the record, its kind and day, the run's moment, and the numbers and
    names of the proposals it added."""

    path: str = msgspec.field(name="file")
    kind: Kind
    date: Day
    at: Moment
    numbers: tuple[int, ...]
    names: tuple[str, ...]


def numbered(given: Given, number: int) -> Proposal:
    """The proposal `given` as the record keeps it, with its number."""
    return Proposal(
        number=number,
        area=given.area,
        move=given.move.strip(),
        body=given.body.strip(),
        source=given.source.strip(),
        where=given.where.strip(),
    )


def added(state: Path, kind: Kind, day: dt.date, run: RunGiven, now: Moment) -> Added:
    """Add the run `run` of `kind` to its record of `day`, under the records' lock."""
    path = days.path_of(state, kind, day)
    checked(run)
    with reviewer_items.held(state):
        before = days.read(path, kind) or DayRecord(
            date=day,
            kind=kind,
            runs=(),
            proposals=(),
            refuted=(),
            passed=(),
            dropped=(),
        )
        first = len(before.proposals) + 1
        numbers = tuple(range(first, first + len(run.proposals)))
        days.write(path, appended(before, run, numbers, now))
    named = tuple(names.name_of(kind, day, number) for number in numbers)
    return Added(
        path=str(path), kind=kind, date=day, at=now, numbers=numbers, names=named
    )


def appended(
    before: DayRecord, run: RunGiven, numbers: tuple[int, ...], now: Moment
) -> DayRecord:
    """The record with the run and its proposals after those already there."""
    made = map(numbered, run.proposals, numbers, strict=True)
    ran = Run(at=now, read=run.read.strip(), proposals=numbers)
    return msgspec.structs.replace(
        before, runs=(*before.runs, ran), proposals=(*before.proposals, *made)
    )
