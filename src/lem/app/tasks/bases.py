"""The base a task starts from and lands on, for every reader before and after its landing's
first round (`docs/plans/2026-11-27-a-feature-in-parts.md`, "The base of a task").

Once a round started, the base is the one the landing recorded (`Started.base_ref`), so a change
of the settings cannot move a task's pull request. Before it, a part of a feature starts from the
feature's branch, and any other task from the settings' `branch.base`. A part is refused before
any worktree or push when its feature's record does not read, when the feature ended, and when
origin has no branch of the feature, also after a fetch (`model/task/part_of.py`). A part that
ended takes its feature's branch whether the feature ended or not, so that its clean-up runs.
"""

from typing import TYPE_CHECKING

from lem.app.tasks import ports, remote
from lem.kernel.errors import Fault, Refusal
from lem.model.landing import destination
from lem.model.task import part_of
from lem.settings.load import base_of, team_of
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git import Git
    from lem.records.record import Record
    from lem.records.task import Task
    from lem.store.places import Workspace


def chosen(git: Git, workspace: Workspace, record: Record) -> str:
    """The branch the task starts from and lands on: the recorded one, else its feature's
    branch for a part, else the settings' base."""
    recorded = destination.recorded(record.landing)
    if recorded is not None:
        return recorded
    if record.task.part_of is None:
        return base_of(team_of(workspace.checkout))
    return feature_branch(git, workspace, record.task)


def bound(workspace: Workspace, record: Record) -> str:
    """The task's base, with the git of the workspace bound for this call."""
    return chosen(ports.bound(workspace).git, workspace, record)


def feature_of(workspace: Workspace, part: str, feature: str) -> Task:
    """The feature's task, as its record reads now; refused when it does not read."""
    try:
        return tasks.read(workspace.state, feature).task
    except (Refusal, Fault) as error:
        raise part_of.unread(part, feature, str(error)) from error


def on_origin(git: Git, checkout: Path, part: str, feature: Task) -> str:
    """The feature's branch, when origin has it: as git last fetched it, else after a fetch
    of origin; refused when it is not there even then."""
    branch = feature.branch
    if branch is None:
        raise part_of.no_branch(part, feature)
    if git.remote_head(checkout, branch) is not None:
        return branch
    said = remote.fetch_warning(git, checkout)
    if git.remote_head(checkout, branch) is None:
        raise part_of.no_branch(part, feature, said)
    return branch


def feature_branch(git: Git, workspace: Workspace, part: Task) -> str:
    """The branch of the feature that the part `part` starts from and lands on. An ended part
    is looked at only to clean up after it, so its feature may have ended too."""
    feature = part_of.named(part)
    found = feature_of(workspace, part.slug, feature)
    refused = part_of.startable(part, found)
    if refused is not None:
        raise refused
    return on_origin(git, workspace.checkout, part.slug, found)
