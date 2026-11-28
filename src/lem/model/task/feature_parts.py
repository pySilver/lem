"""The parts of a feature, as the records name them: each task whose `Task.part_of` names it
(`docs/plans/2026-11-27-a-feature-in-parts.md`, section 3). The feature carries no key of its
own, so a task is a feature when a part names it.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from lem.records.task import Task


def parts_of(feature: Task, every: Iterable[Task]) -> tuple[Task, ...]:
    """Each task that names `feature` in `part_of`: those of its `after` in that order, then
    any other by when it opened."""
    found = [task for task in every if task.part_of == feature.slug]
    order = {slug: index for index, slug in enumerate(feature.after)}
    last = len(order)
    return tuple(
        sorted(
            found,
            key=lambda task: (order.get(task.slug, last), task.opened, task.slug),
        )
    )
