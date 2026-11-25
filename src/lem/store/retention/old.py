"""An old ended task, kept to its small record: its journal folded into its summary with its
citations cleared, under the record's lock and at the revision read, then every other file of
its folder removed (`project.cmd_prune` on `main`). The record is written before any file goes,
so a run cut off between the two leaves files that nothing cites, which the next run removes.
"""

from contextlib import nullcontext
from functools import partial
from typing import TYPE_CHECKING

from lem.kernel import locks, release
from lem.kernel.errors import Fault, Refusal
from lem.store import tasks
from lem.store.retention import activity, answer, files, fold, rules
from lem.store.retention.trees import files_in

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime
    from pathlib import Path

    from lem.records.record import Record

TASKS = "tasks"


def records_of(removal: files.Removal) -> list[Record]:
    """Every task record of the state folder that reads; a link, and a folder whose record
    does not read, are named among what was skipped."""
    folder = removal.top / TASKS
    if removal.link(folder) or not folder.is_dir():
        return []
    names = sorted(folder.iterdir())
    entries = [one for one in names if not removal.link(one)]
    folders = [one for one in entries if one.is_dir()]
    found = [read(removal, one) for one in folders]
    return [record for record in found if record is not None]


def read(removal: files.Removal, folder: Path) -> Record | None:
    """The record of the task folder `folder`, or None when it does not read, which is
    named."""
    if removal.link(folder / tasks.RECORD):
        return None
    try:
        record = tasks.read(removal.top, folder.name)
    except (Refusal, Fault) as error:
        removal.skip(folder, f"its task.json does not read: {error}")
        return None
    slug = record.task.slug
    if slug != folder.name:
        removal.skip(folder, f"its task.json names {slug}")
        return None
    try:
        tasks.writable(record, release.running())
    except Refusal as refusal:
        removal.skip(folder, refusal.why)
        return None
    return record


def keep(
    removal: files.Removal, record: Record, cutoff: datetime, now: datetime
) -> tuple[answer.Folded | None, answer.Kept | None]:
    """Recheck the old task and keep it to its small record under the task lock."""
    folder = removal.top / TASKS / record.task.slug
    path = folder / tasks.LOCK
    if removal.link(folder) or not removal.inside(path):
        return None, None
    with nullcontext() if removal.dry else locks.held(path):
        current = rechecked(removal, folder, record, cutoff)
        if current is None:
            return None, None
        return folded(removal, current, folder, now), files_of(removal, current, folder)


def rechecked(
    removal: files.Removal, folder: Path, record: Record, cutoff: datetime
) -> Record | None:
    """The same old, writable task, if no writer or session got there first."""
    current = read(removal, folder)
    if current is None:
        return None
    if current.revision != record.revision:
        removal.skip(
            folder,
            f"{folder.name} is at revision {current.revision}, not {record.revision}",
        )
        return None
    if activity.call_of(removal.top, current, cutoff) != "old":
        return None
    return current


def folded(
    removal: files.Removal, record: Record, folder: Path, now: datetime
) -> answer.Folded | None:
    """Fold the journal into its summary and clear its citations; what was folded."""
    if rules.folded_already(record) and record == rules.cleared(record):
        return None
    task = record.task
    if not removal.dry:
        change = partial(rules.folded_into, summary=fold.summary_of(record, now))
        tasks.update_held(folder, record, change)
    return answer.Folded(
        task=task.slug, status=task.status, entries=len(record.journal)
    )


def files_of(
    removal: files.Removal, record: Record, folder: Path
) -> answer.Kept | None:
    """Remove every file of the task's folder but its small record; what went."""
    task = record.task
    gone = dict(removed_in(removal, folder))
    files.emptied(removal, folder)
    if not gone:
        return None
    paths = tuple(gone)
    return answer.Kept(
        task=task.slug, status=task.status, files=paths, bytes=sum(gone.values())
    )


def removed_in(removal: files.Removal, folder: Path) -> Iterator[tuple[str, int]]:
    """Remove each file of the task's folder but the small record: its path in the folder,
    and its bytes."""
    for path in files_in(removal, folder):
        shown = path.relative_to(folder).as_posix()
        size = None if rules.kept(shown) else removal.removed(path)
        if size is not None:
            yield shown, size
