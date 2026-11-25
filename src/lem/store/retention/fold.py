"""An ended task's journal folded into one summary entry (`project.summary_of` on `main`).

The summary keeps what the journal held that a reader still asks for: the run of statuses, the
last state with its line (why the task ended), the first and last moments, how many entries it
folded, the pull request with the proposal's green and reasons, whether a plan talk ran, and the
seconds of each span and each wait. A journal whose summary has newer entries after it (a late
append) folds again over the old summary, which is its past: the counts and the waits add up,
and a newer fact replaces an old one. The task's spans stay on the task, so their totals are
read from there.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.records.journal.task import StateNoted, Summary
from lem.store.retention.totals import added, spans_of, waits_of

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.journal.entry import Entry
    from lem.records.record import Record


def summary_of(record: Record, now: datetime) -> Summary:
    """The one summary that stands for the record's journal, folded at `now`."""
    past = past_of(record)
    rest = tuple(one for one in record.journal if not isinstance(one, Summary))
    moments = [one.at for one in rest]
    return replace(
        proposal_of(record, past),
        at=now,
        statuses=statuses_of(past, rest),
        last_state=last_state_of(past, rest),
        first=min((past.first, *moments)),
        last=max((past.last, *moments)),
        entries=past.entries + len(rest),
        talked=record.task.talk is not None or past.talked,
        spans=spans_of(record.task),
        waits=added(past.waits, waits_of(rest, now)),
    )


def past_of(record: Record) -> Summary:
    """The summary an earlier fold left, else one of nothing from the task's own moments."""
    found = (one for one in record.journal if isinstance(one, Summary))
    task = record.task
    nothing = Summary(
        at=task.opened, statuses=(), first=task.opened, last=task.since, entries=0
    )
    return next(found, nothing)


def proposal_of(record: Record, past: Summary) -> Summary:
    """The past with the pull request's number, and the proposal's green and reasons, as the
    landing has them now."""
    landing = record.landing
    if landing is None:
        return past
    pull, proposed = landing.pull, landing.proposed
    if pull is not None:
        past = replace(past, pull=pull.number)
    if proposed is not None:
        past = replace(past, green=proposed.green, reasons=proposed.reasons)
    return past


def states_of(entries: tuple[Entry, ...]) -> list[StateNoted]:
    """The journal's states, oldest first."""
    return [one for one in entries if isinstance(one, StateNoted)]


def last_state_of(past: Summary, entries: tuple[Entry, ...]) -> StateNoted | None:
    """The newest state, with its line: why the task ended."""
    states = states_of(entries)
    return states[-1] if states else past.last_state


def statuses_of(past: Summary, entries: tuple[Entry, ...]) -> tuple[str, ...]:
    """The run of statuses: the old summary's, then each new one that differs from the one
    before it."""
    run = list(past.statuses)
    for state in states_of(entries):
        if not run or run[-1] != state.status:
            run.append(state.status)
    return tuple(run)
