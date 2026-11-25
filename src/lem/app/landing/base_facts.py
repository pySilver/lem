"""The facts `base` reads from git before its move, and after a rebase that stopped
(`model/landing/base.py`): what the tip has of its own, a teammate's commits on origin's task
branch, and the worktree after the abort."""

from typing import TYPE_CHECKING

from lem.model.landing import base
from lem.model.landing.base_stops import Aborted

if TYPE_CHECKING:
    from lem.app.landing import frame
    from lem.ports.git_facts import Commit
    from lem.records.base import Sha


def line_of(commit: Commit) -> str:
    """A commit as a refusal names it: its short sha and its subject."""
    short = commit.sha[:9]
    return f'{short} "{commit.subject}"'


def teammates(context: frame.Context, tip: Sha) -> tuple[str, ...]:
    """A teammate's commits on origin's task branch: each one the tip does not hold and
    origin's base does not either, as a line."""
    git, world, where = context.ports.git, context.world, context.workspace.checkout
    if world.remote is None or world.remote_in_tip:
        return ()
    found = git.commits(where, tip, world.remote)
    return tuple(
        line_of(commit)
        for commit in found
        if not git.is_ancestor(where, commit.sha, world.base)
    )


def before(context: frame.Context) -> base.Facts:
    """The commits of the tip that origin's base lacks, and a teammate's commits."""
    world, where = context.world, context.workspace.checkout
    tip = world.tip or world.base
    ahead = len(context.ports.git.commits(where, world.base, tip))
    return base.Facts(ahead=ahead, theirs=teammates(context, tip))


def aborted(context: frame.Context) -> Aborted:
    """The worktree after a rebase that stopped was undone: a rebase still in progress, the
    branch's commit and HEAD's."""
    git, where, world = context.ports.git, context.worktree, context.world
    return Aborted(
        rebasing=git.rebase_state(where) is not None,
        branch_tip=git.tip(where, f"refs/heads/{world.branch}"),
        head=git.tip(where, "HEAD"),
        where=str(where),
    )
