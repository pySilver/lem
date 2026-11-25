"""The release stop allows observation and the steps the end of a task owes."""

from typing import TYPE_CHECKING

from lem.app.tasks import release
from lem.model.landing.invariants import AFTER_END
from lem.model.landing.merge_evidence import new_call_refusal
from lem.model.task.release import guard

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.landing.world import Due, Verb
    from lem.records.record import Record


def has_intent(record: Record) -> bool:
    """Whether a merge call remains to reconcile."""
    return record.landing is not None and record.landing.intent is not None


def at_step(state: Path, slug: str, verb: Verb | None) -> Record:
    """Read before a step's effects, with the end allowed past the release stop."""
    ends = verb in AFTER_END or verb == "merge"
    record = release.checked(state, slug, ends=ends)
    if verb == "merge" and not has_intent(record):
        stopped = new_call_refusal(record)
        if stopped is not None:
            raise stopped
    return record


def observed(state: Path, slug: str) -> Record:
    """Read for `next`, which can still report a due end or reconciliation."""
    return release.checked(state, slug, ends=True)


def reportable(record: Record, due: Due) -> None:
    """A task under the release stop can still settle a merge or finish its end."""
    if due.step in {"merged", "clean", "done"} or has_intent(record):
        return
    refused = guard(record)
    if refused is not None:
        raise refused
