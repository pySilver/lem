"""An old ended task, kept to its small record: its journal folded into its summary with its
citations cleared, under the record's lock and at the revision read, then every other file of
its folder removed (`project.cmd_prune` on `main`). The record is written before any file goes,
so a run cut off between the two leaves files that nothing cites, which the next run removes.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.kernel.errors import Fault, Refusal
from lem.store import tasks
from lem.store.retention import fold, rules
from lem.store.retention.answer import Folded, Kept
from lem.store.retention.files import Removal, emptied
from lem.store.retention.trees import files_in

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime
    from pathlib import Path

    from lem.records.record import Record

TASKS = "tasks"


def records_of(removal: Removal) -> list[Record]:
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


def read(removal: Removal, folder: Path) -> Record | None:
    """The record of the task folder `folder`, or None when it does not read, which is
    named."""
    try:
        return tasks.read(removal.top, folder.name)
    except (Refusal, Fault) as error:
        removal.skip(folder, f"its task.json does not read: {error}")
    return None


def folded(removal: Removal, record: Record, now: datetime) -> Folded | None:
    """Fold the old task's journal into its summary and clear its citations, unless it is
    folded already; what was folded. A record another writer changed first is left for the
    next run."""
    if rules.folded_already(record):
        return None
    task = record.task
    entries = len(record.journal)
    told = Folded(task=task.slug, status=task.status, entries=entries)
    if removal.dry:
        return told
    change = partial(rules.folded_into, summary=fold.summary_of(record, now))
    try:
        tasks.update(removal.top, task.slug, change, record.revision)
    except Refusal as refusal:
        removal.skip(removal.top / TASKS / task.slug, refusal.why)
        return None
    return told


def files_of(removal: Removal, record: Record) -> Kept | None:
    """Remove every file of the old task's folder but its small record, once its journal is
    its summary on record (in a dry run, at once); what went."""
    task = record.task
    if not removal.dry and not folded_now(removal, task.slug):
        return None
    folder = removal.top / TASKS / task.slug
    gone = dict(removed_in(removal, folder))
    emptied(removal, folder)
    if not gone:
        return None
    files = tuple(gone)
    return Kept(
        task=task.slug, status=task.status, files=files, bytes=sum(gone.values())
    )


def folded_now(removal: Removal, slug: str) -> bool:
    """Whether the task's journal is its summary on record now."""
    return rules.folded_already(tasks.read(removal.top, slug))


def removed_in(removal: Removal, folder: Path) -> Iterator[tuple[str, int]]:
    """Remove each file of the task's folder but the small record: its path in the folder,
    and its bytes."""
    for path in files_in(removal, folder):
        shown = path.relative_to(folder).as_posix()
        size = None if rules.kept(shown) else removal.removed(path)
        if size is not None:
            yield shown, size
