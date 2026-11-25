"""`lem decisions changes`, `list` and `pending`: what a task's record holds of its decisions,
read only (`decisions.cmd_pending`, `Task.changes` and `Task.decisions` on `main`)."""

from typing import TYPE_CHECKING

from lem.app.criteria import where
from lem.model.decisions import book, changes, pending
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path


def changes_of(folder: Path, slug: str) -> changes.Changes:
    """`lem decisions changes SLUG`: the approvals, the changes of the newest one, and the
    criteria they give."""
    return changes.changes_of(where.here_of(folder, slug).read().task)


def listed(folder: Path, slug: str) -> tuple[book.Listed, ...]:
    """`lem decisions list SLUG`: every decision and breaker, each as it stands now."""
    return book.listed(where.here_of(folder, slug).read().task)


def waiting(folder: Path, slug: str | None) -> pending.Pending:
    """`lem decisions pending [SLUG]`: the breakers that wait, of one task or of every task."""
    if slug is not None:
        task = where.here_of(folder, slug).read().task
        return pending.pending((task,), named=True)
    state = places.workspace(folder).state
    every = tuple(record.task for record in tasks.every(state))
    return pending.pending(every, named=False)
