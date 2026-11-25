"""`lem land base`: the task's branch onto origin's base, by a plain rebase when the tip does
not hold it. A rebase that stops on files or that git refuses is undone, and nothing of it is
kept."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import changes, frame, step
from lem.kernel.errors import Refusal
from lem.model.landing import base
from lem.model.landing.world import later
from lem.ports.git_facts import Conflict, GitRefused
from lem.records.landing.start import Based

if TYPE_CHECKING:
    from pathlib import Path

    from lem.kernel.envelope import Envelope


def stopped(context: frame.Context, made: Conflict | GitRefused) -> Refusal:
    """Undo a rebase that stopped, and give its refusal."""
    git, worktree = context.ports.git, context.worktree
    if git.rebase_state(worktree) is not None:
        git.abort(worktree)
    if isinstance(made, Conflict):
        files = ", ".join(made.files)
        return later(f"the repair of a conflict with the base in {files}", "land-base")
    return Refusal(
        "git-refused",
        f"git refused the rebase: {made.said}; nothing was kept",
        "the owner removes what git names, then lem land base runs again",
    )


def rebased(context: frame.Context) -> str:
    """Rebase the worktree onto origin's base, and give the new tip."""
    named = context.world.rules.base
    made = context.ports.git.rebase(context.worktree, f"origin/{named}", reapply=False)
    if not isinstance(made, str):
        raise stopped(context, made)
    return made


def act(context: frame.Context) -> Based:
    """Bring the tip onto origin's base when it does not hold it, and record where it is."""
    world = context.world
    move = base.decide(context.record, world)
    if isinstance(move, Refusal):
        raise move
    before = world.tip or ""
    tip = rebased(context) if move == "rebase" else before
    based = Based(
        tip=tip,
        base=world.base,
        before=before,
        carried=False,
        at=world.now,
    )
    context.write(context.record, partial(changes.landing, based=based))
    return based


def run(folder: Path, slug: str) -> Envelope:
    """`lem land base SLUG`."""
    return step.landed(folder, slug, "base", act)
