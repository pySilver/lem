"""The release stop before a command on one task: every command that acts on a named task
reads its record through `checked` first (`release.check` on `main`).

A task two releases back gets the hold `release` once, and the command stops; a command that
ends the task (a drop, a step of the tracker that its end owes) sets the same hold and goes on,
so that the resume after a drop finds the stop and starts a new request.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.kernel import clock, release
from lem.model.task import release as rule
from lem.records.holds import ReleaseHold
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


def checked(state: Path, slug: str, *, ends: bool = False) -> Record:
    """The record of `slug`, read for a command on it; refused when the task began two
    releases back, unless the command ends it (`ends`)."""
    record = tasks.read(state, slug)
    running = release.running()
    if not rule.stops(record, running, rule.BEFORE):
        return record
    if not isinstance(record.task.hold, ReleaseHold):
        change = partial(rule.held, running=running, now=clock.now())
        record = tasks.update(state, slug, change, record.revision)
    if not ends:
        raise rule.refusal(record)
    return record
