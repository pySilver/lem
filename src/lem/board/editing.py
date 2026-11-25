"""The machine's list of workspaces, changed by hand: `lem serve add DIR` and `lem serve remove
DIR` (`serve --add` and `serve --remove` on `main`).

Each takes the main checkout of the repository DIR is in, from a task's worktree too. A checkout
with no `.lem/` is refused, since Lem is not set up there; a repository that is gone is still
taken out by the path it had, and one not on the list is refused with the way to see the list.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.board import workspaces
from lem.kernel import folders
from lem.kernel.errors import Refusal
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path


class Changed(msgspec.Struct, frozen=True, kw_only=True):
    """What `add` or `remove` did: the checkout, whether the list changed, and the list."""

    checkout: str
    changed: bool
    workspaces: tuple[str, ...]


def added(home: Path, folder: Path) -> Changed:
    """Put the main checkout of `folder` on the list."""
    space = places.workspace(folder)
    path = str(space.checkout.resolve())
    changed = workspaces.changed(home, path, add=True)
    return Changed(checkout=path, changed=changed, workspaces=workspaces.listed(home))


def checkout_of(folder: Path) -> str:
    """The main checkout of `folder`, or its own path when its repository is gone."""
    try:
        return str(places.workspace(folder).checkout.resolve())
    except Refusal:
        return str(folder.absolute())


def removed(home: Path, folder: Path) -> Changed:
    """Take the main checkout of `folder` off the list; refused when it is not there."""
    path = checkout_of(folder)
    if path not in workspaces.listed(home):
        raise Refusal(
            "not-listed",
            f"{path} is not in the list of workspaces",
            "lem serve list shows the list",
        )
    folders.home_marked(home)
    workspaces.changed(home, path, add=False)
    return Changed(checkout=path, changed=True, workspaces=workspaces.listed(home))
