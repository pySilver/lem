"""What a retro reads of the queue: `list`, the unreviewed groups, most sessions first, after
the count of the failures (a message the hook or the worker failed on was never judged); and
`show`, every entry of one group in full (`corrections.cmd_list` and `cmd_show` on `main`)."""

from typing import TYPE_CHECKING

from lem.addons.corrections import groups, queue
from lem.addons.corrections.listed import Failures, Group, Listing

if TYPE_CHECKING:
    import datetime as dt
    from pathlib import Path

    from lem.records.corrections import Correction

OWNER_TRIM = 500
PREVIOUS_TRIM = 300


def listed(state: Path, *, collect: bool) -> Listing:
    """The unreviewed groups of the queue, most sessions first, then the oldest newest entry."""
    ordered = sorted(groups.unreviewed(state).items(), key=order)
    rows = tuple(row_of(gid, entries) for gid, entries in ordered)
    return Listing(
        collect=collect,
        failures=failures_of(state),
        entries=sum(row.entries for row in rows),
        groups=rows,
    )


def failures_of(state: Path) -> Failures:
    """The errors of the queue's log, and the newest; a note is of a message that was judged."""
    logged = queue.lines(state / queue.LOG, queue.LogLine)
    errors = [line for line in logged if line.error]
    newest = errors[-1] if errors else None
    return Failures(count=len(errors), newest=newest)


def row_of(gid: str, entries: list[Correction]) -> Group:
    """One group as the list gives it."""
    scores = [entry.p_lesson for entry in entries if entry.p_lesson is not None]
    first = entries[0]
    return Group(
        gid=gid,
        entries=len(entries),
        sessions=len({entry.session for entry in entries}),
        days=days_of(entries),
        p_lesson_max=max(scores, default=None),
        owner=groups.trimmed(first.owner, OWNER_TRIM),
        answered=groups.trimmed(first.previous, PREVIOUS_TRIM),
    )


def days_of(entries: list[Correction]) -> tuple[str, ...]:
    """The days of a group's entries, in order."""
    days = {entry.at.date().isoformat() for entry in entries}
    return tuple(sorted(days))


def order(found: tuple[str, list[Correction]]) -> tuple[int, dt.datetime]:
    """A group's place: more sessions first, then the earlier newest entry."""
    _, entries = found
    sessions = {entry.session for entry in entries}
    return -len(sessions), max(entry.at for entry in entries)


def shown(state: Path, gid: str) -> tuple[Correction, ...]:
    """Every entry of the unreviewed group `gid` in full."""
    return tuple(groups.group_of(state, gid))
