"""One run of retention over a state folder (`project.cmd_prune` on `main`): each old ended
task kept to its small record (`old.py`), then the old folders of the experts, the panels, the
naps and the cast's copies (`folders.py`); or, in a dry run, what would go, with no file
changed. A task whose journal is its summary already is folded no more, and its files are
removed again only when some are left, so a second run changes nothing.
"""

from datetime import timedelta
from typing import TYPE_CHECKING

import msgspec

from lem.store.retention.answer import Pruned
from lem.store.retention.files import Removal, refused_link
from lem.store.retention.folders import old_folders
from lem.store.retention.old import files_of, folded, records_of
from lem.store.retention.rules import Call, call_of

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from pathlib import Path

    from lem.records.record import Record


def pruned(state: Path, keep: int, source: str, now: datetime, *, dry: bool) -> Pruned:
    """Run retention over `state` with `keep` days, the number's source named, at `now`."""
    refused_link(state)
    removal = Removal(top=state.resolve(), dry=dry)
    cutoff = now - timedelta(days=keep)
    begun = Pruned(
        dry_run=dry, keep_days=keep, source=source, before=cutoff, state=str(state)
    )
    counted = tasks_of(removal, begun, now)
    folders = old_folders(removal, cutoff)
    return msgspec.structs.replace(
        counted,
        folders=folders,
        bytes=counted.bytes + sum(one.bytes for one in folders),
        skipped=tuple(removal.skipped),
        failed=tuple(removal.failed),
    )


def tasks_of(removal: Removal, begun: Pruned, now: datetime) -> Pruned:
    """Keep each old task to its small record, and count the tasks by what retention does
    with each."""
    records = records_of(removal)
    calls = [call_of(record, begun.before) for record in records]
    return kept_of(removal, counted(begun, calls), aged_of(records, calls), now)


def aged_of(records: list[Record], calls: list[Call]) -> list[Record]:
    """The old tasks among `records`, whose calls are `calls`."""
    pairs = zip(records, calls, strict=True)
    return [record for record, call in pairs if call == "old"]


def counted(begun: Pruned, calls: list[Call]) -> Pruned:
    """The run with how many tasks were open, young and old."""
    opened = calls.count("open")
    young = calls.count("young")
    aged = calls.count("old")
    return msgspec.structs.replace(begun, open=opened, young=young, old=aged)


def kept_of(
    removal: Removal, counts: Pruned, aged: list[Record], now: datetime
) -> Pruned:
    """Fold each old task's journal and remove its files, and the totals of both."""
    summarized = each(lambda one: folded(removal, one, now), aged)
    kept = each(lambda one: files_of(removal, one), aged)
    return msgspec.structs.replace(
        counts,
        tasks=kept,
        summarized=summarized,
        entries=sum(one.entries for one in summarized),
        files=sum(len(one.files) for one in kept),
        bytes=sum(one.bytes for one in kept),
    )


def each[Done](
    act: Callable[[Record], Done | None], aged: list[Record]
) -> tuple[Done, ...]:
    """What `act` did for each old task, for each where it did something."""
    found = [act(one) for one in aged]
    return tuple(one for one in found if one is not None)
