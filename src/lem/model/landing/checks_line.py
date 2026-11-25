"""The machine's one line of the runs of the checks that wait at the load gate, and one look of
a run in it (`land.line_order`, `line_why` and `gate_look` on `main`).

The line is one for every repository on the machine. A run another open task waits for goes
first (`wanted`), then the run whose wait began first, then by the task and the repository, so
that every run reads the same first. A run starts when it is first, the load is under the start
number, and a minute passed since the last start under the gate: the load average of one minute
needs about that long to show a run that started (`LOAD_SPACING` on `main`, a guess, not a
measurement).
"""

from typing import Literal

from lem.model.landing.checks_said import Behind
from lem.records.base import Frozen

type Line = tuple[Entry, ...]
# The load average now and the start number under which the checks start.
type Levels = tuple[float, float]
# The least time between two starts under the gate on one machine, in seconds.
SPACING = 60.0


class Entry(Frozen, frozen=True, kw_only=True):
    """A run in the line: its task, the main checkout of its repository, when its wait began
    (seconds of the epoch), and whether another open task of its repository waits for it."""

    task: str
    repo: str
    since: float
    wanted: bool = False


class LastStart(Frozen, frozen=True, kw_only=True):
    """The last start under the gate on the machine: when, and which task of which repository."""

    at: float
    task: str
    repo: str


class Look(Frozen, frozen=True, kw_only=True):
    """One look of a run: it starts (`go`), or why it waits: `behind` the first in the line,
    the `load`, or `after` the last start, with the seconds since it (`gap`)."""

    go: bool
    reason: Literal["behind", "load", "after"] | None = None
    behind: str | None = None
    behind_repo: str | None = None
    why: Behind | None = None
    after: str | None = None
    gap: float | None = None


def order(entries: Line) -> Line:
    """The line, first first."""
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                not entry.wanted,
                entry.since,
                entry.task,
                entry.repo,
            ),
        )
    )


def why(first: Entry, own: Entry) -> Behind:
    """Why `first` goes before `own` in the line."""
    if first.wanted and not own.wanted:
        return "wanted"
    return "longer" if first.since < own.since else "first"


def spaced(last: LastStart | None, now: float) -> Look | None:
    """The wait of a run whose start would come too soon after the last start; None when a
    minute passed, or when no start is known."""
    if last is None:
        return None
    gap = now - last.at
    if gap < 0 or gap >= SPACING:
        return None
    return Look(go=False, reason="after", after=last.task, gap=gap)


def look(line: Line, own: Entry, levels: Levels) -> Look:
    """One look of the run `own` at the line (the other runs that wait, `own` among them), the
    load and the start number (`levels`): behind the first, also while the load
    is above the number; the load; else it starts, once `spaced` says a minute passed since
    the last start, which the caller asks under the same lock."""
    first = order(line)[0]
    if first != own:
        other = None if first.repo == own.repo else first.repo
        reason = why(first, own)
        return Look(
            go=False,
            reason="behind",
            behind=first.task,
            behind_repo=other,
            why=reason,
        )
    load, start = levels
    if load >= start:
        return Look(go=False, reason="load")
    return Look(go=True)
