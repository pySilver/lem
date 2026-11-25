"""`session.md`: the first read of a task's new session, in the task's folder.

Its first line names `prompts/session.md` by its place under the root that `lem version` prints,
never by the folder of the Lem that wrote it: the plugin's folder changes with each update, and
a session reads the texts of the Lem whose `lem` it runs. The lines after it are the facts the
session starts from; `phase:` is also what the PreCompact hook reads (`hooks/precompact.py`).
"""

from typing import TYPE_CHECKING

from lem.kernel import files
from lem.store import guard

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.app.sessions.here import Here
    from lem.records.task import Task

BRIEF = "session.md"
FIRST = (
    "Read `skills/lem/prompts/session.md` in the folder that `lem version` prints as `root`, "
    "and follow it; when `lem version` fails, stop and say that `lem` is not on the PATH, "
    "with `lem doctor` as the check."
)


def write(folder: Path, facts: Mapping[str, str]) -> Path:
    """Write the brief of the task in `folder`, whole, with its `facts` one a line; its path."""
    lines = (f"{name}: {fact}" for name, fact in facts.items())
    text = "\n".join((FIRST, "", *lines, ""))
    path = folder / BRIEF
    guard.writable(folder.parents[1])
    files.write_whole(path, text.encode())
    return path


def facts(here: Here, task: Task, phase: str, why: str) -> dict[str, str]:
    """The lines of the brief after its first: the task, its phase and why it opened, and the
    task's folder, main checkout and worktree."""
    worktree = here.worktree(task.slug)
    return {
        "task": task.slug,
        "phase": phase,
        "opened because": why,
        "task directory": str(here.folder(task.slug)),
        "main checkout": str(here.where.checkout),
        "worktree": str(worktree) if worktree else "none yet",
    }
