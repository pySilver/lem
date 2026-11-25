"""The head of a reviewer's item as python-frontmatter reads it: its `worth`, and the proposals
it names (`project.item_front` and `item_proposals` on `main`)."""

from typing import TYPE_CHECKING

import frontmatter
import yaml

from lem.addons.proposals import names
from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path


class Head(Frozen, frozen=True, kw_only=True):
    """An item's worth as written (YAML's `no` is the word again), and the names of the
    proposals it names, none when it names no proposal of a record."""

    worth: str | None = None
    proposals: tuple[str, ...] = ()


def head_of(text: str) -> Head:
    """The head of the item `text`; an item with no head, or a head that does not read, has
    an empty one."""
    try:
        meta = frontmatter.loads(text).metadata
    except yaml.YAMLError:
        return Head()
    return Head(
        worth=worth_of(meta.get("worth")), proposals=proposals_of(meta.get("proposals"))
    )


def worth_of(said: object) -> str | None:
    """An item's `worth` as the word written: YAML reads a bare `no` or `yes` as a truth
    value, which is the word here again."""
    if isinstance(said, bool):
        return "yes" if said else "no"
    return None if said is None else str(said).strip().lower()


def proposals_of(given: object) -> tuple[str, ...]:
    """The names of a head's `proposals`, a list or one line joined by commas; none when one
    of them is no proposal's name."""
    listed = given.split(",") if isinstance(given, str) else given
    if not isinstance(listed, list):
        return ()
    stripped = (str(name).strip() for name in listed)
    found = tuple(filter(None, stripped))
    known = all(map(names.parsed, found))
    return found if known else ()


def read(path: Path) -> Head:
    """The head of an item. An absent file or a link holds no proposal."""
    if path.is_symlink():
        return Head()
    try:
        return head_of(path.read_text(encoding="utf-8"))
    except FileNotFoundError, IsADirectoryError:
        return Head()


def refuted_items(existing: dict[Path, Head]) -> dict[str, list[Path]]:
    """The `worth: no` items of the reviewer's folder, by the one proposal each names: what a
    verdict wrote for a refuted proposal."""
    found: dict[str, list[Path]] = {}
    for path, head in existing.items():
        if head.worth == "no" and len(head.proposals) == 1:
            found.setdefault(head.proposals[0], []).append(path)
    return found


def passed_names(existing: dict[Path, Head]) -> dict[frozenset[str], str]:
    """Each passed item's filename, by the set of proposals it names."""
    return {
        frozenset(head.proposals): path.name
        for path, head in existing.items()
        if head.worth == "later" and head.proposals
    }
