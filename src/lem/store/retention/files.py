"""What retention removes, or in a dry run would remove, inside one state folder (`project.
Remover` on `main`).

A path is touched only when it is no link and its folder resolves inside the state folder: a
link is never followed and never removed, and is named among what was skipped. Each removal that
fails is named with the error, and the others go on, so that the next run finishes it.
"""

import os
import stat
from dataclasses import dataclass, field
from pathlib import Path

from lem.kernel.errors import Refusal
from lem.records.base import Frozen

LINK = "a link, which prune never follows and never removes"


class Skipped(Frozen, frozen=True, kw_only=True):
    """A path retention left as it is, and why."""

    path: str
    why: str


class Failed(Frozen, frozen=True, kw_only=True):
    """A removal that failed, and the error."""

    path: str
    error: str


def shown(top: Path, path: Path) -> str:
    """A path as the answer names it: inside the state folder `top` when it is there."""
    if path.is_relative_to(top):
        return path.relative_to(top).as_posix()
    return str(path)


def refused_link(state: Path) -> None:
    """Refuse a state folder that is a link: retention removes nothing through one."""
    if state.is_symlink():
        raise Refusal(
            "state-link",
            f"{state} is a link, and prune removes nothing through a link",
            "make the state folder a folder of the main checkout",
        )


@dataclass(kw_only=True)
class Removal:
    """The removals of one run in the state folder `top`, and what they skipped and failed."""

    top: Path
    dry: bool
    skipped: list[Skipped] = field(default_factory=list)
    failed: list[Failed] = field(default_factory=list)

    def fail(self, path: Path, error: OSError) -> None:
        """Name a removal that failed, with the error."""
        named = shown(self.top, path)
        self.failed.append(Failed(path=named, error=str(error)))

    def skip(self, path: Path, why: str) -> None:
        """Name a path that stays, and why."""
        named = shown(self.top, path)
        self.skipped.append(Skipped(path=named, why=why))

    def link(self, path: Path) -> bool:
        """Whether `path` is a link, which is then named among what was skipped."""
        if path.is_symlink():
            self.skip(path, LINK)
            return True
        return False

    def inside(self, path: Path) -> bool:
        """Whether `path` is no link, and its folder is inside the state folder."""
        if self.link(path):
            return False
        parent = path.parent.resolve()
        if parent == self.top or parent.is_relative_to(self.top):
            return True
        self.skip(path, f"not inside the state folder {self.top}")
        return False

    def removed(self, path: Path) -> int | None:
        """Remove one plain file; its bytes, or None when it stays."""
        if not self.inside(path):
            return None
        try:
            facts = path.lstat()
        except OSError as error:
            self.fail(path, error)
            return None
        if not stat.S_ISREG(facts.st_mode):
            self.skip(path, "not a plain file")
            return None
        return facts.st_size if self.unlinked(path) else None

    def unlinked(self, path: Path) -> bool:
        """Unlink the file unless the run is dry; whether it went, or would go."""
        if self.dry:
            return True
        try:
            path.unlink()
        except OSError as error:
            self.fail(path, error)
            return False
        return True


def emptied(removal: Removal, folder: Path) -> None:
    """Remove the folders under `folder` that hold nothing now, deepest first; `folder` itself
    stays, and so does a link. A dry run removes none."""
    if removal.dry:
        return
    for at, inner, _ in os.walk(folder, topdown=False):
        for name in inner:
            rmdir(removal, Path(at) / name)


def rmdir(removal: Removal, path: Path) -> None:
    """Remove an empty folder that is no link."""
    if path.is_symlink() or any(path.iterdir()):
        return
    try:
        path.rmdir()
    except OSError as error:
        removal.fail(path, error)
