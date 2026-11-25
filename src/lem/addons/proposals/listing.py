"""`lem proposals list`: every proposal of every record with no verdict yet, every one refuted,
passed or dropped on any day, and the newest run of each kind (`project.cmd_proposals_read` on
`main`).

A morning whose reviewer did not finish is read on the next one: a proposal with no verdict is
listed whatever its day. The newest run of each kind is the moment the next retro reads from.
"""

from itertools import chain
from typing import TYPE_CHECKING

import msgspec

from lem.addons.proposals import days, names
from lem.addons.proposals.listed import (
    DroppedOne,
    Listed,
    Newest,
    PassedOne,
    Read,
    RefutedOne,
)

if TYPE_CHECKING:
    from pathlib import Path

    from lem.addons.proposals.record import DayRecord, Kind, Passed, Proposal, Run

BACKLOG = "backlog"
GROUPS = ("undecided", "refuted", "passed", "dropped")


def listed(state: Path) -> Read:
    """Every proposal of the state folder's records, by its verdict, and the newest runs."""
    records = days.every(state)
    every = tuple(chain.from_iterable(judged_of(state, found) for found in records))
    lists = {
        group: tuple(one for named, one in every if named == group) for group in GROUPS
    }
    return Read(**lists, newest=newest_runs(records))


def judged_of(state: Path, found: days.Found) -> tuple[tuple[str, Listed], ...]:
    """Each proposal of one record, with its group."""
    kind, path, record = found
    return tuple(
        judged(state, record, base_of(kind, path, record, proposal))
        for proposal in record.proposals
    )


def base_of(kind: Kind, path: Path, record: DayRecord, proposal: Proposal) -> Listed:
    """One proposal as the list gives it, with no verdict."""
    fields = msgspec.structs.asdict(proposal)
    fields["name"] = names.name_of(kind, record.date, proposal.number)
    return Listed(kind=kind, date=record.date, path=str(path), **fields)


def judged(state: Path, record: DayRecord, one: Listed) -> tuple[str, Listed]:
    """The proposal's group and the proposal with its verdict and drop, when it has them: a
    drop first, then a refute, then a pass."""
    number = one.number
    dropped = next((entry for entry in record.dropped if entry.number == number), None)
    if dropped is not None:
        return "dropped", DroppedOne(
            **msgspec.structs.asdict(one),
            said=dropped.said,
            day=dropped.day,
            item_path=dropped.item_path,
        )
    refuted = next((entry for entry in record.refuted if entry.number == number), None)
    if refuted is not None:
        return "refuted", RefutedOne(
            **msgspec.structs.asdict(one), reason=refuted.reason, day=refuted.day
        )
    passed = next((entry for entry in record.passed if entry.number == number), None)
    if passed is None:
        return "undecided", one
    return "passed", passed_one(state, one, passed)


def passed_one(state: Path, one: Listed, passed: Passed) -> PassedOne:
    """A passed proposal, with whether its item is still in the state folder's backlog."""
    _, _, name = passed.item_path.rpartition("/")
    there = (state / BACKLOG / name).is_file()
    return PassedOne(
        **msgspec.structs.asdict(one),
        item_path=passed.item_path,
        day=passed.day,
        there=there,
    )


def newest_runs(records: tuple[days.Found, ...]) -> dict[Kind, Newest | None]:
    """The newest run of each kind, None for a kind with none."""
    newest: dict[Kind, Newest | None] = {"night": None, "retro": None}
    for kind, _, record in records:
        for run in record.runs:
            newest[kind] = newer(newest[kind], record, run)
    return newest


def newer(seen: Newest | None, record: DayRecord, run: Run) -> Newest | None:
    """The newer of `seen` and the run `run` of `record`."""
    if seen is not None and seen.at >= run.at:
        return seen
    return Newest(date=record.date, at=run.at, read=run.read)
