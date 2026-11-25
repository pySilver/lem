"""The few words of YAML a rule file's `paths:` is written in: a comment, a quoted glob, and a
flow list. Lem reads only these, not YAML as a whole, so that a frontmatter reads the same way
on every machine.
"""

from itertools import pairwise
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

QUOTES = "\"'"
COMMENT = "#"


def outside(text: str) -> Iterator[tuple[int, str]]:
    """Each character of `text` outside quotes, with its place; a quote itself is none."""
    quote = ""
    for index, char in enumerate(text):
        if quote:
            quote = "" if char == quote else quote
        elif char in QUOTES:
            quote = char
        else:
            yield index, char


def bare(text: str) -> str:
    """The text without a YAML comment: a `#` at the start or after a space, outside quotes."""
    cuts = (index for index, _ in outside(text) if comment_at(text, index))
    return text[: next(cuts, len(text))].strip()


def comment_at(text: str, index: int) -> bool:
    """Whether a comment starts at `index`: a `#` at the start or after a space."""
    opens = not index or text[index - 1].isspace()
    return text[index] == COMMENT and opens


def written(line: str) -> bool:
    """Whether a line says something: it is not empty and not a comment."""
    said = line.strip()
    return bool(said) and not said.startswith(COMMENT)


def flow_items(inner: str) -> list[str]:
    """The items of a flow list, the text between its brackets, cut at each comma outside
    quotes and outside a brace group."""
    cuts = (-1, *top_commas(inner), len(inner))
    pieces = pairwise(cuts)
    return [inner[start + 1 : end] for start, end in pieces]


def top_commas(inner: str) -> Iterator[int]:
    """The place of each comma outside quotes and outside a brace group."""
    level = 0
    for index, char in outside(inner):
        level += (char == "{") - (char == "}")
        if char == "," and not level:
            yield index


def unquoted(word: str) -> str:
    """A glob without the quotes around it."""
    first = word[:1]
    closes = len(word) > 1 and word.endswith(first)
    return word[1:-1] if closes and first in QUOTES else word
