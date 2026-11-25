"""Read a regular file below a task, with the open confined to the checked path."""

import os
import stat
from contextlib import ExitStack
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path

DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
REGULAR = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK


def task_root(state: Path, slug: str) -> Path | None:
    """A resolved task folder below the workspace's task directory and state."""
    tasks = (state / "tasks").resolve()
    task = places.task_folder(state, slug).resolve()
    return task if state in tasks.parents and tasks in task.parents else None


def read_resolved(found: Path) -> bytes | None:
    """Refuse a link put in the resolved path before any component is opened."""
    with ExitStack() as stack:
        parent = os.open(found.anchor, DIRECTORY)
        stack.callback(os.close, parent)
        for part in found.parts[1:-1]:
            parent = os.open(part, DIRECTORY, dir_fd=parent)
            stack.callback(os.close, parent)
        descriptor = os.open(found.name, REGULAR, dir_fd=parent)
        stack.callback(os.close, descriptor)
        if stat.S_ISREG(os.fstat(descriptor).st_mode):
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                return stream.read()
    return None


def read(state: Path, slug: str, path: str, *, media: bool = False) -> bytes | None:
    """Read a visible file in the task folder, or strictly below its media folder."""
    parts = [part for part in path.split("/") if part]
    if not parts or any(part.startswith(".") for part in parts):
        return None
    try:
        return inside(state.resolve(), slug, parts, media=media)
    except OSError, Refusal, ValueError:
        return None


def inside(state: Path, slug: str, parts: list[str], *, media: bool) -> bytes | None:
    """Resolve the roots and the file before the descriptor-relative open."""
    task = task_root(state, slug)
    if task is None:
        return None
    root = (task / "media").resolve() if media else task
    if media and task not in root.parents:
        return None
    found = root.joinpath(*parts).resolve()
    if root not in found.parents:
        return None
    return read_resolved(found)
