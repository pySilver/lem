"""The facts `base` reads from git after its move (`model/landing/base.py`): the tip and tree
it left, git's merges that show what a rebase kept and whether the review carried, and the
polish pass's last commit by its new name."""

from typing import TYPE_CHECKING

from lem.model.landing import base, carry
from lem.model.landing.rebased import Clash
from lem.ports.git_facts import Conflict
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.app.landing import frame
    from lem.model.landing.rebased import Merged
    from lem.records.base import Sha


def merged_of(context: frame.Context, tip: Sha | None) -> Merged:
    """git's merge of `tip` onto origin's base, its conflict as a clash; None for no tip."""
    if tip is None:
        return None
    made = context.ports.git.merge_tree(context.worktree, context.world.base, tip)
    return Clash(files=made.files) if isinstance(made, Conflict) else made


def polish(context: frame.Context, tip: Sha) -> Sha | None:
    """The polish pass's last commit by its name on the tip a rebase made: the commit as far
    from the tip as it was from the tip before. None when it needs no new name or is not in
    the tip before."""
    git, start = context.ports.git, context.world.tip
    polished = (context.record.landing or Landing()).polished
    last = polished.after if polished else None
    if last is None or start is None or start == tip:
        return None
    if not git.is_ancestor(context.worktree, last, start):
        return None
    count = len(git.commits(context.worktree, last, start))
    return git.tip(context.worktree, f"{tip}~{count}")


def differ_of(context: frame.Context, merged: Merged, tree: Sha) -> tuple[str, ...]:
    """The paths where `tree` differs from the tree of git's merge, when the merge was clean."""
    if not isinstance(merged, str) or merged == tree:
        return ()
    return context.ports.git.diff_stat(context.worktree, merged, tree).paths


def reviewed_of(context: frame.Context, tip: Sha) -> Merged:
    """git's merge of the newest reviewed tip onto the base, when a review read another tip."""
    review = carry.newest(context.record.landing or Landing())
    if review is None or review.tip == tip:
        return None
    return merged_of(context, review.tip)


def after(context: frame.Context, tip: Sha, merged: Merged) -> base.After:
    """The facts after the move to `tip`: its tree, what it has of its own, where its tree
    differs from git's merge of the tip before onto the base, and git's merge of the newest
    reviewed tip onto the base."""
    git, where = context.ports.git, context.worktree
    tree = git.tree(where, tip)
    return base.After(
        tip=tip,
        tree=tree,
        ahead=len(git.commits(where, context.world.base, tip)),
        merged=merged,
        differ=differ_of(context, merged, tree),
        reviewed=reviewed_of(context, tip),
    )
