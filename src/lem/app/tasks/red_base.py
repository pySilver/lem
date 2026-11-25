"""Set a red-base hold or lift it after its repair lands, under the task's step lock."""

from typing import TYPE_CHECKING

from lem.app.tasks import release
from lem.kernel import clock
from lem.model.task import red_base
from lem.store import places, steps, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.records.task import Task


def changed(state: Path, record: Record, after: str | None, now: Moment) -> Record:
    """The change of the hold after a fresh read of the repair."""
    if after is not None:
        return red_base.blocked(record, tasks.read(state, after), now)
    repair = tasks.read(state, red_base.needs_repair(record))
    return red_base.released(record, repair, now)


def run(folder: Path, slug: str, after: str | None) -> Task:
    """The task with its hold set or lifted."""
    state = places.workspace(folder).state
    tasks.read(state, slug)
    now = clock.now()
    with steps.step(state, slug, "red-base", now):
        record = release.checked(state, slug)
        updated = changed(state, record, after, now)
        if updated is record:
            return record.task
        return tasks.update(state, slug, lambda _: updated, record.revision).task
