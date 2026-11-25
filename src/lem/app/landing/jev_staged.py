"""The items Jev is asked about, written as the tip's commit has them for the one ask the
`Judge` port takes them in, by their paths, and removed after it (`land.cmd_alike` reads HEAD
on `main`, never a builder's edit in the worktree). A stand-in until the port takes an item's
facts (`notes/land-review.md`)."""

import contextlib
import shutil
from typing import TYPE_CHECKING

from lem.kernel import files

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.landing.items import BacklogItem
    from lem.ports import judge as port

type Said = tuple[port.Score, ...] | port.NotAsked


def text_of(one: BacklogItem) -> str:
    """An item as the question about it tells it: its `where`, its title, its first line."""
    head = f"---\nwhere: {one.where}\n---\n" if one.where else ""
    first = f"\n{one.first}\n" if one.first else ""
    return f"{head}# {one.title}\n{first}"


def staged(folder: Path, shelved: tuple[BacklogItem, ...]) -> dict[str, str]:
    """Write each item under `folder`; each written path with its path in the repository."""
    named: dict[str, str] = {}
    for one in shelved:
        path = folder / one.path
        path.parent.mkdir(parents=True, exist_ok=True)
        files.write_whole(path, text_of(one).encode())
        named[str(path)] = one.path
    return named


def asked_at(
    judge: port.Judge, folder: Path, told: port.Defect, shelved: tuple[BacklogItem, ...]
) -> tuple[Said, dict[str, str]]:
    """Jev's answer about the items staged under `folder`, which is removed after it, and the
    staged paths with their paths in the repository."""
    with contextlib.ExitStack() as stack:
        stack.callback(shutil.rmtree, folder, ignore_errors=True)
        named = staged(folder, shelved)
        return judge.same_items(told, tuple(named)), named
