"""Every task's record of a workspace for a comparison across its tasks, and the tasks whose
record does not read. A damaged record of another task leaves the comparison short and named,
never the command of this task stopped (`main:land.events_all` passed over a line that did not
read)."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Fault
from lem.store import guard, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record

# The records that read, by slug, and the slugs of those that do not.
type Survey = tuple[tuple[Record, ...], tuple[str, ...]]


def records(state: Path) -> Survey:
    """The record of every task in `state` that reads, by slug, and the slugs of those whose
    `task.json` is no record."""
    guard.readable(state)
    paths = (state / "tasks").glob(f"*/{tasks.RECORD}")
    slugs = sorted(path.parent.name for path in paths)
    found: list[Record] = []
    unread: list[str] = []
    for slug in slugs:
        try:
            found.append(tasks.read(state, slug))
        except Fault:
            unread.append(slug)
    return tuple(found), tuple(unread)
