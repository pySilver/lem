"""`lem task open --part-of NAME`: a part joins its feature.

The feature NAME must be a task that is `queued`, is no part itself and has its branch on origin
(`model/task/part_of.py`). Before the workspace lock, its branch is looked for on origin, after a
fetch when git has not seen it. Under the lock, the part's slug goes into NAME's `after` first,
under NAME's own task lock and on NAME's record as it is then, so that no other write of NAME is
lost or makes this one stale; the part's record is published after it. A run cut off between the
two leaves NAME waiting for a task with no record, which holds NAME `queued` (`model/task/
behind.py`), and its retry publishes the part.
"""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.tasks import bases, ports
from lem.kernel import locks, release
from lem.model.task import part_of
from lem.store import guard, places, tasks

if TYPE_CHECKING:
    from lem.app.tasks.opening import Asked
    from lem.records.record import Record
    from lem.records.task import Task


def fetched(workspace: places.Workspace, asked: Asked) -> str | None:
    """Before the workspace lock: the branch of the feature the new task `asked` joins, seen
    on origin; None for a task that is no part."""
    feature = asked.part_of
    if feature is None:
        return None
    found = bases.feature_of(workspace, asked.slug, feature)
    refused = part_of.joinable(asked.slug, found)
    if refused is not None:
        raise refused
    git = ports.bound(workspace).git
    return bases.on_origin(git, workspace.checkout, asked.slug, found)


def held(part: str, feature: Task, branch: str) -> None:
    """Refuse the join when the feature, as it is under its lock, may no longer take a part,
    or no longer holds the branch seen on origin."""
    refused = part_of.joinable(part, feature)
    if refused is not None:
        raise refused
    if feature.branch != branch:
        raise part_of.no_branch(part, feature)


def waits_for(record: Record, *, part: str) -> Record:
    """The feature's record, waiting for `part` too."""
    task = record.task
    return replace(record, task=replace(task, after=(*task.after, part)))


def added(workspace: places.Workspace, part: str, feature: str, branch: str) -> None:
    """Put `part` into the `after` of `feature` once, under the feature's own task lock, after
    the checks of `held` on its record as it is then."""
    state = workspace.state
    guard.writable(state)
    folder = places.task_folder(state, feature)
    with locks.held(folder / tasks.LOCK):
        record = tasks.read(state, feature)
        if part in record.task.after:
            return
        held(part, record.task, branch)
        tasks.writable(record, release.running())
        tasks.update_held(folder, record, partial(waits_for, part=part))


def joined(
    workspace: places.Workspace, task: Task, asked: Asked, branch: str | None
) -> None:
    """The part `task`, new or found again after a cut, joins the feature `asked` names, with
    the branch `fetched` gave; nothing for a task that is no part."""
    if branch is None or task.part_of is None or task.part_of != asked.part_of:
        return
    added(workspace, task.slug, task.part_of, branch)


def waiting(every: tuple[Record, ...], task: Task) -> bool:
    """Whether nothing is left to write for the task found again: it is no part, or its
    feature waits for it already."""
    if task.part_of is None:
        return True
    features = (one.task for one in every if one.task.slug == task.part_of)
    return any(task.slug in found.after for found in features)
