"""An item of the backlog as rule 6 of the builder's standing rules gives its format, read from
its text, and the item `file` writes for a defect a review saw outside the change.

An item is a file of the backlog folder: between two `---` lines its `worth`, `where` and
`added`, then `# TITLE`, then the run in prose, and for a `worth: no` item the line `Decided
against: REASON`. A defect is the same as an item when the item has its `where`, its title and
its run, word for word (`land.holds` on `main`); any other text of the body (the owner's reason,
a later note) leaves it the same defect.
"""

import re

from lem.records.base import Frozen

FRONT = re.compile(r"---\n(.*?)\n---\n", re.DOTALL)
DECIDED = re.compile(r"(?i)\s*decided against:")
# What no paragraph holds: the run is found in the body as whole paragraphs, in order.
SEPARATOR = "\0"
GIVEN = re.compile(r"(?i)\s*decided against:\s*\S")


class BacklogItem(Frozen, frozen=True, kw_only=True):
    """An item of the backlog as its file says: its path, `where`, title and `worth` (as
    written, lowercase), its body's paragraphs without the `Decided against:` line, its first
    line, and whether that line gives a reason."""

    path: str
    where: str | None = None
    title: str
    worth: str | None = None
    paragraphs: tuple[str, ...] = ()
    first: str | None = None
    reason: bool = False


class Defect(Frozen, frozen=True, kw_only=True):
    """A defect as an item is written for it: its place, its title and its run."""

    where: str
    title: str
    what: str


def paragraphs(text: str) -> tuple[str, ...]:
    """The paragraphs of a text, each stripped, as `file` writes them: a blank line between
    two."""
    parts = re.split(r"\n[ \t]*\n", text.strip())
    return tuple(part.strip() for part in parts if part.strip())


def front_of(text: str) -> tuple[dict[str, str], list[str]]:
    """The front matter of an item's text, each key with its value stripped, and the lines
    after it."""
    head = FRONT.match(text)
    if head is None:
        return {}, text.strip().splitlines()
    pairs = (line.partition(":") for line in head.group(1).splitlines())
    front = {key.strip(): rest.strip() for key, _, rest in pairs}
    return front, text[head.end() :].strip().splitlines()


def read(path: str, text: str) -> BacklogItem | None:
    """The item at `path` from its text; None for a file that is no item (no `# TITLE`)."""
    front, lines = front_of(text)
    if not lines or not lines[0].startswith("# "):
        return None
    body = lines[1:]
    kept = "\n".join(line for line in body if not DECIDED.match(line))
    return BacklogItem(
        path=path,
        where=front.get("where") or None,
        title=lines[0][2:].strip(),
        worth=front.get("worth", "").lower() or None,
        paragraphs=paragraphs(kept),
        first=next((line.strip() for line in body if line.strip()), None),
        reason=any(GIVEN.match(line) for line in body),
    )


def holds(found: BacklogItem | None, defect: Defect) -> bool:
    """Whether the item is this defect: its `where`, its title, and its run as paragraphs of
    the body, word for word."""
    if found is None:
        return False
    if (found.where, found.title) != (defect.where, defect.title):
        return False
    run = SEPARATOR.join(paragraphs(defect.what))
    body = SEPARATOR.join(found.paragraphs)
    return f"{SEPARATOR}{run}{SEPARATOR}" in f"{SEPARATOR}{body}{SEPARATOR}"
