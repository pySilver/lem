"""`clean`: what a task that ended leaves goes, and the landing ends (`landing.md` B, `merged`
to `ended`; E, "Clean, landed", "Clean, the forge's copy", "Clean, dropped or answered",
"Clean, dirty"; `main:land.cmd_clean`, `after_push`, `drop_forge_copy`).

A landed task's local branch goes when origin's base holds its tip, its tip is the head the
forge merged, or its tip holds that head's change rebased after Lem's last push; a branch that
differs from it after such a rebase stays, with the commands that show and remove it; a tip the
forge did not merge keeps the branch and the forge's copy, and the cleanup is refused. The
forge's copy goes only at the head the forge merged. A dropped or answered task's branch goes
only when a base holds its tip: else it holds the task's commits, which are the owner's.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.landing import merge_lines
from lem.model.landing.invariants import protected
from lem.records.base import Frozen, Sha
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.landing.merge import Merged
    from lem.records.record import Record


class Rebased(Frozen, frozen=True, kw_only=True):
    """The proof for a branch rebased after Lem's last push: whether the merged head's change,
    merged onto the tip's own base, gives the tip's tree, and the two bases."""

    same: bool
    base_tip: Sha
    base_merged: Sha


class Facts(Frozen, frozen=True, kw_only=True):
    """What git says of the local branch beyond the world: whether the local base branch
    holds its tip, whether it holds the merged head (commits after it) or the merged head
    holds it (a commit made on the forge after it), and the rebase's proof when it was
    asked."""

    in_local_base: bool = False
    after_merged: bool = False
    inside_merged: bool = False
    rebased: Rebased | None = None


class Sweep(Frozen, frozen=True, kw_only=True):
    """What `clean` removes: the worktree, the local branch, the forge's copy at the merged
    head, the line for a branch it keeps, and the line of a branch rebased after its push."""

    worktree: bool
    branch: bool
    remote: Sha | None = None
    branch_left: str | None = None
    rebased: str | None = None


def asks_rebase(world: World, merged: Merged, pushed: Sha | None) -> bool:
    """Whether the rebase's proof decides the local branch: its tip is neither on the base
    nor the merged head, and the forge merged the head Lem pushed last."""
    local = world.local
    plain = local is None or world.local_in_base or local == merged.merged_head
    return not plain and merged.merged_head == pushed


def landed(
    world: World, merged: Merged, facts: Facts, pushed: Sha | None
) -> Refusal | Sweep:
    """What goes of a landed task's branches (`pushed`: the head Lem pushed last)."""
    local, rebased = world.local, facts.rebased
    head = merged.merged_head
    sweep = Sweep(
        worktree=world.tip is not None,
        branch=local is not None,
        remote=head if world.remote == head else None,
    )
    if local is None or world.local_in_base or local == head:
        return sweep
    apart = not (facts.after_merged or facts.inside_merged)
    if apart and rebased is not None and asks_rebase(world, merged, pushed):
        said = merge_lines.after_push(
            world.branch,
            (local, head),
            (rebased.base_tip, rebased.base_merged),
            same=rebased.same,
        )
        if rebased.same:
            return replace(sweep, rebased=said)
        return replace(sweep, branch=False, branch_left=said)
    return Refusal(
        "unmerged",
        merge_lines.unmerged_why(
            world.rules.base,
            (world.branch, local),
            after=facts.after_merged,
            inside=facts.inside_merged,
        ),
        f"git log {world.branch} shows what it holds, and git branch -D {world.branch} "
        "removes it; then lem land clean runs again",
    )


def ended(record: Record, world: World, facts: Facts) -> Sweep:
    """What goes of a dropped or answered task: its worktree, and its branch only when a base
    holds its tip; the forge's copy and its pull request stay for the owner."""
    local, branch = world.local, world.branch
    if local is None or world.local_in_base or facts.in_local_base:
        return Sweep(worktree=world.tip is not None, branch=local is not None)
    held = (
        "the dropped task's commits"
        if record.task.status == "dropped"
        else "the answered task's commits, the test that reproduced its bug among them"
    )
    left = f"{branch} holds {held}; git branch -D {branch} deletes them"
    return Sweep(worktree=world.tip is not None, branch=False, branch_left=left)


def decide(record: Record, world: World, facts: Facts) -> Refusal | Sweep:
    """What goes, or why nothing may go now: a protected branch, a worktree with changes or
    files of its own, a landed branch the forge did not merge."""
    slug, status = record.task.slug, record.task.status
    landing = record.landing or Landing()
    guard = protected(world.branch, world.rules, "deletes")
    if guard is not None:
        return guard
    if world.tip is not None and not world.clean:
        return Refusal(
            "dirty",
            f"the worktree of {slug} has changes or files of its own: nothing was removed",
            f"the owner keeps or removes them, then lem land clean {slug} runs again",
        )
    if status != "landed":
        return ended(record, world, facts)
    if landing.merged is None:
        return Refusal(
            "unmerged", f"{slug} has no merge on record", f"lem land next {slug}"
        )
    return landed(world, landing.merged, facts, landing.pushed)
