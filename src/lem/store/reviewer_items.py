"""The files of the reviewer's items, shared by proposals, task claims and merge completion.

The proposal lock protects each item and its verdict. A task claim takes the workspace lock
first: the board can hold it while the child that drops an item takes the proposal lock.
"""

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
    """A reviewer's item as a checkout path, whether given whole or from the checkout."""
    named = checkout / given.strip()
    if named.parent not in (
        checkout / FROM_CHECKOUT,
        checkout.resolve() / FROM_CHECKOUT,
    ):
        return None
    if not named.name.endswith(".md") or named.name == ".md":
        return None
    return (FROM_CHECKOUT / named.name).as_posix()


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
