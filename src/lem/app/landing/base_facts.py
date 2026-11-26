"""The facts `base` reads from git before its move, and after a rebase that stopped
(`model/landing/base.py`): what the tip has of its own, a teammate's commits on origin's task
branch, and the worktree after the abort."""

from typing import TYPE_CHECKING

from lem.model.landing import base, base_said
from lem.model.landing.base_stops import Aborted
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.app.landing import frame
    from lem.ports.git_facts import Commit
    from lem.records.base import Sha


def line_of(commit: Commit) -> str:
    """A commit as a refusal names it: its short sha and its subject."""
    short = commit.sha[:9]
    return f'{short} "{commit.subject}"'


def teammates(context: frame.Context, tip: Sha) -> tuple[str, ...]:
    """A teammate's commits on origin's task branch: each one the tip does not hold, origin's
    base does not hold and no push of Lem's held, as a line."""
    git, world, where = context.ports.git, context.world, context.workspace.checkout
    if world.remote is None or world.remote_in_tip:
        return ()
    pushed = (context.record.landing or Landing()).pushed
    held = tuple(sha for sha in (world.base, pushed) if sha)
    return tuple(
        line_of(commit)
        for commit in git.commits(where, tip, world.remote)
        if not any(git.is_ancestor(where, commit.sha, one) for one in held)
    )


def orig(context: frame.Context, tip: Sha) -> Sha | None:
    """The tip before the last rebase (git's `ORIG_HEAD`) while it holds a change origin's
    base lacks: what a rebase cut off before its record left of a change it dropped."""
    git, where, world = context.ports.git, context.worktree, context.world
    found = git.tip(where, "ORIG_HEAD")
    if found is None or found == tip:
        return None
    merged = git.merge_tree(where, world.base, found)
    return None if merged == world.base_tree else found


def dropped(context: frame.Context) -> bool:
    """Whether the tip is Lem's own unpublished rebase of a tip before it, and that rebase
    left out a commit of the change: git found its patch in the base it went onto."""
    git, where = context.ports.git, context.worktree
    based = (context.record.landing or Landing()).based
    first = base_said.remade(context.record, context.world)
    if first is None or based is None:
        return False
    fork = git.merge_base(where, first, based.base) or based.base
    return len(git.commits(where, fork, first)) != len(
        git.commits(where, based.base, based.tip)
    )


def before(context: frame.Context) -> base.Facts:
    """What `base` reads before it acts: the commits of the tip that origin's base lacks, a
    teammate's commits, the branch HEAD is on, and the tip before a rebase that a stop cut."""
    world, where = context.world, context.workspace.checkout
    tip = world.tip or world.base
    ahead = len(context.ports.git.commits(where, world.base, tip))
    return base.Facts(
        ahead=ahead,
        theirs=teammates(context, tip),
        on_branch=context.ports.git.branch_of(context.worktree) == world.branch,
        orig=None if ahead else orig(context, tip),
        dropped=dropped(context),
    )


def aborted(context: frame.Context) -> Aborted:
    """The worktree after a rebase that stopped was undone: a rebase still in progress, the
    branch's commit and HEAD's."""
    git, where, world = context.ports.git, context.worktree, context.world
    return Aborted(
        rebasing=git.rebase_state(where) is not None,
        branch_tip=git.tip(where, f"refs/heads/{world.branch}"),
        head=git.tip(where, "HEAD"),
        where=str(where),
        on=git.branch_of(where),
    )
