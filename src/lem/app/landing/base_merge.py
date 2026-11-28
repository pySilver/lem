"""The move of `base` for a feature: origin's base merged into its branch by a merge commit, as
its sync merges it (`app/tasks/sync_tip.py`), never a rebase, which drops the merge commits of
its parts and of its syncs (`docs/plans/2026-11-27-a-feature-in-parts.md`, "The end").

A conflict stays in the worktree for a builder, who commits the merge; a merge git refuses
leaves nothing. What the merge kept of the change, and whether the review carries over it, is
judged as after a rebase (`base_after.py`), with no rebase to compare.
"""

from typing import TYPE_CHECKING

from lem.app.landing import base_after
from lem.model.landing import feature_said
from lem.model.task import sync
from lem.ports.git_facts import Conflict, GitRefused

if TYPE_CHECKING:
    from lem.app.landing import frame
    from lem.model.landing import base


def merged_in(context: frame.Context) -> base.After:
    """Merge origin's base, by the commit the world read, into the worktree's branch with a
    merge commit; give the facts after it."""
    world, where = context.world, context.worktree
    message = sync.message(world.rules.base, world.branch)
    made = context.ports.git.merge(where, world.base, message)
    if isinstance(made, Conflict):
        raise feature_said.merge_conflict(context.record, world, made.files, str(where))
    if isinstance(made, GitRefused):
        raise feature_said.merge_refused(context.record, world, made.said)
    return base_after.after(context, made, None)
