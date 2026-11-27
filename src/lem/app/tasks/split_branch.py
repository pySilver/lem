"""The feature's branch of a split: `feature/NAME` in the feature's worktree, cut from origin's
base after a fetch (`worktree.py`), and pushed to origin, so that each part is cut from it
(`bases.py`).

A worktree that is there is taken as it is, and a branch origin has already is not pushed again:
a split run again after a cut makes only what is missing.
"""

from typing import TYPE_CHECKING

from lem.app.tasks import heads, ports, worktree
from lem.kernel.errors import Refusal
from lem.ports.git_facts import GitRefused
from lem.records.base import Frozen
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.store.places import Workspace

PREFIX = "feature/"


class Branched(Frozen, frozen=True, kw_only=True):
    """The feature's branch and worktree, whether this call made the worktree and pushed the
    branch, and the line the cut said when origin did not answer."""

    branch: str
    worktree: str
    made: bool = False
    pushed: bool = False
    said: str | None = None


def pushed(workspace: Workspace, path: Path, branch: str) -> bool:
    """Push the branch's tip to origin when origin has no such branch; whether it pushed."""
    git = ports.bound(workspace).git
    if git.remote_head(workspace.checkout, branch) is not None:
        return False
    tip = git.tip(workspace.checkout, heads.HEADS + branch)
    sent = None
    if tip is not None:
        sent = git.push(path, branch, None, commit=tip)
    if sent is None or isinstance(sent, GitRefused):
        why = "git has no commit on it" if sent is None else sent.said
        raise Refusal(
            "push",
            f"the feature's branch {branch} did not reach origin: {why}",
            "correct what git says, then run lem task split again: it makes only what is "
            "missing",
        )
    return True


def branched(workspace: Workspace, slug: str) -> Branched:
    """The feature's worktree on `feature/NAME`, and that branch on origin."""
    record = tasks.read(workspace.state, slug)
    branch = PREFIX + slug
    made = worktree.made(ports.bound(workspace), workspace, record, (branch, None))
    path = worktree.where.worktree(workspace, slug)
    return Branched(
        branch=branch,
        worktree=made.worktree,
        made=made.made,
        pushed=pushed(workspace, path, branch),
        said=made.said,
    )
