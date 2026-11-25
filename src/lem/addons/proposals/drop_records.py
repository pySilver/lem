"""The records that keep a drop: each proposal the item names passed into it on its day, and
gets its drop once (`project.cmd_proposals_drop` on `main`)."""

from typing import TYPE_CHECKING

import msgspec

from lem.addons.proposals import days, names
from lem.addons.proposals.record import Dropped
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    import datetime as dt
    from pathlib import Path

    from lem.addons.proposals.record import DayRecord

# What a drop says in the record, which the reviewer of a later morning reads as his no.
SAID = "the owner dropped it"

type Held = tuple[Path, DayRecord]
type Records = dict[tuple[str, str], Held]
type Told = tuple[str, str]


def kept(state: Path, listed: tuple[str, ...], path: str, today: dt.date) -> Records:
    """The records of the proposals `listed`, each with its drop of the item `path`; refused
    for a proposal no record says passed into it."""
    records: Records = {}
    for name in listed:
        named = names.parsed(name)
        if named is None:
            raise unrecorded(path, name)
        told = (path, name)
        key = loaded(state, records, named, told)
        records[key] = dropped_in(records[key], named.number, told, today)
    return records


def dropped_in(found: Held, number: int, told: Told, today: dt.date) -> Held:
    """The record at its path, with the drop of proposal `number`."""
    record_path, record = found
    return record_path, with_drop(record, number, told, today)


def loaded(
    state: Path, records: Records, named: names.Named, told: Told
) -> tuple[str, str]:
    """The key of the proposal's record in `records`, read into it when it is not there;
    refused when there is no record."""
    key = (named.kind, named.day.isoformat())
    if key in records:
        return key
    found = days.path_of(state, named.kind, named.day)
    record = days.read(found, named.kind)
    if record is None:
        raise unrecorded(*told)
    records[key] = (found, record)
    return key


def written(records: Records) -> None:
    """Write each record of a drop whole."""
    for found in records.values():
        days.write(*found)


def with_drop(record: DayRecord, number: int, told: Told, today: dt.date) -> DayRecord:
    """The record with the drop of proposal `number`, once; refused when it did not pass into
    the item `told` names (its path, and the proposal's name)."""
    path, name = told
    passed = any(
        entry.number == number and entry.item_path == path for entry in record.passed
    )
    if not passed:
        raise unrecorded(path, name)
    if any(entry.number == number for entry in record.dropped):
        return record
    move = record.proposals[number - 1].move
    entry = Dropped(number=number, text=move, said=SAID, day=today, item_path=path)
    return msgspec.structs.replace(record, dropped=(*record.dropped, entry))


def unrecorded(path: str, name: str) -> Refusal:
    """The refusal of an item that names a proposal no record says passed into it."""
    return Refusal(
        "item-unrecorded",
        f"the item {path} names {name}, and no record says that it passed into this item, "
        "so no record keeps its drop",
        "the maintaining session compares the item with the records of lem proposals list",
    )
