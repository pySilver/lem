"""The checks of a sync's merge, through the runner of the landing's checks: the load gate first,
then each command of `checks.commands` in the feature's worktree, and the serial ones under the
serial lock when the others passed (`app/landing/checks_run.py`), each output in a file of the
feature's folder. A term ends what runs with what it started. What the commands left that git
neither tracks nor ignores goes after them, so that the next sync finds the worktree as it was.

A run of the sync is no run of the landing: nothing of it goes on the feature's record. The
context of a landing step over the feature (`context_of`) serves the runner and the merge lock.
"""

import contextlib
from typing import TYPE_CHECKING

from lem.app.landing import (
    checks_gate,
    checks_git,
    checks_stop,
    checks_tree,
    checks_verdict,
    frame,
    world,
)
from lem.model.task import sync_ends
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from lem.app.tasks.sync_frame import Sync
    from lem.records.landing.checks import Outcome


def context_of(sync: Sync) -> frame.Context:
    """The context of a landing step over the feature, its record read as it is now: the
    commands of the checks come from its settings, and the merge lock notes its waits in its
    journal."""
    record = tasks.read(sync.workspace.state, sync.place.slug)
    found = world.origin(sync.ports, sync.workspace, record, sync.now)
    return frame.Context(
        ports=sync.ports, workspace=sync.workspace, record=record, world=found
    )


def checked(sync: Sync) -> tuple[Outcome, ...]:
    """The outcomes of the checks on the merge; refused when one failed or the run was
    stopped."""
    context = context_of(sync)
    stopper = checks_stop.Stopper()
    with stopper.held():
        try:
            outcomes = gated(context)
        except InterruptedError:
            raise sync_ends.stopped(sync.place) from None
        stopper.done = True
    if not all(outcome.passed for outcome in outcomes):
        raise sync_ends.red(sync.place, outcomes)
    return outcomes


def gated(context: frame.Context) -> tuple[Outcome, ...]:
    """The wait at the load gate, then the commands."""
    slug = context.record.task.slug
    checks_gate.Gate(slug=slug, workspace=context.workspace).passed()
    with swept(context.worktree, slug):
        return checks_verdict.commands_of(context)


@contextlib.contextmanager
def swept(worktree: Path, slug: str) -> Generator[None]:
    """The stale bytecode removed before the commands; what they left that git neither
    tracks nor ignores removed after them, however they end."""
    checks_tree.cleared(worktree, slug)
    there = checks_git.untracked(worktree)
    try:
        yield
    finally:
        checks_tree.swept(worktree, there)
