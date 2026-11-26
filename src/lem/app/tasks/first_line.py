"""The first line of a task, composed from its record and the files of its folder, which
`lem task read` says and `lem task show` shows (the owner's ruling "The first line of a task is
composed by Lem, and its session says it as it is")."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.model.task import first_line, quotes
from lem.records.journal.task import StateNoted
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.journal.entry import Entry
    from lem.records.record import Record
    from lem.records.task import Task

# The investigator's report in the task's folder.
REPORT = "investigation.md"


def text_of(path: Path) -> str:
    """The text of a file, or nothing when it is not there."""
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def gathered(workspace: places.Workspace, task: Task) -> first_line.Read:
    """What the line reads beside the record: the task's `criteria.md`, `task.md` and
    report, and the title of the backlog item it came from."""
    folder = places.task_folder(workspace.state, task.slug)
    backlog = task.backlog_item
    title = quotes.title_of(text_of(workspace.checkout / backlog)) if backlog else None
    return first_line.Read(
        criteria=text_of(folder / "criteria.md"),
        outcome=text_of(folder / "task.md"),
        title=title,
        report=(folder / REPORT).is_file(),
    )


def said(workspace: places.Workspace, record: Record, *, named: bool) -> str | None:
    """The task's first line as its own session says it, or with `named` as another session
    does, the task's name first; None for a night task, before the read names the task's
    path, and while his order waits for his answer."""
    task = record.task
    line = first_line.line_of(task, gathered(workspace, task))
    if line is None:
        return None
    return first_line.composed(line, task.slug if named else None)


def with_opening(record: Record, opening_line: str | None) -> tuple[Entry, ...]:
    """The first line belongs to the read's current state block."""
    for index in range(len(record.journal) - 1, -1, -1):
        entry = record.journal[index]
        if isinstance(entry, StateNoted):
            noted = replace(entry, opening=opening_line)
            before = record.journal[:index]
            after = record.journal[index + 1 :]
            return (*before, noted, *after)
    return record.journal
