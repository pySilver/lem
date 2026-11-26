"""The wait the checks write into the journal and the wait their status gives."""

from datetime import UTC, datetime
from functools import partial
from itertools import takewhile
from typing import TYPE_CHECKING

from lem.app.landing import changes
from lem.model.landing import checks_said
from lem.records.base import Frozen, Moment
from lem.records.journal.landing import CheckEnd, CheckWait
from lem.records.journal.task import SpanMark
from lem.store import tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.journal.entry import Entry


class Waited(Frozen, frozen=True, kw_only=True):
    """What `--status` gives about the wait: its moment, its facts and the owner's line."""

    at: Moment
    wait: checks_said.Wait
    say: str


def noted(state: Path, slug: str, entry: CheckWait) -> None:
    """Write one wait into the task's journal."""
    record = tasks.read(state, slug)
    tasks.update(state, slug, partial(changes.noted, entry=entry), record.revision)


def wait_of(
    wait: checks_said.Wait, slug: str, position: int, now: float, *, run: str | None
) -> CheckWait:
    """The facts and words of one wait, tied to the run that wrote it."""
    reason = "load"
    if wait.behind:
        reason = "behind"
    elif wait.after:
        reason = "after"
    return CheckWait(
        at=datetime.fromtimestamp(now, UTC).replace(microsecond=0),
        reason=reason,
        load=wait.load,
        start_below=wait.start,
        behind=wait.behind,
        position=position,
        after=wait.after,
        behind_repo=wait.behind_repo,
        why=wait.why,
        unread=wait.unread,
        say=checks_said.waiting(slug, wait),
        run=run,
    )


def shown(entry: CheckWait) -> Waited | None:
    """The status shape of a journal wait with all its facts."""
    if entry.load is None or entry.start_below is None or entry.say is None:
        return None
    wait = checks_said.Wait(
        load=entry.load,
        start=entry.start_below,
        behind=entry.behind,
        after=entry.after,
        behind_repo=entry.behind_repo,
        why=entry.why,
        unread=entry.unread,
    )
    return Waited(at=entry.at, wait=wait, say=entry.say)


def latest(journal: tuple[Entry, ...], run: str | None) -> Waited | None:
    """The active run's latest wait, until the checks start or end."""
    if run is None:
        return None
    active = takewhile(before_checks, reversed(journal))
    entry = next(
        (one for one in active if isinstance(one, CheckWait) and one.run == run),
        None,
    )
    return shown(entry) if isinstance(entry, CheckWait) else None


def before_checks(entry: Entry) -> bool:
    """Whether this entry leaves a wait for the active run in force."""
    if isinstance(entry, SpanMark):
        return entry.name != "checks"
    return not isinstance(entry, CheckEnd)
