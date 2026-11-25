"""The files of the reviewer's items, `backlog/` of the state folder: an item's name, taken from
its title, the names already there, and the path a record keeps of one."""

import re
from pathlib import Path

BACKLOG = "backlog"
# The item's path as a record keeps it and a task's ask names it, from the main checkout.
FROM_CHECKOUT = Path(".lem") / "state" / BACKLOG


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
    return (FROM_CHECKOUT / name).as_posix()


def file_of(state: Path, path: str) -> Path:
    """The file of the item a record keeps as `path`, in the state folder's backlog."""
    _, _, name = path.rpartition("/")
    return state / BACKLOG / name
