"""`lem land clean`: what a task that ended leaves goes, each only as `model/landing/clean.py`
allows, and the landing ends.

Each removal is read from the world again on a run after a stop, so what went already is not
removed twice; a deletion that did not happen (the branch or the forge's copy moved since) keeps
the cleanup due (`main:land.drop_forge_copy`).
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import changes, merge_step, merge_world
from lem.kernel.errors import Refusal
from lem.model.landing import clean
from lem.records.landing.merge import Cleaned
from lem.records.landing.record import Landing

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app.landing.frame import Context
    from lem.kernel.envelope import Envelope
    from lem.records.record import Record


def failed(what: str, branch: str, slug: str) -> Refusal:
    """The refusal of a deletion git or the forge did not make: the cleanup stays due."""
    return Refusal(
        "not-deleted",
        f"{what} of {branch} was not deleted: it is no longer at the commit the task left",
        f"lem land clean {slug} runs again; what went already is not removed twice",
    )


def swept(context: Context, sweep: clean.Sweep) -> Cleaned:
    """Remove what `sweep` names, and say what went and what stayed."""
    git, world = context.ports.git, context.world
    checkout, slug = context.workspace.checkout, context.record.task.slug
    if sweep.worktree:
        git.worktree_remove(checkout, context.worktree)
    if sweep.branch and not git.branch_delete(
        checkout, world.branch, world.local or ""
    ):
        raise failed("the local branch", world.branch, slug)
    ref = f"refs/heads/{world.branch}"
    if sweep.remote is not None and not context.ports.forge.delete_ref(
        ref, sweep.remote
    ):
        raise failed("the forge's copy", world.branch, slug)
    return Cleaned(
        worktree_gone=True,
        branch_gone=sweep.branch or world.local is None,
        forge_branch_gone=sweep.remote is not None or world.remote is None,
        branch_left=sweep.branch_left,
        rebased=sweep.rebased is not None,
        at=world.now,
    )


def ended(record: Record, *, cleaned: Cleaned) -> Record:
    """The record with what the cleanup did, and the landing ended."""
    return changes.landing(record, cleaned=cleaned, phase="ended")


def facts_of(context: Context) -> clean.Facts:
    """What git says of the task's branch, the rebase's proof only where it decides."""
    landing = context.record.landing or Landing()
    merged = landing.merged
    asks = merged is not None and clean.asks_rebase(
        context.world, merged, landing.pushed
    )
    return merge_world.branch_facts(context, merged, asks=asks)


def act(context: Context) -> Cleaned:
    """Remove what may go, and end the landing."""
    sweep = clean.decide(context.record, context.world, facts_of(context))
    if isinstance(sweep, Refusal):
        raise sweep
    cleaned = swept(context, sweep)
    context.write(context.record, partial(ended, cleaned=cleaned))
    return cleaned


def run(folder: Path, slug: str) -> Envelope:
    """`lem land clean SLUG`."""
    return merge_step.landed(folder, slug, "clean", act)
