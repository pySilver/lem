"""Where a sync of a feature stops in its worktree: no worktree, another branch, changes that no
commit holds, a history that went apart from origin's, a conflict, and a merge that git refused.

Each refusal names the feature, its branch and its worktree, and says that nothing was pushed;
the fix is a builder's in the worktree, then `lem task sync NAME` again.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, kw_only=True, slots=True)
class Place:
    """The feature's name, its branch, the base it takes in, and its worktree."""

    slug: str
    branch: str
    base: str
    worktree: Path

    @property
    def again(self) -> str:
        """The command that runs the sync again."""
        return f"then run lem task sync {self.slug} again"


def no_worktree(place: Place) -> Refusal:
    """The feature has no worktree."""
    return Refusal(
        "no-worktree",
        f"the feature {place.slug} has no worktree at {place.worktree}",
        f"lem task worktree {place.slug} makes it on {place.branch}, {place.again}",
    )


def off_branch(place: Place, on: str | None) -> Refusal:
    """The feature's worktree is on another branch."""
    shown = on or "a detached HEAD"
    return Refusal(
        "worktree",
        f"the worktree of {place.slug} is on {shown}, not on {place.branch}",
        f"check out {place.branch} in {place.worktree}, {place.again}",
    )


def dirty(place: Place) -> Refusal:
    """The worktree holds changes that no commit holds, or a merge not yet committed."""
    return Refusal(
        "dirty",
        f"the worktree of {place.slug} has changes that no commit holds, or a merge that is "
        "not committed yet; nothing was pushed",
        f"a builder commits the resolution of the merge (git commit) or takes the changes "
        f"out in {place.worktree}, {place.again}",
    )


def diverged(place: Place) -> Refusal:
    """The worktree and origin's branch each hold commits the other lacks."""
    branch = place.branch
    return Refusal(
        "diverged",
        f"the worktree of {place.slug} holds commits that origin's {branch} lacks, and "
        f"origin's {branch} moved since; nothing was pushed",
        f"a builder merges origin/{branch} into {branch} in {place.worktree} "
        f"(git merge origin/{branch}), {place.again}",
    )


def conflict(place: Place, files: tuple[str, ...]) -> Refusal:
    """The merge of origin's base stopped on a conflict, which waits for a builder."""
    shown = ", ".join(files)
    return Refusal(
        "conflict",
        f"the merge of origin/{place.base} into {place.branch} stopped on a conflict in "
        f"{shown}; nothing was pushed",
        f"a builder resolves the conflict in {place.worktree} and commits the merge (git "
        f"commit), {place.again}",
    )


def refused(place: Place, act: str, said: str) -> Refusal:
    """Git refused an act of the sync in the worktree: its words."""
    return Refusal(
        "git",
        f"git refused the {act} in the worktree of {place.slug}: {said}; nothing was pushed",
        f"a builder clears what git names in {place.worktree}, {place.again}",
    )
