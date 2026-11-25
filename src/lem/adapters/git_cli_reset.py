"""The ignored local paths a reset would replace, including file and directory swaps."""

import os
from pathlib import Path
from typing import TYPE_CHECKING
from unicodedata import normalize

from lem.adapters.git_cli_names import shown
from lem.adapters.git_cli_shell import all_words
from lem.ports.git_facts import GitRefused

if TYPE_CHECKING:
    from collections.abc import Iterable

    from lem.adapters.git_cli_shell import Shell

type DiskEntry = tuple[int, int, str]


def ignored_collision(
    shell: Shell, where: Path, before: str, target: str
) -> GitRefused | None:
    """Refuse a reset that would overwrite an ignored local path."""
    ignored = shell.output(
        where, "ls-files", "--others", "--ignored", "--exclude-standard", "-z"
    )
    if not ignored:
        return None
    diff = ("diff", "--name-only", "--no-renames", "--diff-filter=AT", "-z")
    added = shell.raw(where, *diff, before, target, "--")
    if added.returncode:
        return GitRefused(said=all_words(added.stderr.decode(errors="replace")))
    collision = first_collision(where, ignored, added.stdout.split(b"\0"))
    if collision is None:
        return None
    return GitRefused(said=f"the reset would overwrite an ignored path: {collision}")


def first_collision(where: Path, ignored: bytes, added: list[bytes]) -> str | None:
    """An ignored file at, within or above a new tracked path."""
    paths = {Path(os.fsdecode(raw)) for raw in added if raw}
    targets = disk_entries(where, paths)
    blocked = disk_entries(where, (parent for path in paths for parent in path.parents))
    blocked.update(targets)
    for raw in ignored.rstrip(b"\0").split(b"\0"):
        local = Path(os.fsdecode(raw))
        if disk_entry(where, local) in blocked:
            return shown(raw)
        if targets.intersection(disk_entry(where, parent) for parent in local.parents):
            return shown(raw)
    return None


def disk_entries(where: Path, paths: Iterable[Path]) -> set[DiskEntry | None]:
    """The distinct entries that exist at these paths."""
    return {disk_entry(where, path) for path in set(paths)} - {None}


def disk_entry(where: Path, path: Path) -> DiskEntry | None:
    """Identify a path even when the file system accepts another spelling."""
    try:
        found = (where / path).lstat()
    except FileNotFoundError, NotADirectoryError:
        return None
    # A folded name keeps unrelated hard links apart where their inode is the same.
    spelling = normalize("NFC", str(path)).casefold()
    return found.st_dev, found.st_ino, spelling
