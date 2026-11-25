"""Whether the place in the code an item names is still there (`board.where_problem` on
`main`): the check the backlog skill makes before it reports an item, read in the main
checkout."""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

LEAVES = "the path leaves the repository"
GONE = "the file is not there"
UNREADABLE = "the file cannot be read"
NO_HEADING = "the heading is not in the file"


def where_problem(root: Path, where: str) -> str | None:
    """What of an item's `where` (`PATH` or `PATH:SYMBOL`) no longer resolves under `root`,
    or None when it all does."""
    path, _, symbol = where.partition(":")
    path, symbol = path.strip(), symbol.strip()
    if not path:
        return None
    target = root / path
    if not target.resolve().is_relative_to(root.resolve()):
        return LEAVES
    if not target.exists():
        return GONE
    if not symbol or target.is_dir():
        return None
    return symbol_problem(target, symbol)


def symbol_problem(target: Path, symbol: str) -> str | None:
    """What of `symbol` the file `target` lacks: a heading of a markdown file, else each
    dotted part as a whole word."""
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        # a file nobody may read is a problem of this item, not a reason to stop the read
        return UNREADABLE
    if target.suffix == ".md":
        return None if symbol in text else NO_HEADING
    missing = [
        part
        for part in symbol.split(".")
        if part and not re.search(rf"\b{re.escape(part)}\b", text)
    ]
    if not missing:
        return None
    named = ".".join(missing)
    return f"not in the file: {named}"
