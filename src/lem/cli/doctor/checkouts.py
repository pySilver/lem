"""The checkouts the call of `lem doctor` is in, and Claude Code's settings files.

A file of a project's own that git does not track is in its main checkout only, so a task's
worktree has no copy of it: the rows look in the checkout of the call, then in its main
checkout. Both are read from the files git keeps (`store.places.common_dir`), with no git
started. A settings file of Claude Code is the agent's own and may read any way: one that is
absent or reads another way is an empty table.
"""

import json
from typing import TYPE_CHECKING

from lem.store.places import common_dir

if TYPE_CHECKING:
    from pathlib import Path

type Table = dict[str, object]


def dot_git(folder: Path) -> Path | None:
    """The `.git` of the checkout `folder` is in; None outside one."""
    start = folder.resolve()
    for one in (start, *start.parents):
        if (one / ".git").exists():
            return one / ".git"
    return None


def roots(folder: Path) -> tuple[Path, ...]:
    """The checkout `folder` is in, then its main checkout when that is another, by their real
    paths; none outside a repository."""
    found = dot_git(folder)
    if found is None:
        return ()
    try:
        main = common_dir(found).parent.resolve()
    except OSError, UnicodeDecodeError:
        return (found.parent,)
    if main == found.parent:
        return (main,)
    return (found.parent, main)


def main_checkout(folder: Path) -> Path | None:
    """The main checkout of the repository `folder` is in; None outside one."""
    found = roots(folder)
    return found[-1] if found else None


def table_of(path: Path) -> Table:
    """The JSON object a settings file of Claude Code holds; empty when it is absent or holds
    anything else."""
    try:
        read = json.loads(path.read_text(encoding="utf-8"))
    except OSError, ValueError:
        return {}
    return read if isinstance(read, dict) else {}


def files_of(home: Path, root: Path | None) -> tuple[Path, ...]:
    """Claude Code's settings files for the repository `root` (None: outside one), in the
    order they say a thing first: its local settings, its shared ones, then the user's."""
    user = home / ".claude" / "settings.json"
    if root is None:
        return (user,)
    claude = root / ".claude"
    return (claude / "settings.local.json", claude / "settings.json", user)
