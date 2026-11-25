"""Where a workspace keeps Lem's state: `.lem/state/` of its main checkout, which git never
sees, a folder for each task, and the shared locks (the design's part 3, "Elsewhere").

The folder holds a `.gitignore` of `*`, which hides the folder and itself with no change to a
file git tracks. A slug is a folder's name, so it is lower-case words and digits joined by
hyphens, and anything else is refused before a path is made of it.
"""

import re
from pathlib import Path

from lem.kernel.errors import Refusal

STATE = Path(".lem") / "state"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def state_of(checkout: Path) -> Path:
    """The state folder of the main checkout `checkout`, made with its ignore file when it is
    not there."""
    state = checkout / STATE
    state.mkdir(parents=True, exist_ok=True)
    ignore = state / ".gitignore"
    if not ignore.is_file():
        ignore.write_text("*\n", encoding="utf-8")
    return state


def task_folder(state: Path, slug: str) -> Path:
    """The folder of the task `slug` in `state`; a slug that is no such name is refused."""
    if not SLUG.fullmatch(slug):
        raise Refusal(
            "slug",
            f"{slug!r} is no task's name",
            "name a task by lower-case words and digits joined by hyphens: fix-the-login",
        )
    return state / "tasks" / slug


def locks_folder(state: Path) -> Path:
    """The folder of the workspace's shared locks (the claim, the merge, the serial checks),
    made when it is not there."""
    folder = state / "locks"
    folder.mkdir(parents=True, exist_ok=True)
    return folder
