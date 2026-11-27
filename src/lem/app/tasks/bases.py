"""The base a task starts from and lands on, for every reader before and after its landing's
first round (`docs/plans/2026-11-27-a-feature-in-parts.md`, "The base of a task").

Once a round started, the base is the one the landing recorded (`Started.base_ref`), so a change
of the settings cannot move a task's pull request. Before it, a part of a feature starts from the
feature's branch, and any other task from the settings' `branch.base`. A part is refused before
any worktree or push when its feature's record does not read, when the feature ended, and when
origin has no branch of the feature, as git last fetched it (`model/task/part_of.py`).
"""

from typing import TYPE_CHECKING

from lem.app.tasks import ports
from lem.kernel.errors import Fault, Refusal
from lem.model.landing import destination
from lem.model.task import part_of
from lem.settings.load import base_of, team_of
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git import GitFacts
    from lem.records.record import Record
    from lem.store.places import Workspace


def chosen(git: GitFacts, workspace: Workspace, record: Record) -> str:
    """The branch the task starts from and lands on: the recorded one, else its feature's
    branch for a part, else the settings' base."""
    recorded = destination.recorded(record.landing)
    if recorded is not None:
        return recorded
    feature = record.task.part_of
    if feature is None:
        return base_of(team_of(workspace.checkout))
    return feature_branch(git, workspace, record.task.slug, feature)


def bound(workspace: Workspace, record: Record) -> str:
    """The task's base, with the git of the workspace bound for this call."""
    return chosen(ports.bound(workspace).git, workspace, record)


def on_origin(git: GitFacts, checkout: Path, branch: str | None) -> bool:
    """Whether origin has `branch`, as git last fetched it."""
    return branch is not None and git.remote_head(checkout, branch) is not None


def feature_branch(git: GitFacts, workspace: Workspace, part: str, feature: str) -> str:
    """The branch of the feature `feature` that its part `part` starts from."""
    try:
        found = tasks.read(workspace.state, feature).task
    except (Refusal, Fault) as error:
        raise part_of.unread(part, feature, str(error)) from error
    refused = part_of.startable(part, found)
    if refused is not None:
        raise refused
    if found.branch is None or not on_origin(git, workspace.checkout, found.branch):
        raise part_of.no_branch(part, found)
    return found.branch
