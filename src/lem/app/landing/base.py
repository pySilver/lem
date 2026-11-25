"""`lem land base`: the task's branch onto origin's base, by the plain rebase when the tip does
not hold it. A rebase that stops on files or that git refuses is undone, and nothing of it is
kept but the files a builder resolves; what the rebase kept of the change is judged from git's
merges (`model/landing/base.py`)."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import base_after, base_facts, frame, step
from lem.kernel.errors import Refusal
from lem.model.landing import base, base_kept, base_stops
from lem.ports.git_facts import Conflict, GitRefused

if TYPE_CHECKING:
    from pathlib import Path

    from lem.kernel.envelope import Envelope
    from lem.records.landing.start import Based


def stopped(context: frame.Context, made: Conflict | GitRefused) -> Refusal:
    """Undo a rebase that stopped, and give its refusal; a conflict's files are kept for the
    builder who resolves them."""
    git, record, world = context.ports.git, context.record, context.world
    if git.rebase_state(context.worktree) is not None:
        git.abort(context.worktree)
    aborted = base_facts.aborted(context)
    if isinstance(made, GitRefused):
        return base_stops.refused(record, world, made.said, aborted)
    context.write(record, partial(base_kept.conflicted, world=world, files=made.files))
    return base_stops.conflict(record, world, made.files, aborted)


def rebased(context: frame.Context) -> base.After:
    """Rebase the worktree onto origin's base, git's merge of the tip before onto it asked
    first (a git too old for it is refused before the branch moves), and give the facts
    after it."""
    merged = base_after.merged_of(context, context.world.tip)
    named = context.world.rules.base
    made = context.ports.git.rebase(context.worktree, f"origin/{named}", reapply=False)
    if isinstance(made, (Conflict, GitRefused)):
        raise stopped(context, made)
    return base_after.after(context, made, merged)


def moved(context: frame.Context) -> base.After:
    """The facts after the move `base` decides: a rebase onto origin's base, or none; or why
    it may not move now."""
    record, world = context.record, context.world
    where = str(context.worktree)
    move = base.decide(record, world, base_facts.before(context), where)
    if isinstance(move, Refusal):
        raise move
    if move == "rebase":
        return rebased(context)
    return base_after.after(context, world.tip or world.base, None)


def act(context: frame.Context) -> Based:
    """Bring the tip onto origin's base when it does not hold it, and record where it is and
    what the move showed of the change."""
    after = moved(context)
    based = base.judged(context.world, after)
    polish = base_after.polish(context, after.tip)
    context.write(context.record, partial(base_kept.kept, based=based, polish=polish))
    where = str(context.worktree)
    refused = base.emptied(context.record, context.world, based, after.ahead, where)
    if refused is not None:
        raise refused
    return based


def run(folder: Path, slug: str) -> Envelope:
    """`lem land base SLUG`."""
    return step.landed(folder, slug, "base", act)
