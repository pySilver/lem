"""Every task's record of a workspace for a comparison across its tasks, and the tasks whose
record does not read. A damaged record of another task leaves the comparison short and named,
never the command of this task stopped (`main:land.events_all` passed over a line that did not
read)."""

from typing import TYPE_CHECKING, NamedTuple

from lem.kernel.errors import Fault, Refusal
from lem.store import task_file

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


class Survey(NamedTuple):
    """The records that read, by slug, and the folder names of those that do not."""

    readable: tuple[Record, ...]
    unread: tuple[str, ...]


def records(state: Path) -> Survey:
    """The record of every task in `state` that reads, by slug, and the slugs of those whose
    `task.json` is no record."""
    found: list[Record] = []
    unread: list[str] = []
    for path in task_file.paths(state):
        try:
            found.append(task_file.read(path))
        except Fault, OSError:
            unread.append(path.parent.name)
    return Survey(tuple(found), tuple(unread))


def warnings(state: Path, unread: tuple[str, ...]) -> tuple[str, ...]:
    """The lines a workspace view shows for its unread records."""
    paths = (state / "tasks" / slug / task_file.RECORD for slug in unread)
    return tuple(f"Lem omitted {path}: the record does not read." for path in paths)


def require_complete(warnings: tuple[str, ...]) -> None:
    """Refuse an action when it requires a complete survey."""
    if warnings:
        why = " ".join(warnings)
        raise Refusal(
            "unread-task-record",
            f"Lem needs every task record for this step. {why}",
            "The owner restores the task records listed here.",
        )
