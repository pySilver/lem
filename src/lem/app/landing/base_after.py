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


def resolved_files(context: frame.Context, tip: Sha) -> tuple[str, ...]:
    """The files of a builder's resolution, once he rebased past the conflict: each file git's
    merge of the tip before the conflict onto the base meets a conflict in, so that a later
    commit's stop on another file is read too."""
    found = (context.record.landing or Landing()).resolution
    if found is None or found.after != found.before:
        return ()
    if found.before == tip:
        return ()
    merged = merged_of(context, found.before)
    return merged.files if isinstance(merged, Clash) else ()


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
        resolved=resolved_files(context, tip),
    )


def recovered(context: frame.Context) -> Sha | None:
    """The tip before a rebase a stop cut between the rebase and its record: the record's mark
    names it (`base_kept.marked`), git's `ORIG_HEAD` names it too, and the tip now is another
    commit. None otherwise, a builder's resolution of a conflict among them."""
    landing = context.record.landing or Landing()
    based, waiting = landing.based, landing.resolution
    if based is None or based.before != based.tip:
        return None
    if based.tip == context.world.tip:
        return None
    if waiting is not None and waiting.after == waiting.before:
        return None
    found = context.ports.git.tip(context.worktree, "ORIG_HEAD")
    return based.tip if found == based.tip else None
