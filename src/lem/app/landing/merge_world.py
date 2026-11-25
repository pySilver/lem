"""What the merge's steps read from git and the forge beyond the world: the trees a merge is
judged by, the queue's end, and the facts of a branch the cleanup decides on (`landing.md` D and
E)."""

from typing import TYPE_CHECKING

from lem.model.landing.clean import Facts, Rebased
from lem.model.landing.reconcile import Trees

if TYPE_CHECKING:
    from lem.app.landing.frame import Context
    from lem.model.landing.world import PullSeen
    from lem.records.base import Sha
    from lem.records.landing.merge import Merged


# The local branch of a name.
LOCAL = "refs/heads/{0}"


def checks_tree(context: Context) -> Sha:
    """The tree of the base the checks ran on; origin's base tree when no checks ran."""
    checked = context.record.landing.checked if context.record.landing else None
    if checked is None:
        return context.world.base_tree
    return context.ports.git.tree(context.workspace.checkout, checked.base)


def trees_of(context: Context, pull: PullSeen | None) -> Trees:
    """The trees a merge is judged by: of the checks' base, and of the commit of the base the
    forge's merge went onto (the checks' tree while the forge reports none, or the merge went
    into another branch, which is no landing)."""
    checks = checks_tree(context)
    parent = None if pull is None else pull.base_parent
    into = pull is not None and pull.base == context.world.rules.base
    if parent is None or not into:
        return Trees(checks=checks, parent=checks)
    tree = context.ports.git.tree(context.workspace.checkout, parent)
    return Trees(checks=checks, parent=tree)


def rebase_proof(context: Context, local: Sha, head: Sha) -> Rebased:
    """Whether the merged `head`'s change, merged onto the tip's own base, gives the tree of
    the branch's tip `local` (`main:land.after_push`): a patch id is no proof, a tree is."""
    git, checkout = context.ports.git, context.workspace.checkout
    base_tip = git.merge_base(checkout, local, context.world.base) or context.world.base
    base_merged = git.merge_base(checkout, head, base_tip) or base_tip
    same = git.merge_tree(checkout, base_tip, head) == git.tree(checkout, local)
    return Rebased(same=same, base_tip=base_tip, base_merged=base_merged)


def branch_facts(context: Context, merged: Merged | None, *, asks: bool) -> Facts:
    """What git says of the task's local branch for its cleanup: whether the local base branch
    holds its tip, how it stands to the merged head, and, when `asks`, the proof of a rebase
    after Lem's last push."""
    git, checkout, local = (
        context.ports.git,
        context.workspace.checkout,
        context.world.local,
    )
    if local is None:
        return Facts()
    ref = LOCAL.format(context.world.rules.base)
    in_local = git.is_ancestor(checkout, local, ref)
    if merged is None:
        return Facts(in_local_base=in_local)
    return Facts(
        in_local_base=in_local,
        after_merged=git.is_ancestor(checkout, merged.merged_head, local),
        inside_merged=git.is_ancestor(checkout, local, merged.merged_head),
        rebased=rebase_proof(context, local, merged.merged_head) if asks else None,
    )


def dequeued_of(context: Context) -> str | None:
    """The forge's word for a pull request it took out of its merge queue, and why; asked
    only of an open request that waits in no queue, where the world's view of it holds
    none."""
    pull, landing = context.world.pull, context.record.landing
    if pull is None or pull.state != "open" or pull.queued or landing is None:
        return None
    return context.ports.forge.pull(pull.number).dequeued
