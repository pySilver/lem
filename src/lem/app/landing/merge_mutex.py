"""The workspace's merge lock file and the task it names."""

from typing import TYPE_CHECKING

import msgspec

from lem.kernel.errors import Refusal
from lem.records.base import Frozen
from lem.store import steps

if TYPE_CHECKING:
    from io import TextIOWrapper
    from pathlib import Path


class Holder(Frozen, frozen=True, kw_only=True):
    """Who holds the merge lock: the task and its process."""

    task: str
    pid: int


def holder_of(path: Path) -> str | None:
    """The task whose living process holds the merge lock, as its file names it."""
    try:
        holder = msgspec.json.decode(path.read_bytes(), type=Holder)
    except OSError, msgspec.DecodeError:
        return None
    return holder.task if steps.alive(holder.pid) else None


def opened(path: Path, slug: str) -> TextIOWrapper:
    """Open the lock file, or tell the owner how to repair it."""
    try:
        return path.open("a+", encoding="utf-8")
    except OSError as error:
        raise Refusal(
            "merge-lock",
            f"the merge lock {path} cannot be opened: {error.strerror}",
            f"the owner fixes access to the lock or removes it if it is not a file, "
            f"then runs lem land merge {slug} again",
        ) from error
