"""What `base` refuses before its rebase, each with its code, why and the fix that names the
way on (`landing.md` F, `base`; `land.cmd_base` and `Task.own_remote` on `main`)."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.model.landing.world import World
    from lem.records.landing.start import Based
    from lem.records.record import Record

# How many of a teammate's commits a refusal names, one line each; the rest are counted.
NAMED = 5


def in_progress(record: Record, where: str) -> Refusal:
    """The refusal of a worktree where a builder's own rebase is in progress: an abort of it
    would undo his work."""
    slug = record.task.slug
    return Refusal(
        "rebase-in-progress",
        f"a rebase is in progress in the worktree of {slug}, a builder's own: base starts "
        "no rebase over it and aborts none",
        f"the builder finishes it (`git -C {where} rebase --continue`) or ends it "
        f"(`git -C {where} rebase --abort`), then lem land base {slug} runs again",
    )


def teammate(
    record: Record, world: World, theirs: tuple[str, ...], where: str
) -> Refusal:
    """The refusal of a task branch on origin that holds a commit Lem did not push and the
    tip does not hold: a push after the rebase would remove it."""
    slug, branch = record.task.slug, world.branch
    named = "; ".join(theirs[:NAMED]) or str(world.remote)
    rest = more(len(theirs))
    count = len(theirs) or 1
    return Refusal(
        "teammate",
        f"origin's {branch} holds {count} commit(s) that Lem did not push and "
        f"the task's branch does not hold: {named}{rest}. A push would remove them",
        f"`git -C {where} pull --rebase origin {branch}` brings them into the task's "
        f"branch; then lem land base {slug} runs again: they are part of the change, with "
        "its checks and a read",
    )


def more(count: int) -> str:
    """The count of a teammate's commits a refusal does not name, as the end of its list."""
    left = count - NAMED
    return f", and {left} more" if left > 0 else ""


def lost(
    record: Record, world: World, based: Based | None, where: str
) -> Refusal | None:
    """The refusal of a rebase that left the branch no commit of its own while it could not
    show that it kept the change: the change sat only in a merge commit, which a rebase drops.
    None when no rebase of this base made the tip so."""
    if based is None or based.tip != world.tip:
        return None
    if based.before == based.tip or not based.unshown_paths:
        return None
    slug, paths = record.task.slug, ", ".join(based.unshown_paths)
    onto = world.rules.base
    return Refusal(
        "merge-only",
        f"the rebase onto origin/{onto} left the branch no commit of its own, "
        f"and the change in {paths} sat only in a merge commit, which a rebase drops. The "
        f"branch was at {based.before} before it",
        f"`git -C {where} reset --hard {based.before}` puts it back; the change goes into a "
        f"commit of its own, which a rebase keeps, then lem land base {slug} runs again. "
        f"When the work reached the base another way, lem task move {slug} dropped ends "
        "the task",
    )


def nothing(record: Record) -> Refusal:
    """The refusal of a branch with no commit that origin's base lacks."""
    slug = record.task.slug
    return Refusal(
        "nothing-to-land",
        "the branch has no commit that origin's base lacks: there is nothing to land",
        f"when the work reached the base another way, or there is none, lem task move "
        f"{slug} dropped ends the task",
    )
