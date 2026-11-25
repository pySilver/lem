"""The name of a task the board starts (`serve.slug_of` and `item_slug` on `main`): the first
five plain words of the owner's words, or the stem of the backlog item it starts from.

An item whose task ended (a dropped one is undecided again) starts again as its stem with the
first `-2`, `-3` that no task has; a task of the stem that did not end keeps it, and the start is
refused with that task.
"""

import re
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from lem.model.task import claim
from lem.store.places import SLUG

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.task import Task

# How many of the owner's words name his task.
SLUG_WORDS = 5
PLAIN = re.compile(r"[a-z0-9]+")


def slug_of(text: str, words: int | None = SLUG_WORDS) -> str:
    """The first `words` plain words of `text` (letters a to z and digits) in lower case,
    joined by hyphens, all of them with no `words`; empty when it holds none."""
    plain = PLAIN.findall(text.lower())
    return "-".join(plain[:words] if words else plain)


def by_slug(every: tuple[Record, ...]) -> dict[str, Task]:
    """Each task by its slug."""
    return {record.task.slug: record.task for record in every}


def item_slug(path: str, every: tuple[Record, ...]) -> str:
    """The slug of a task that starts from the backlog item at `path`."""
    stem = PurePosixPath(path).stem
    slug = stem if SLUG.fullmatch(stem) else slug_of(stem, None)
    known = by_slug(every)
    found = known.get(slug)
    if found is None or found.status not in claim.ENDED:
        return slug
    number = 2
    while f"{slug}-{number}" in known:
        number += 1
    return f"{slug}-{number}"
