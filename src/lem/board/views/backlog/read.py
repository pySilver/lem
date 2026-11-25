"""The read of the backlog (`board.backlog` on `main`): the items of the backlog folder of the
main checkout, and beside them the reviewer's items of its state folder, each with its head,
what git says of it, and whether the place in the code it names is still there.

It is one of the views' reads, like `gather.py`, and changes nothing. A file that does not read
is an entry that says why, never a read that stops.
"""

import re
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.board.views.backlog import head
from lem.board.views.backlog.known import known_of
from lem.board.views.backlog_read import Entry, Shelved
from lem.store.places import STATE

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from lem.board.views.backlog.known import Known
    from lem.board.views.backlog.ledger import Ledger
    from lem.board.views.world import Place

# The reviewer's items: `.lem/state/backlog/` of the main checkout, which git never sees.
REVIEWER = (STATE / "backlog").as_posix()
MARKDOWN = ".md"
PATTERN = f"*{MARKDOWN}"
LEAVES = "the path leaves the repository"
GONE = "the file is not there"
UNREADABLE = "the file cannot be read"
NO_HEADING = "the heading is not in the file"


def read(checkout: Path, place: Place, git: Ledger | None, now: datetime) -> Shelved:
    """The backlog of the main checkout `checkout` at the minute `now`, with git's answers
    from `git` (None when git is not asked)."""
    folder = place.backlog
    known = known_of(git, checkout, folder)
    mine = entries(checkout, folder, known)
    theirs = entries(checkout, REVIEWER, None)
    return Shelved(
        folder=folder,
        reviewer=REVIEWER,
        entries=(*mine, *theirs),
        read=now,
        told=known.told,
    )


def entries(checkout: Path, folder: str, known: Known | None) -> tuple[Entry, ...]:
    """The items of `folder`, by name: of the backlog folder with what git says (`known`),
    or the reviewer's (None). A file named `.md` alone is no item."""
    place = checkout / folder
    if not place.is_dir():
        return ()
    found = (path.name for path in place.glob(PATTERN))
    names = sorted(name for name in found if name != MARKDOWN)
    paths = (f"{folder}/{name}" for name in names)
    return tuple(entry(checkout, path, known) for path in paths)


def entry(checkout: Path, path: str, known: Known | None) -> Entry:
    """The item at `path`, which may not read."""
    stem = stem_of(path)
    key = f"-{stem}" if known is None else stem
    whose = Entry(path=path, key=key, reviewer=known is None)
    if known is not None:
        whose = known.marked(whose)
    try:
        raw = (checkout / path).read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        # a link to a file that moved, or a folder with an item's name: shown, not hidden
        why = error.strerror or str(error)
        return replace(whose, title=stem, bad=why)
    return headed(checkout, whose, head.parse(raw))


def headed(checkout: Path, whose: Entry, parsed: head.Head | str) -> Entry:
    """The item with its head, or with why its head does not read."""
    stem = stem_of(whose.path)
    if isinstance(parsed, str):
        return replace(whose, title=stem, bad=parsed)
    where = parsed.where
    return replace(
        whose,
        worth=parsed.worth,
        where=where,
        added_on=parsed.added,
        title=parsed.title or stem,
        text=parsed.text,
        where_problem=where_problem(checkout, where) if where else None,
    )


def stem_of(path: str) -> str:
    """The file's name without `.md`."""
    return path.rpartition("/")[2].removesuffix(MARKDOWN)


def where_problem(root: Path, where: str) -> str | None:
    """What of an item's `where` (`PATH` or `PATH:SYMBOL`) no longer resolves under `root`."""
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
    """What of `symbol` the file lacks: a markdown heading, else each dotted part as a word."""
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return UNREADABLE
    if target.suffix == MARKDOWN:
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
