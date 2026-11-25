"""One run of retention over a state folder (`project.cmd_prune` on `main`): each old ended
task kept to its small record (`old.py`), then the old folders of the experts, the panels, the
naps and the cast's copies (`folders.py`); or, in a dry run, what would go, with no file
changed. A task whose journal is its summary already is folded no more, and its files are
removed again only when some are left, so a second run changes nothing.
"""

from datetime import timedelta
from typing import TYPE_CHECKING

import msgspec

from lem.store import guard
from lem.store.retention import activity, files, old
from lem.store.retention.answer import Pruned
from lem.store.retention.folders import old_folders

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from lem.records.record import Record
    from lem.store.retention.rules import Call


def pruned(state: Path, keep: int, source: str, now: datetime, *, dry: bool) -> Pruned:
    """Run retention over `state` with `keep` days, the number's source named, at `now`."""
    files.refused_link(state)
    guard.readable(state)
    removal = files.Removal(top=state.resolve(), dry=dry)
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


def tasks_of(removal: files.Removal, begun: Pruned, now: datetime) -> Pruned:
    """Keep each old task to its small record, and count the tasks by what retention does
    with each."""
    records = old.records_of(removal)
    calls = [activity.call_of(removal.top, record, begun.before) for record in records]
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
    removal: files.Removal, counts: Pruned, aged: list[Record], now: datetime
) -> Pruned:
    """Fold each old task's journal and remove its files, and the totals of both."""
    kept_by_task = [old.keep(removal, one, counts.before, now) for one in aged]
    summarized = tuple(one for one, _ in kept_by_task if one is not None)
    kept = tuple(one for _, one in kept_by_task if one is not None)
    return msgspec.structs.replace(
        counts,
        tasks=kept,
        summarized=summarized,
        entries=sum(one.entries for one in summarized),
        files=sum(len(one.files) for one in kept),
        bytes=sum(one.bytes for one in kept),
    )
