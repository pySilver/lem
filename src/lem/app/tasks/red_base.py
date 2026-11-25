"""Set a red-base hold under the task's step lock."""

from typing import TYPE_CHECKING

from lem.app.tasks import release
from lem.kernel import clock
from lem.model.task import red_base
from lem.store import places, steps, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.task import Task


def run(folder: Path, slug: str, after: str) -> Task:
    """The task with its hold set."""
    state = places.workspace(folder).state
    tasks.read(state, slug)
    now = clock.now()
    with steps.step(state, slug, "red-base", now):
        record = release.checked(state, slug)
        updated = red_base.blocked(record, tasks.read(state, after), now)
        if updated is record:
            return record.task
        return tasks.update(state, slug, lambda _: updated, record.revision).task
