"""`clean`: what a landed task leaves goes: its worktree, its branch and the forge's copy of it
(`landing.md` B, `merged` to `ended`; E, "Clean, landed").

The local branch goes when origin's base holds its tip or its tip is the head the forge merged;
the forge's copy goes only at that head. A divergent local branch, a dropped or answered task and
the rebase after Lem's last push are the step `land-merge`'s.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing.invariants import protected
from lem.model.landing.world import World, later
from lem.records.base import Frozen
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.records.landing.merge import Merged
    from lem.records.record import Record


class Sweep(Frozen, frozen=True, kw_only=True):
    """What `clean` removes: the worktree, the local branch, the forge's copy, and the line
    for a branch it keeps."""

    worktree: bool
    branch: bool
    remote: bool
    branch_left: str | None = None


def branch_goes(world: World, merged: Merged) -> bool:
    """Whether the local branch holds nothing the forge did not merge."""
    return world.local is not None and (
        world.local_in_base or world.local == merged.merged_head
    )


def swept(world: World, merged: Merged) -> Sweep:
    """What goes of what is there now."""
    left = None
    if world.local is not None and not branch_goes(world, merged):
        left = (
            f"{world.branch} is at {world.local}, which the forge did not merge: it stays "
            f"(git branch -D {world.branch} removes it)"
        )
    return Sweep(
        worktree=world.tip is not None,
        branch=branch_goes(world, merged),
        remote=world.remote == merged.merged_head,
        branch_left=left,
    )


def decide(record: Record, world: World) -> Refusal | Sweep:
    """What goes, or why nothing may go now."""
    slug, status = record.task.slug, record.task.status
    merged = (record.landing or Landing()).merged
    if status != "landed" or merged is None:
        return later(f"the cleanup of a task that is {status}", "land-merge")
    guard = protected(world.branch, world.rules, "deletes")
    if guard is not None:
        return guard
    if world.tip is not None and not world.clean:
        return Refusal(
            "dirty",
            f"the worktree of {slug} has changes or files of its own",
            "the owner keeps or removes them, then lem land clean runs again",
        )
    return swept(world, merged)
