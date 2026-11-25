"""The files of the reviewer's items, `backlog/` of the state folder: an item's name, taken from
its title, the names already there, and the path a record keeps of one."""

import re
from typing import TYPE_CHECKING

from lem.store import reviewer_items

if TYPE_CHECKING:
    from pathlib import Path

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
    """The names of the items in `folder`, none when it is not there."""
    if not folder.is_dir():
        return set()
    return {path.name for path in folder.glob("*.md")}


def recorded(name: str) -> str:
    """The path a record keeps of the item `name`: `.lem/state/backlog/NAME`."""
    return (reviewer_items.FROM_CHECKOUT / name).as_posix()
