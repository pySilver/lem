"""`lem task open --part-of NAME`: a part joins its feature under the workspace lock.

The feature NAME must be a task that is `queued`, is no part itself and has its branch on origin
(`model/task/part_of.py`). The new part's slug goes into NAME's `after`, so the feature waits for
it as for each of its parts. A run cut off after the part's record and before the feature's write
is a retry of the same words, which writes what is missing.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.tasks import bases, ports
from lem.kernel.errors import Refusal
from lem.model.task import part_of
from lem.store import tasks

if TYPE_CHECKING:
    from lem.app.tasks.opening import Asked
    from lem.records.record import Record
    from lem.records.task import Task
    from lem.store.places import Workspace


def feature_of(every: tuple[Record, ...], part: str, feature: str) -> Record:
    """The record of the feature `feature` among `every`; refused when there is none."""
    found = next((one for one in every if one.task.slug == feature), None)
    if found is None:
        raise Refusal(
            part_of.CODE,
            f"no task {feature} here, so {part} cannot be a part of it",
            "lem task list names the tasks",
        )
    return found


def checked(
    workspace: Workspace, every: tuple[Record, ...], part: str, feature: str
) -> Record:
    """The feature a new part may join: a task that is queued, is no part, and has its branch
    on origin, as git last fetched it."""
    found = feature_of(every, part, feature)
    refused = part_of.joinable(part, found.task)
    if refused is not None:
        raise refused
    git = ports.bound(workspace).git
    if not bases.on_origin(git, workspace.checkout, found.task.branch):
        raise part_of.no_branch(part, found.task)
    return found


def joinable(
    workspace: Workspace, every: tuple[Record, ...], asked: Asked
) -> Record | None:
    """The feature the new task `asked` joins as a part, checked; None for a task that is no
    part."""
    if asked.part_of is None:
        return None
    return checked(workspace, every, asked.slug, asked.part_of)


def waits_for(record: Record, *, part: str) -> Record:
    """The feature's record, waiting for `part` too."""
    task = record.task
    if part in task.after:
        return record
    return replace(record, task=replace(task, after=(*task.after, part)))


def added(workspace: Workspace, feature: Record, part: str) -> None:
    """Under the workspace lock, put `part` into the `after` of the checked `feature`."""
    change = partial(waits_for, part=part)
    tasks.update(workspace.state, feature.task.slug, change, feature.revision)


def joined(workspace: Workspace, every: tuple[Record, ...], task: Task) -> None:
    """Under the workspace lock, put the part `task` into its feature's `after`, once."""
    feature = task.part_of
    if feature is None:
        return
    if task.slug in feature_of(every, task.slug, feature).task.after:
        return
    added(workspace, checked(workspace, every, task.slug, feature), task.slug)
