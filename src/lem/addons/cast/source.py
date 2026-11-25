"""Read project files from the active worktree or from the default branch."""

from pathlib import Path
from typing import TYPE_CHECKING

from lem.kernel import files
from lem.records.base import Frozen
from lem.store.guard import writable

if TYPE_CHECKING:
    from lem.addons.cast import refs

CAST = ".lem/personas"
PROFILE = ".lem/profile.md"
INDEX = "README.md"


class Located(Frozen, frozen=True, kw_only=True):
    """Where the panel reads a path and where it came from."""

    path: str
    source: str


def paths_of(folder: Path) -> tuple[Path, ...]:
    """The personas of a folder, apart from their index."""
    return tuple(sorted(filter(is_persona, folder.glob("*.md"))))


def is_persona(path: Path) -> bool:
    """An ordinary Markdown file, other than the cast's index."""
    return path.name != INDEX and path.suffix == ".md" and path.is_file()


def remote_cast(git: refs.Checkout, ref: str, state: Path) -> Located | None:
    """Publish a copy of the cast at one commit."""
    commit = git.text("rev-parse", "--verify", ref)
    paths = remote_paths(git, commit)
    if not any(path.name != INDEX for path in paths):
        return None
    writable(state)
    parent = state / "personas-cast" / commit
    for path in paths:
        raw = git.blob(commit, path.as_posix())
        files.publish(parent / path.name, raw)
    parent.touch()
    return Located(path=str(parent), source=label(ref, commit))


def remote_paths(git: refs.Checkout, ref: str) -> tuple[Path, ...]:
    """The Markdown files directly under the cast directory."""
    raw = git.text("ls-tree", "-z", "--name-only", ref, f"{CAST}/")
    names = (name for name in raw.split("\0") if name.endswith(".md"))
    return tuple(map(Path, names))


def label(ref: str, commit: str) -> str:
    """The branch and abbreviated commit the owner sees."""
    shown = ref.removeprefix("refs/heads/").removeprefix("refs/remotes/")
    short = commit[:9]
    return f"{shown} at {short}"


def remote_profile(git: refs.Checkout, ref: str, state: Path) -> Located | None:
    """Share one published copy for each distinct profile."""
    commit = git.text("rev-parse", "--verify", ref)
    blob = git.text("rev-parse", "--verify", f"{commit}:{PROFILE}")
    if not blob:
        return None
    writable(state)
    path = state / "personas-profile" / f"{blob}.md"
    files.publish(path, git.blob(commit, PROFILE))
    path.touch()
    return Located(path=str(path), source=label(ref, commit))
