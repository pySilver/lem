"""`lem land clean`: the landed task's worktree, its branch and the forge's copy of it go, each
only as `model/landing/clean.py` allows, and the landing ends.

Each removal is read from the world again on a run after a stop, so what went already is not
removed twice.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import changes, frame, step
from lem.kernel.errors import Refusal
from lem.model.landing import clean
from lem.records.landing.merge import Cleaned

if TYPE_CHECKING:
    from pathlib import Path

    from lem.kernel.envelope import Envelope
    from lem.records.record import Record


def swept(context: frame.Context, sweep: clean.Sweep, head: str) -> Cleaned:
    """Remove what `sweep` names, and say what went and what stayed."""
    git, world = context.ports.git, context.world
    checkout = context.workspace.checkout
    if sweep.worktree:
        git.worktree_remove(checkout, context.worktree)
    branch_gone = sweep.branch and git.branch_delete(
        checkout, world.branch, world.local or ""
    )
    copy_gone = sweep.remote and context.ports.forge.delete_ref(
        f"refs/heads/{world.branch}", head
    )
    return Cleaned(
        worktree_gone=True,
        branch_gone=branch_gone or world.local is None,
        forge_branch_gone=copy_gone or world.remote is None,
        branch_left=sweep.branch_left,
        at=world.now,
    )


def ended(record: Record, *, cleaned: Cleaned) -> Record:
    """The record with what the cleanup did, and the landing ended."""
    return changes.landing(record, cleaned=cleaned, phase="ended")


def act(context: frame.Context) -> Cleaned:
    """Remove what may go, and end the landing."""
    sweep = clean.decide(context.record, context.world)
    if isinstance(sweep, Refusal):
        raise sweep
    landing = context.record.landing
    merged = landing.merged if landing else None
    cleaned = swept(context, sweep, merged.merged_head if merged else "")
    context.write(context.record, partial(ended, cleaned=cleaned))
    return cleaned


def run(folder: Path, slug: str) -> Envelope:
    """`lem land clean SLUG`."""
    return step.landed(folder, slug, "clean", act)
