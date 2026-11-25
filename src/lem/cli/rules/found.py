"""The rule files of a folder: every `.md` below it, through links too, as the agent that loads
such a folder by itself reads it, and each folder once, so that a loop of links ends."""

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

RULE = ".md"

# A folder, and the names of its files.
type Walked = tuple[str, list[str]]


def rule_files(folder: Path) -> tuple[Path, ...]:
    """The rule files below `folder`, by name in each folder, a folder before its subfolders."""
    return tuple(
        Path(where) / name
        for where, names in walked(folder)
        for name in sorted(names)
        if name.endswith(RULE)
    )


def walked(folder: Path) -> Iterator[Walked]:
    """Each folder below `folder` that is not one already seen through another link, with the
    names of its files; subfolders in the order of their names."""
    seen: set[str] = set()
    for where, folders, names in os.walk(folder, followlinks=True):
        real = os.path.realpath(where)
        if real in seen:
            folders.clear()
            continue
        seen.add(real)
        folders.sort()
        yield where, names
