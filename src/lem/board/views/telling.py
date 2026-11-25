"""What a task's card says of it in one line, and that line's hover (`board_model.card_line` on
`main`): a wait of its checks or its merge, an answered question's answer, else its newest state's
line in the board's words, with its state's label before it where the column does not say it
already.

Its hover is `hovers.py`'s.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.board.views import words
from lem.records.journal.landing import CheckEnd, CheckWait, MergeWait
from lem.records.journal.task import StateNoted, Summary

if TYPE_CHECKING:
    from lem.board.views.standing import Standing
    from lem.records.journal.entry import Entry
    from lem.records.record import Record
    from lem.records.task import Task

# What an investigation found, as a card says it before its line.
CALLS = MappingProxyType(
    {
        "small": "The cause",
        "full": "The cause",
        "not-a-bug": "No bug",
        "not-reproduced": "Not reproduced",
        "answer": "The answer",
    }
)
# Why the checks wait behind another landing, by the wait's `why`.
BEHIND = MappingProxyType(
    {
        "wanted": "which another task waits for",
        "longer": "which waits longer",
        "first": "which is first in the line",
    }
)
WAITING = frozenset(("landing", "open"))


def line(record: Record, standing: Standing, title: str) -> str:
    """The card's line in the column titled `title`."""
    waits = waiting(record) or answered(record.task)
    if waits is not None:
        return waits
    shown = said(record)
    if not shown:
        return standing.label
    label = standing.label
    repeats = label == title or shown.lower().startswith(label.lower())
    return words.capital(shown) if repeats else f"{label}: {shown}"


def answered(task: Task) -> str | None:
    """The answer of a question its investigation answered, or None."""
    found = task.investigation
    if task.status != "answered" or found is None or found.call is None:
        return None
    call = CALLS[found.call]
    return f"{call}: {found.line}" if found.line else call


def said(record: Record) -> str:
    """The newest state's line in the board's words; "" with none."""
    noted = newest_state(record.journal)
    if noted is None or not noted.line:
        return ""
    talked = any(
        span.name == "plan-talk" and span.end is not None and span.end <= noted.at
        for span in record.task.spans
    )
    return words.said(noted.line, talked=talked)


def newest_state(journal: tuple[Entry, ...]) -> StateNoted | None:
    """The newest state of the journal, the one a summary keeps among them."""
    for entry in reversed(journal):
        if isinstance(entry, StateNoted):
            return entry
        if isinstance(entry, Summary):
            return entry.last_state
    return None


def waiting(record: Record) -> str | None:
    """What a landing or an open task waits for now, when its newest checks' or merge's entry
    is a wait; else None."""
    if record.task.status not in WAITING:
        return None
    entries = (
        entry
        for entry in reversed(record.journal)
        if isinstance(entry, CheckWait | CheckEnd | MergeWait)
    )
    newest = next(entries, None)
    if isinstance(newest, MergeWait):
        behind = newest.behind or "another task"
        return f"Waits for the merge of {behind}"
    if isinstance(newest, CheckWait):
        return checks_wait(newest)
    return None


def checks_wait(wait: CheckWait) -> str:
    """The words of a wait of the checks: behind another run, after one, or for the load."""
    if wait.behind:
        repo = wait.behind_repo.rpartition("/")[2] if wait.behind_repo else ""
        name = f"{wait.behind} of {repo}" if repo else wait.behind
        why = BEHIND[wait.why or "first"]
        return f"Its checks wait behind {name}, {why}"
    if wait.after:
        return f"Its checks wait a minute after the checks of {wait.after} started"
    return f"Waits for the load: {wait.load}, starts below {wait.start_below}"
