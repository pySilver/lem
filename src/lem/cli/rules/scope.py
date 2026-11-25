"""The globs a rule file scopes itself to, or None for one that covers every path.

The one format read is Claude Code's: `paths:` in the file's frontmatter, as a block list, a
flow list or one glob. A `paths:` that names no glob is refused: whether the file then covers
every path or none is not for Lem to guess.
"""

import re
from itertools import takewhile
from typing import TYPE_CHECKING

from lem.cli.rules.frontmatter import frontmatter
from lem.cli.rules.yaml_words import bare, flow_items, unquoted, written
from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from pathlib import Path

PATHS = re.compile(r"paths\s*:")
LIST_ENTRY = re.compile(r"\s*-\s+(.*)$")
SCOPE = "rule-scope"
ONE_GLOB_A_LINE = 'write each glob under it as `  - "GLOB"`'


def rule_scope(path: Path, name: str) -> tuple[str, ...] | None:
    """The globs of the rule file at `path`, which messages call `name`."""
    # utf-8-sig: a byte order mark before the first `---` must not turn a scoped rule into
    # one for every path
    block = frontmatter(path.read_text(encoding="utf-8-sig", errors="replace"))
    at = paths_line(block)
    if at is None:
        return None
    words = entries(block, at, name)
    globs = tuple(unquoted(word.strip()) for word in words)
    if not globs or not all(globs):
        raise Refusal(
            SCOPE,
            f"{name}: its `paths:` names no glob",
            f"{ONE_GLOB_A_LINE}, or take the line out so the file covers every path",
        )
    return globs


def paths_line(block: list[str]) -> int | None:
    """The line of the frontmatter that holds the key `paths:`, or None."""
    found = (index for index, line in enumerate(block) if PATHS.match(line))
    return next(found, None)


def entries(block: list[str], at: int, name: str) -> list[str]:
    """The words `paths:` lists, on its own line or in the lines under it."""
    rest = bare(block[at].split(":", 1)[1])
    if rest.startswith("[") and rest.endswith("]"):
        return flow_items(rest[1:-1])
    if rest:
        return [rest]
    return block_items(block[at + 1 :], name)


def block_items(lines: list[str], name: str) -> list[str]:
    """The items of a block list, up to the next key; an indented line that is no item is
    refused."""
    listed = takewhile(under_paths, filter(written, lines))
    return [glob_of(line, name) for line in listed]


def under_paths(line: str) -> bool:
    """Whether a line belongs to the list: an item, or indented under the key."""
    return bool(LIST_ENTRY.match(line)) or line[:1].isspace()


def glob_of(line: str, name: str) -> str:
    """The glob of one item of the list; a line that is no item is refused."""
    entry = LIST_ENTRY.match(line)
    if entry is None:
        raise Refusal(
            SCOPE,
            f"{name}: a line under `paths:` is not a list item ({line.strip()!r})",
            ONE_GLOB_A_LINE,
        )
    return bare(entry.group(1))
