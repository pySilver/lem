"""What `start` refuses, each with its code, why and the fix that names the way on
(`landing.md` F, `start`; `land.start_locked` and `Task.need_worktree` on `main`)."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.records.holds import Blocked

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.record import Record

# Why `start` blocks a task whose project names no command of the checks: the one block it
# sets itself, and clears once the commands are there.
NO_CHECKS = "the project has no command in its checks"
WORKTREES = ".lem/worktrees"


def unready(record: Record, world: World) -> Refusal | None:
    """Why the worktree may not land as it is: gone, or with changes nobody committed."""
    slug = record.task.slug
    if world.tip is None:
        return Refusal(
            "no-worktree",
            f"the task has no worktree at {WORKTREES}/{slug}",
            f"in the main checkout, `git worktree prune` forgets a worktree whose folder was "
            f"removed by hand, and `git worktree add {WORKTREES}/{slug} {world.branch}` "
            f"puts the task's branch back in it; then this step runs again. When the work "
            f"is gone with it, `lem task move {slug} dropped` ends the task",
        )
    # a rebase in progress leaves the worktree unclean: `base` names it, a builder's own
    if not world.clean and not world.rebasing:
        return Refusal(
            "dirty",
            "the task's worktree has changes nobody committed",
            "the builder commits them or removes them, then this step runs again",
        )
    return None


def off_branch(record: Record, world: World) -> Refusal:
    """The refusal of a worktree whose HEAD is not the task's branch: a detached HEAD, or
    another branch."""
    slug = record.task.slug
    return Refusal(
        "off-branch",
        f"the task's worktree is not on its branch {world.branch}, which the landing "
        "pushes and deletes after the merge",
        f"`git -C {WORKTREES}/{slug} switch {world.branch}` in the main checkout puts it "
        "back on it, then this step runs again",
    )


def status(record: Record) -> Refusal:
    """The refusal of a task whose status starts no landing."""
    slug, now = record.task.slug, record.task.status
    return Refusal(
        "status",
        f"{slug} is {now}: only a ready task, or an open one whose base moved, starts a "
        "landing",
        f"lem task move {slug} ready, once its builder's change is committed",
    )


def not_open(record: Record) -> Refusal:
    """The refusal of `--conflicting` for a task that is not `open`."""
    slug, now = record.task.slug, record.task.status
    return Refusal(
        "status",
        f"--conflicting is for an open task whose pull request the forge calls "
        f"conflicting, and {slug} is {now}",
        f"lem land start {slug}, without --conflicting",
    )


def held(record: Record) -> Refusal | None:
    """The refusal of a task that a hold keeps where it is; the block for want of checks,
    which `start` set, is no refusal: `start` takes the task back."""
    hold, slug = record.task.hold, record.task.slug
    if hold is None or (isinstance(hold, Blocked) and hold.why == NO_CHECKS):
        return None
    fix = hold.fix if isinstance(hold, Blocked) else f"lem task show {slug} names it"
    kind = hold.__struct_config__.tag
    return Refusal("held", f"{slug} is held ({kind}): no landing starts", fix)


def no_checks(record: Record, *, own: tuple[str, ...]) -> Refusal:
    """The refusal of a task whose project names no command of the checks: the task is
    blocked until they are there. A branch that brings its own is the task that sets them
    up, whose landing the step `land-checks` builds."""
    slug = record.task.slug
    brought = ", ".join(own)
    also = (
        f"; this branch brings its own ({brought}), and the landing of a task that sets "
        "up the checks is not built yet: the step `land-checks` builds it"
        if own
        else ""
    )
    return Refusal(
        "no-checks",
        f"{NO_CHECKS}, so nothing would show that the change works; the task is "
        f"blocked{also}",
        "add the commands to checks.commands in .lem/settings.toml, or, for the task "
        f"that sets up the checks, in its own branch's; then lem land start {slug} again",
    )
