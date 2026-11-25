"""The step of the guard of a stopped session that is due now (`guard_rule` says the rule)."""

from typing import TYPE_CHECKING

from lem.app.sessions.guard_rule import (
    ANSWER_SECONDS,
    QUIET_SECONDS,
    STOPPED,
    Due,
    Facts,
    Timeline,
    restarted,
    run_start,
)

if TYPE_CHECKING:
    from datetime import datetime


def due(line: Timeline, facts: Facts, now: datetime) -> Due | None:
    """The step due for the task now, or None."""
    if not facts.working():
        return None
    start = clock_start(line)
    since = max(start, facts.sign) if facts.read and facts.sign else start
    worked = worked_due(line, facts, start)
    if worked is not None:
        return worked
    place = sent_wake(line, facts, since)
    if place is None:
        quiet = (now - since).total_seconds() >= QUIET_SECONDS
        return Due(step="status", since=since) if quiet else None
    return after_wake(line, facts, place, now)


def clock_start(line: Timeline) -> datetime:
    """The newest of the task's work, its newest open, and the turn of its newest `worked`."""
    moments = [one.at for one in line.events if one.kind in {"work", "open"}]
    turns = [one.turn for one in line.events if one.turn]
    return max((*moments, *turns))


def worked_due(line: Timeline, facts: Facts, start: datetime) -> Due | None:
    """`worked` when the signs read and show a turn at or after the newest status wake that
    the unread clock sent after the clock's start."""
    wakes = line.status_after(start)
    sign = facts.sign
    if not (wakes and facts.read and sign):
        return None
    newest = line.events[wakes[-1]]
    if not newest.unread or sign < newest.at:
        return None
    return Due(step="worked", since=sign)


def sent_wake(line: Timeline, facts: Facts, since: datetime) -> int | None:
    """The place of the first status wake after `since` that the clock of `facts` sent (the
    unread clock its unread wakes, the other its own), or the one before the stop that
    stands, which counts for both clocks."""
    stop = line.stop_stands()
    held = None if stop is None else line.wake_before(stop)
    found = [
        place
        for place in line.status_after(since)
        if line.events[place].unread is not facts.read or place == held
    ]
    return found[0] if found else None


def after_wake(line: Timeline, facts: Facts, place: int, now: datetime) -> Due | None:
    """`restart` or `stopped` once the wake at `place` has waited ANSWER_SECONDS: a restart
    with signs that read, once for a run of work and never over a stop; else one stop."""
    asked = line.events[place].at
    if (now - asked).total_seconds() < ANSWER_SECONDS:
        return None
    if facts.read and restartable(line):
        return Due(step="restart", since=asked)
    return None if line.has(STOPPED, place) else Due(step="stopped", since=asked)


def restartable(line: Timeline) -> bool:
    """Whether a restart may come: no stop stands, no restart came after the task's newest
    work, and no stop stood in the run of work since its newest open."""
    places = range(run_start(line), len(line.events))
    stood = any(map(line.stood, places))
    return line.stop_stands() is None and not restarted(line) and not stood
