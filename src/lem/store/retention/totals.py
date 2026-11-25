"""The seconds of each span and each wait of a task, which its summary keeps (`Total`): the
Activity view and the retro read them after the journal is folded."""

from collections import Counter
from typing import TYPE_CHECKING

from lem.records.journal.landing import CheckWait, MergeWait
from lem.records.journal.task import Total

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime

    from lem.records.journal.entry import Entry
    from lem.records.task import Task
    from lem.records.work import Span

type Totals = tuple[Total, ...]

# The name each wait of the journal is summed under.
WAITS = ((CheckWait, "checks"), (MergeWait, "merge"))


def totals(seconds: Iterable[tuple[str, int]]) -> Totals:
    """The seconds summed by name, in the order of the names."""
    summed: Counter[str] = Counter()
    for name, count in seconds:
        summed[name] += count
    names = sorted(summed)
    return tuple(Total(name=named, seconds=summed[named]) for named in names)


def between(start: datetime, end: datetime) -> int:
    """The whole seconds from `start` to `end`."""
    return int((end - start).total_seconds())


def spans_of(task: Task) -> Totals:
    """The seconds of each name of the task's ended spans."""
    ended = [span for span in task.spans if span.end is not None]
    return totals(map(span_seconds, ended))


def span_seconds(span: Span) -> tuple[str, int]:
    """A span's name and its seconds, none for one that has not ended."""
    end = span.end or span.start
    return span.name, between(span.start, end)


def wait_of(entry: Entry) -> str | None:
    """The name an entry is summed under when it is a wait, else None."""
    return next((name for kind, name in WAITS if isinstance(entry, kind)), None)


def waits_of(entries: tuple[Entry, ...], now: datetime) -> Totals:
    """The seconds of each kind of wait: a wait lasts until the journal's next entry, or
    `now` for the newest."""
    seconds: list[tuple[str, int]] = []
    ends = [*(one.at for one in entries[1:]), now]
    for entry, end in zip(entries, ends, strict=False):
        name = wait_of(entry)
        if name is not None:
            seconds.append((name, between(entry.at, end)))
    return totals(seconds)


def added(old: Totals, new: Totals) -> Totals:
    """The totals of two folds, by name."""
    seconds = [(total.name, total.seconds) for total in old]
    seconds.extend((total.name, total.seconds) for total in new)
    return totals(seconds)
