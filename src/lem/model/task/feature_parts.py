"""The parts of a feature, as the records name them: each task whose `Task.part_of` names it
(`docs/plans/2026-11-27-a-feature-in-parts.md`, section 3). The feature carries no key of its
own, so a task is a feature when a part names it. A part that went on in a resumed part, which
its feature's `after` holds too, is waited for no more: the resumed part is waited for in its
place, and no owner's word is needed for the one that was dropped.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

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


def went_on(task: Task, every: Iterable[Task]) -> frozenset[str]:
    """The tasks of `task.after` that a task also in its `after` went on from: a part of a
    feature resumed as another part, which the feature waits for in its place."""
    after = frozenset(task.after)
    return frozenset(
        one.resumed_from
        for one in every
        if one.slug in after and one.resumed_from in after
    )


def dropped_before(task: Task, tasks: Mapping[str, Task]) -> tuple[Task, ...]:
    """Each dropped task the queued `task` waits for, but one that went on in another task
    of its `after` (`went_on`)."""
    gone = went_on(task, tasks.values())
    predecessors = map(tasks.get, dict.fromkeys(task.after))
    return tuple(
        one
        for one in predecessors
        if one is not None and one.status == "dropped" and one.slug not in gone
    )
