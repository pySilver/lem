"""What an ended task keeps after `state.keep_days` with nothing new (the design's part 3,
"Retention"; `project.task_calls` and `artifacts.SMALL_RECORD` on `main`).

A task is `open` until it landed, was answered or was dropped; an ended one is `young` while
its newest moment is after the cutoff, and `old` after it. An old task keeps its small record:
`task.json`, whose journal becomes one summary entry (`fold.py`) and whose citations of the
files that go are cleared, its sessions (`sessions.jsonl`, so that Done and the token totals
still count, and Lem's acts on them, so that no duty wakes it again), its ask, its request, the
aside of a park, and its locks. Every other file of its folder goes.
"""

from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from lem.records.journal.task import Summary

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.landing.record import Landing
    from lem.records.record import Record

type Call = Literal["open", "young", "old"]

ENDED = frozenset(("landed", "answered", "dropped"))
KEPT = frozenset(
    (
        "task.json",
        "sessions.jsonl",
        "session-acts.jsonl",
        "ask.txt",
        "task.md",
        "parked.json",
    )
)
LOCKS = ".lock"


def kept(name: str) -> bool:
    """Whether a file of the task's folder, by its path inside it, is of the small record."""
    return name in KEPT or (name.endswith(LOCKS) and "/" not in name)


def newest(record: Record) -> datetime:
    """The task's newest moment: its last change of status, and its journal's newest entry,
    whose summary counts by the newest moment it folded."""
    moments = [
        entry.last if isinstance(entry, Summary) else entry.at
        for entry in record.journal
    ]
    return max((record.task.since, *moments))


def call_of(record: Record, cutoff: datetime) -> Call:
    """What retention does with the task: nothing while it is open or young."""
    if record.task.status not in ENDED:
        return "open"
    return "old" if newest(record) <= cutoff else "young"


def folded_already(record: Record) -> bool:
    """Whether the journal is its one summary and nothing newer."""
    journal = record.journal
    return len(journal) == 1 and isinstance(journal[0], Summary)


def folded_into(record: Record, *, summary: Summary) -> Record:
    """The record with its journal as the one summary, and no citation of a file that goes."""
    return cleared(replace(record, journal=(summary,)))


def cleared(record: Record) -> Record:
    """The record with no citation of a file that goes: the landing's evidence, the
    decisions (the merge commit's text lists them), and the investigation's report."""
    task = record.task
    found = task.investigation
    investigation = replace(found, report=None) if found else None
    task = replace(task, decisions=(), investigation=investigation)
    landing = cleared_landing(record.landing) if record.landing else None
    return replace(record, task=task, landing=landing)


def cleared_landing(landing: Landing) -> Landing:
    """The landing with only what cites no file of the task's folder."""
    proposed = landing.proposed
    if proposed is not None:
        proposed = replace(proposed, notes_path=None, text=None, text_waits=None)
    polished = landing.polished
    if polished is not None:
        polished = replace(polished, filed=(), report=None)
    reads = tuple(replace(read, brief=None) for read in landing.reads)
    return replace(
        landing,
        proposed=proposed,
        polished=polished,
        reads=reads,
        checked=None,
        reviews=(),
        archived=(),
        filed=(),
        resolution=None,
        jev=(),
    )
