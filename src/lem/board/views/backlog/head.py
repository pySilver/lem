"""A backlog item's head and text (`board.parse_item` on `main`): the `worth`, `where` and
`added` of its front matter, which python-frontmatter reads, the title of its `# TITLE` line
without backticks, and its text without the head and the title line."""

import re
from datetime import date
from types import MappingProxyType

import frontmatter
import yaml

from lem.records.base import Frozen

TITLE = re.compile(r"(?m)^#\s+(.+)$")
# YAML reads a bare `yes` or `no` as a truth value, which is the word written here again.
WORDS = MappingProxyType({True: "yes", False: "no"})


class Head(Frozen, frozen=True, kw_only=True):
    """What the board reads of an item's file: its worth, where, the day it was added, its
    title (empty with no `# TITLE` line) and its text."""

    worth: str | None = None
    where: str | None = None
    added: str | None = None
    title: str = ""
    text: str = ""


def parse(raw: str) -> Head | str:
    """The head of an item's text, or why its front matter does not read."""
    try:
        post = frontmatter.loads(raw)
    except yaml.YAMLError as error:
        return f"its head is not YAML: {error}"
    body = post.content
    found = TITLE.search(body)
    title = ""
    if found:
        title = found[1].replace("`", "").strip()
        body = TITLE.sub("", body, count=1)
    return Head(
        worth=word(post.get("worth")),
        where=word(post.get("where")),
        added=word(post.get("added")),
        title=title,
        text=body.strip(),
    )


def word(said: object) -> str | None:
    """A field of the head as the word written: a truth value as `yes` or `no`, a day as
    `2026-11-25`."""
    if said is None:
        return None
    if isinstance(said, bool):
        return WORDS[said]
    if isinstance(said, date):
        return said.isoformat()
    return str(said).strip()
