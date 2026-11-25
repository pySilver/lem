"""A rebase of `base` that stopped: undone, looked at after the abort, and refused with what
it left; a conflict's files are kept for the builder who resolves them only once the worktree is
as it was (`land.cmd_base`, `land.rebase_left` on `main`)."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.landing import base_facts
from lem.model.landing import base_kept, base_stops
from lem.ports.faults import Unanswered
from lem.ports.git_facts import Conflict, GitRefused

if TYPE_CHECKING:
    from lem.app.landing import frame
    from lem.kernel.errors import Refusal
    from lem.model.landing.rebased import Paths
    from lem.model.landing.world import World
    from lem.records.landing.start import Based
    from lem.records.record import Record


def undone(context: frame.Context) -> None:
    """Abort a rebase that stopped in the worktree. An abort that fails is no fault here: what
    it left is looked at next and named, with the command that ends it."""
    git, where = context.ports.git, context.worktree
    if git.rebase_state(where) is None:
        return
    try:
        git.abort(where)
    except Unanswered:
        return


def stopped(
    context: frame.Context, made: Conflict | GitRefused, kept: Based | None
) -> Refusal:
    """Undo a rebase that stopped, and give its refusal. Once the worktree is as it was, the
    record goes back to `kept`, what it held before the mark, and a conflict's files are kept
    for the builder who resolves them; while it is not, the mark keeps the tip before."""
    record, world = context.record, context.world
    undone(context)
    aborted = base_facts.aborted(context)
    if not base_stops.left(world, aborted):
        files = made.files if isinstance(made, Conflict) else None
        context.write(record, partial(back, kept=kept, world=world, files=files))
    if isinstance(made, GitRefused):
        return base_stops.refused(record, world, made.said, aborted)
    return base_stops.conflict(record, world, made.files, aborted)


def back(
    record: Record, kept: Based | None, world: World, files: Paths | None
) -> Record:
    """The record as it was before the mark, with a conflict's files when there are."""
    unmarked = base_kept.unmarked(record, kept)
    if files is None:
        return unmarked
    return base_kept.conflicted(unmarked, world, files)
