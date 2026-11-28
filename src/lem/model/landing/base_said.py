"""What `base` refuses before its rebase, each with its code, why and the fix that names the
way on (`landing.md` F, `base`; `land.cmd_base` and `Task.own_remote` on `main`)."""

import shlex
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing import start_said
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from lem.model.landing.base import Facts
    from lem.model.landing.world import World
    from lem.records.record import Record

# How many of a teammate's commits a refusal names, one line each; the rest are counted.
NAMED = 10


def in_progress(record: Record, where: str) -> Refusal:
    """The refusal of a worktree where a builder's own rebase is in progress: an abort of it
    would undo his work."""
    slug = record.task.slug
    return Refusal(
        "rebase-in-progress",
        f"a rebase is in progress in the worktree of {slug}, a builder's own: base starts "
        "no rebase over it and aborts none",
        f"the builder finishes it (`git -C {shlex.quote(where)} rebase --continue`) or ends it "
        f"(`git -C {shlex.quote(where)} rebase --abort`), then lem land base {slug} runs again",
    )


def merge_in_progress(record: Record, where: str) -> Refusal:
    """The refusal of a worktree where a merge is in progress: a builder's resolution of a
    conflict of the merge of origin's base, which an abort would delete."""
    slug, quoted = record.task.slug, shlex.quote(where)
    return Refusal(
        "merge-in-progress",
        f"a merge is in progress in the worktree of {slug}, a builder's resolution: base "
        "starts no merge over it and aborts none",
        f"the builder commits the resolution (`git -C {quoted} commit --no-edit`), then lem "
        f"land base {slug} runs again",
    )


def teammate(
    record: Record, world: World, theirs: tuple[str, ...], where: str
) -> Refusal:
    """The refusal of a task branch on origin that holds a commit Lem did not push, the tip
    does not hold and origin's base does not either: a push after the rebase would remove it.
    `theirs` names each such commit."""
    slug, branch = record.task.slug, world.branch
    left = len(theirs) - NAMED
    rest = f", and {left} more" if left > 0 else ""
    named = "; ".join(theirs[:NAMED])
    return Refusal(
        "teammate",
        f"origin's {branch} holds {len(theirs)} commit(s) that Lem did not push and the "
        f"task's branch does not hold: {named}{rest}. A push would remove them",
        f"`git -C {shlex.quote(where)} pull --rebase origin {branch}` brings them into the task's "
        f"branch; then lem land base {slug} runs again: they are part of the change, with "
        "its checks and a read",
    )


def remade(record: Record, world: World) -> str | None:
    """The tip before Lem's own rebase when the tip now is what that rebase made, with no
    commit after it, no conflict on the way and nobody's push or proposal of it; else
    None."""
    landing = record.landing or Landing()
    based, proposed = landing.based, landing.proposed
    if based is None or based.before == based.tip:
        return None
    if based.tip != world.tip:
        return None
    published = {landing.pushed, proposed.tip if proposed else None}
    if based.tip in published or landing.resolution is not None:
        return None
    return based.before


def again(record: Record, world: World, where: str) -> Refusal | None:
    """The refusal of a second rebase of the tip Lem's own rebase made and nobody published:
    git may have left a commit out of the first onto a base that held its edit, and a second
    rebase of what it left would lose that commit for good. `main` starts again from the tip
    before Lem's first rebase (`land.cmd_base`, `made`); the `Git` port has no act that moves
    a branch back yet (`notes/land-base.md`), so the owner's reset does."""
    before = remade(record, world)
    if before is None:
        return None
    slug = record.task.slug
    return Refusal(
        "rebase-again",
        f"the tip is the one Lem's rebase made of {before}, and origin's base moved again; "
        "a rebase of it would lose each commit git left out of the first",
        f"`git -C {shlex.quote(where)} reset --hard {before}` puts the branch back on the "
        f"tip before Lem's rebase, then lem land base {slug} rebases it once onto the base "
        "now",
    )


def blocked(record: Record, world: World, facts: Facts, where: str) -> Refusal | None:
    """Why `base` may not act on the worktree now: a builder's rebase in progress, a HEAD off
    the task's branch, or a teammate's commits on origin's task branch."""
    landing = record.landing or Landing()
    if world.rebasing:
        return in_progress(record, where)
    if world.merging:
        return merge_in_progress(record, where)
    if not facts.on_branch:
        return start_said.off_branch(record, world)
    foreign = (
        world.remote is not None
        and not world.remote_in_tip
        and world.remote != landing.pushed
    )
    if foreign and facts.theirs:
        return teammate(record, world, facts.theirs, where)
    return None
