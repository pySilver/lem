"""The words of each comment Lem leaves on an issue, from the task's record alone, so that any
session, or the owner, can run a step a task still owes: what landed and its pull request, why
the task was dropped, and the answer with where it is."""

from typing import TYPE_CHECKING

from lem.model.task.outcome import outcome_of
from lem.model.task.quotes import first_sentence
from lem.records.journal.task import StateNoted, Summary
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

TASK_TEXT = "task.md"
REPORT = "investigation.md"


def first_line(record: Record) -> str:
    """The line of the task's newest state, or its status when it has none."""
    for entry in reversed(record.journal):
        if isinstance(entry, StateNoted) and entry.line:
            return entry.line
        if isinstance(entry, Summary) and entry.last_state and entry.last_state.line:
            return entry.last_state.line
    return record.task.status


def what_changed(state: Path, record: Record) -> str:
    """What the task changed: the outcome of its `task.md`, else the first sentence of what was
    asked."""
    task = record.task
    path = places.task_folder(state, task.slug) / TASK_TEXT
    outcome = outcome_of(path.read_text(encoding="utf-8")) if path.is_file() else None
    return outcome or first_sentence(task.ask or task.slug)


def pull_line(record: Record) -> str:
    """The pull request, green or not green when it was proposed, or the task's state when
    none is on record."""
    landing = record.landing
    pull = landing.pull if landing else None
    if landing is None or pull is None:
        said = first_line(record)
        return f"No pull request is on record; the task's state says: {said}."
    green = landing.proposed is not None and landing.proposed.green
    verdict = "green" if green else "not green"
    return f"The pull request: {pull.url}, {verdict} when it was proposed."


def landed(state: Path, record: Record) -> str:
    """The landing's comment: what changed, and the pull request with green or not."""
    what = what_changed(state, record)
    return f"Lem landed the work of this issue: {what}.\n\n{pull_line(record)}"


def dropped(record: Record) -> str:
    """The drop's comment: why, in the line of the task's state."""
    return f"Lem dropped its task for this issue: {first_line(record)}."


def answer_line(record: Record) -> str:
    """The answer in one line: the investigation's line and where, else the task's state."""
    found = record.task.investigation
    line = (found and found.line) or first_line(record)
    where = f" ({found.where})" if found and found.where else ""
    return f"{line}{where}"


def answered(state: Path, record: Record) -> str:
    """The answer's comment: the answer, and that its report stays in the task's folder while
    the folder holds it; an answer still owed after the prune removed the report names none."""
    said = f"Lem's investigation answered this issue: {answer_line(record)}."
    found = record.task.investigation
    report = (found and found.report) or REPORT
    if not (places.task_folder(state, record.task.slug) / report).is_file():
        return said
    return (
        f"{said}\n\nThe report is in the task's directory on the owner's machine, not on "
        "this issue."
    )
