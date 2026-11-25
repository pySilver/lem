"""`lem land base`: the task's branch onto origin's base, by the plain rebase when the tip does
not hold it. A rebase that stops on files or that git refuses is undone, and nothing of it is
kept but the files a builder resolves; what the rebase kept of the change is judged from git's
merges (`model/landing/base.py`)."""

import dataclasses
from functools import partial
from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import (
    base_after,
    base_facts,
    base_polish,
    base_stop,
    frame,
    step,
)
from lem.kernel.errors import Refusal
from lem.model.landing import base, base_empty, base_kept
from lem.ports.git_facts import Conflict, GitRefused
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from pathlib import Path

    from lem.kernel.envelope import Envelope
    from lem.records.landing.start import Based


def mark(context: frame.Context) -> frame.Context:
    """Write the tip before the rebase on record, and give the context with that record."""
    world = context.world
    fork = context.ports.git.merge_base(
        context.worktree, world.tip or world.base, world.base
    )
    marked = partial(base_kept.marked, world=world, fork=fork or world.base)
    return dataclasses.replace(context, record=context.write(context.record, marked))


def rebased(context: frame.Context) -> tuple[frame.Context, base.After]:
    """Rebase the worktree onto origin's base by the commit the world read, git's merge of the
    tip before onto it asked first (a git too old for it is refused before the branch moves)
    and the tip before it marked on record; give the context after the mark and the facts
    after the rebase."""
    merged = base_after.merged_of(context, context.world.tip)
    kept = (context.record.landing or Landing()).based
    context = mark(context)
    made = context.ports.git.rebase(context.worktree, context.world.base, reapply=False)
    if isinstance(made, (Conflict, GitRefused)):
        raise base_stop.stopped(context, made, kept)
    return context, base_after.after(context, made, merged)


def stayed(context: frame.Context) -> base.After:
    """The facts of a tip that holds origin's base already; the tip before a rebase a stop
    cut before its record is taken from the record's mark."""
    start = base_after.recovered(context)
    tip = context.world.tip or context.world.base
    after = base_after.after(context, tip, base_after.merged_of(context, start))
    return msgspec.structs.replace(after, before=start)


def moved(context: frame.Context) -> tuple[frame.Context, base.After]:
    """The facts after the move `base` decides: a rebase onto origin's base, or none; or why
    it may not move now."""
    where = str(context.worktree)
    move = base.decide(context.record, context.world, base_facts.before(context), where)
    if isinstance(move, Refusal):
        raise move
    if move == "rebase":
        return rebased(context)
    return context, stayed(context)


def recorded(context: frame.Context, after: base.After) -> Based:
    """Write where the move left the branch, the polish pass and a builder's resolution."""
    based = base.judged(context.world, after)
    polished = base_polish.polish(context, after.tip, after.before)
    context.write(
        context.record,
        partial(base_kept.kept, based=based, polished=polished, files=after.resolved),
    )
    return based


def act(context: frame.Context) -> Based:
    """Bring the tip onto origin's base when it does not hold it, and record where it is and
    what the move showed of the change."""
    context, after = moved(context)
    based = recorded(context, after)
    where = str(context.worktree)
    refused = base_empty.emptied(
        context.record, context.world, based, after.ahead, where
    )
    if refused is not None:
        raise refused
    return based


def run(folder: Path, slug: str) -> Envelope:
    """`lem land base SLUG`."""
    return step.landed(folder, slug, "base", act)
