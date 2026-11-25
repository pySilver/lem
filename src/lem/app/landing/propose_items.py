"""What git shows of the backlog's items at a proposal: each item the branch adds, with its
title and `worth` as the tip's file says them (python-frontmatter reads its head), and which
paths the tip holds."""

from types import MappingProxyType
from typing import TYPE_CHECKING

import frontmatter

from lem.model.landing.propose_facts import BACKLOG, Filing

if TYPE_CHECKING:
    from pathlib import Path

    from lem.ports.git import Git

UTF8 = "utf-8"
WORDS = MappingProxyType({True: "yes", False: "no"})
# The commits a proposal compares: the branch's merge base with the base, and its tip.
type Span = tuple[str, str]
type Paths = tuple[str, ...]
type Heads = tuple[Filing, ...]


def text(found: bytes | None) -> str | None:
    """A file's bytes as text, or None for a file that is not there."""
    return None if found is None else found.decode(UTF8, errors="replace")


def head_of(found: bytes, path: str) -> Filing:
    """An item's title (the first line after its head, a `# ` heading) and its `worth`."""
    post = frontmatter.loads(text(found) or "")
    lines = post.content.splitlines()
    first = next(filter(str.strip, lines), "")
    title = first.removeprefix("# ").strip() if first.startswith("# ") else None
    return Filing(path=path, title=title, worth=worth_of(post.get("worth")))


def worth_of(said: object) -> str | None:
    """An item's `worth` as the word written: YAML reads a bare `no` or `yes` as a truth
    value, which is the word here again."""
    if isinstance(said, bool):
        return WORDS[said]
    if said is None:
        return None
    return str(said).strip().lower()


def added(git: Git, where: Path, commits: Span, paths: Paths) -> tuple[Filing, ...]:
    """Each item the branch adds to the backlog folder, with its head at the tip."""
    found = (item_at(git, where, commits, path) for path in paths)
    return tuple(filter(None, found))


def item_at(git: Git, where: Path, commits: Span, path: str) -> Filing | None:
    """The item at `path` when the branch adds it to the backlog folder, with its head at
    the tip; None for any other path."""
    since, tip = commits
    if not path.startswith(f"{BACKLOG}/"):
        return None
    if git.show(where, since, path) is not None:
        return None
    shown = git.show(where, tip, path)
    return None if shown is None else head_of(shown, path)


def held(git: Git, where: Path, tip: str, paths: set[str]) -> Heads:
    """Each of `paths` the tip holds, with its head when it is an item."""
    found = (head_at(git, where, tip, path) for path in sorted(paths))
    return tuple(filter(None, found))


def head_at(git: Git, where: Path, tip: str, path: str) -> Filing | None:
    """The head of the file at `path` in the tip; None when the tip lacks it."""
    shown = git.show(where, tip, path)
    return None if shown is None else head_of(shown, path)
