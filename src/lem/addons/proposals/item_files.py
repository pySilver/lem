"""The files of the reviewer's items, `backlog/` of the state folder: an item's name, taken from
its title, the names already there, and the path a record keeps of one."""

import re
from pathlib import Path
from typing import TYPE_CHECKING

from lem.addons.proposals import heads
from lem.model.task.claim import ENDED
from lem.store import reviewer_items, tasks

if TYPE_CHECKING:
    from collections.abc import Iterator

    from lem.records.task import Task

file_of = reviewer_items.file_of


def slug_of(title: str) -> str:
    """The stem of an item's file name: the title's words in lower case, joined by hyphens."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def free_name(stem: str, taken: set[str]) -> str:
    """`STEM.md`, or `STEM-2.md`, `STEM-3.md` when that is taken; the name is taken now."""
    name, suffix = f"{stem}.md", 1
    while name in taken:
        suffix += 1
        name = f"{stem}-{suffix}.md"
    taken.add(name)
    return name


def taken_names(folder: Path) -> set[str]:
    """The names on disk or held by tasks, including items a merge retry can remove."""
    written = {path.name for path in folder.glob("*.md")}
    claimed = {Path(path).name for path, _ in claims_of(folder.parent)}
    return written | claimed


def backlog_heads(folder: Path) -> dict[Path, heads.Head]:
    """Read the head of each Markdown file of the reviewer's backlog."""
    return {path: heads.read(path) for path in sorted(folder.glob("*.md"))}


def claims_of(state: Path) -> Iterator[tuple[str, Task]]:
    """Each reviewer item a task that has not ended holds, with that task."""
    checkout = state.parent.parent
    for record in tasks.every(state):
        task = record.task
        path = reviewer_items.relative(checkout, task.backlog_item or "")
        if path is not None and task.status not in ENDED:
            yield path, task


def recorded(name: str) -> str:
    """The path a record keeps of the item `name`: `.lem/state/backlog/NAME`."""
    return (reviewer_items.FROM_CHECKOUT / name).as_posix()
