"""A rebase of `base` that stopped and was undone: on files a builder resolves, or for a reason
no builder resolves (a hook of git, a lock), with what the abort left not as it was and the
command that puts each back (`land.rebase_failed` and `land.rebase_left` on `main`)."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.records.base import Frozen, Sha

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.record import Record


class Aborted(Frozen, frozen=True, kw_only=True):
    """The worktree after the abort, looked at and never taken on trust: whether a rebase is
    still in progress, the commit of the task's branch, the commit of HEAD, and the worktree's
    path."""

    rebasing: bool
    branch_tip: Sha | None
    head: Sha | None
    where: str


def left(world: World, aborted: Aborted) -> str:
    """What the abort left not as it was before the rebase, each with the command that puts it
    back, in the order they run; empty when the branch is at its tip and HEAD on it."""
    found = (
        still_rebasing(aborted),
        branch_moved(world, aborted),
        head_off(world, aborted),
    )
    return "; ".join(line for line in found if line)


def still_rebasing(aborted: Aborted) -> str:
    """A rebase the abort did not end, and how to end it."""
    if not aborted.rebasing:
        return ""
    return f"a rebase is still in progress (`git -C {aborted.where} rebase --abort`)"


def branch_moved(world: World, aborted: Aborted) -> str:
    """A branch the abort left at another commit than its tip before the rebase."""
    before, branch = world.tip, world.branch
    if aborted.branch_tip == before:
        return ""
    at = (aborted.branch_tip or "no commit")[:9]
    # on the branch, HEAD moves with a reset; off it, the branch is set by its name
    on = aborted.head is not None and aborted.head == aborted.branch_tip
    back = f"reset --hard {before}" if on else f"branch -f {branch} {before}"
    return (
        f"the branch {branch} is at {at}, not at its tip before the rebase {before} "
        f"(`git -C {aborted.where} {back}` puts it back)"
    )


def head_off(world: World, aborted: Aborted) -> str:
    """A HEAD the abort left off the branch: detached, or on another branch."""
    if aborted.head == aborted.branch_tip:
        return ""
    head = (aborted.head or "no commit")[:9]
    return (
        f"HEAD is at {head}, not on the branch {world.branch} "
        f"(`git -C {aborted.where} switch --force {world.branch}` puts it back)"
    )


def conflict(
    record: Record, world: World, files: tuple[str, ...], aborted: Aborted
) -> Refusal:
    """The refusal of a rebase that stopped on files: undone, the files named, for a builder
    to resolve in the worktree."""
    slug, named = record.task.slug, ", ".join(files)
    onto = world.rules.base
    still = left(world, aborted)
    why = f"the rebase onto origin/{onto} stopped on these file(s): {named}"
    if still:
        return Refusal(
            "conflict",
            f"{why}, and its abort left the worktree not as it was: {still}",
            f"nothing is kept for a builder: once it is put back, lem land base {slug} "
            "runs again",
        )
    return Refusal(
        "conflict",
        f"{why}; it was undone",
        f"a builder resolves it in the worktree (`git -C {aborted.where} rebase origin/{onto}`, "
        f"then each file), then lem land base {slug} runs again",
    )


def refused(record: Record, world: World, said: str, aborted: Aborted) -> Refusal:
    """The refusal of a rebase that git refused or stopped with no file in conflict: git's
    words, and where the worktree is after the abort. Nothing is kept for a builder."""
    slug, still = record.task.slug, left(world, aborted)
    where = (
        f"the worktree is not as it was: {still}"
        if still
        else "the worktree is as it was"
    )
    back = ", puts the worktree back as named," if still else ""
    onto = world.rules.base
    return Refusal(
        "git-refused",
        f"the rebase onto origin/{onto} failed with no file in conflict, and "
        f"{where}; git said: {said}",
        "nothing is kept for a builder: the owner removes what git names (a hook of git "
        f"that refuses the rebase, a lock that another git holds){back} and lem land base "
        f"{slug} runs again",
    )
