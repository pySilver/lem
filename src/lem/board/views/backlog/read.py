"""The read of the backlog (`board.backlog` on `main`): the items of the backlog folder of the
main checkout, and beside them the reviewer's items of its state folder, each with its head,
what git says of it, and whether the place in the code it names is still there.

It is one of the views' reads, like `gather.py`, and changes nothing. A file that does not read
is an entry that says why, never a read that stops.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.board.views.backlog import head
from lem.board.views.backlog.known import known_of
from lem.board.views.backlog.where import where_problem
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
    return tuple(entry(checkout, named(folder, name), known) for name in names)


def named(folder: str, name: str) -> str:
    """The path of the file `name` of `folder`, from the main checkout's root."""
    return f"{folder}/{name}"


def entry(checkout: Path, path: str, known: Known | None) -> Entry:
    """The item at `path`, which may not read."""
    whose = blank(path, known)
    try:
        raw = (checkout / path).read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        # a link to a file that moved, or a folder with an item's name: shown, not hidden
        why = error.strerror or str(error)
        return replace(whose, title=stem_of(path), bad=why)
    return headed(checkout, whose, head.parse(raw))


def blank(path: str, known: Known | None) -> Entry:
    """The item at `path` before its file is read: its key (`-STEM` for a reviewer's item,
    so that two items of one stem stay two), and what git says of it."""
    stem = stem_of(path)
    if known is None:
        return Entry(path=path, key=f"-{stem}", reviewer=True)
    return known.marked(Entry(path=path, key=stem))


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
