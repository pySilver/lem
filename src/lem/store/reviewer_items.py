"""The files of the reviewer's items, shared by proposals, task claims and merge completion.

The proposal lock protects each item and its verdict. A task claim takes the workspace lock
first: the board can hold it while the child that drops an item takes the proposal lock.
"""

from os.path import normpath
from pathlib import Path
from typing import TYPE_CHECKING

from lem.kernel import locks
from lem.kernel.errors import Refusal
from lem.store.places import STATE

if TYPE_CHECKING:
    from contextlib import AbstractContextManager
    from io import TextIOWrapper

BACKLOG = "backlog"
FROM_CHECKOUT = STATE / BACKLOG
LOCK = "proposals.lock"


def relative(checkout: Path, given: str) -> str | None:
    """A reviewer's item as a checkout path, with the spelling of its directory entry."""
    if not given.strip().lower().endswith(".md"):
        return None
    named = checkout_path(checkout, given)
    if named is None or not in_backlog(named):
        return None
    if named.suffix.lower() != ".md":
        return None
    source = checkout / named
    if not source.is_file():
        return named.as_posix() if named.parent == FROM_CHECKOUT else None
    folder = checkout / FROM_CHECKOUT
    spelling = next(
        (
            entry.name
            for entry in folder.iterdir()
            if entry.name.casefold() == named.name.casefold() and entry.samefile(source)
        ),
        None,
    )
    return None if spelling is None else (FROM_CHECKOUT / spelling).as_posix()


def in_backlog(path: Path) -> bool:
    """Whether the path spells the reviewer's backlog folder, in any case."""
    return path.parent.as_posix().casefold() == FROM_CHECKOUT.as_posix()


def checkout_path(checkout: Path, given: str) -> Path | None:
    """The checkout path. Only an alias inside the reviewer's backlog can name a link."""
    root = checkout.resolve()
    whole = root / given.strip()
    lexical = Path(normpath(whole))
    if not lexical.is_relative_to(root):
        return None
    lexical = lexical.relative_to(root)
    try:
        named = whole.resolve().relative_to(root)
    except ValueError:
        return None
    if named != lexical and not (in_backlog(named) and in_backlog(lexical)):
        return None
    return named


def file_of(state: Path, path: str) -> Path:
    """The file of a reviewer's item named by its record."""
    return state / BACKLOG / Path(path).name


def held(state: Path) -> AbstractContextManager[TextIOWrapper]:
    """Hold the lock of the reviewer's items and proposal records."""
    return locks.held(state / LOCK)


def require(checkout: Path, path: str) -> None:
    """Refuse a claim when the file of its backlog item is gone."""
    if not (checkout / path).is_file():
        raise Refusal(
            "item-gone",
            f"the backlog item {path} is not in {checkout}: the owner dropped it, "
            "or it never was",
            "start the task from the owner's own words (--ask), with no --item",
        )


def remove(state: Path, path: str) -> None:
    """Remove a merged task's reviewer item under the proposal lock."""
    with held(state):
        file_of(state, path).unlink(missing_ok=True)
