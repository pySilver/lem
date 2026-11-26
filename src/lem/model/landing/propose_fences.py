"""A fenced block of the notes that never closes (`main:criteria.fenced_lines`): its line,
for `propose`'s refusal. markdown-it-py runs a block that never closes to the end of the notes;
whether the last line closes it is CommonMark's rule: at most three spaces before the fence,
and nothing but its character after it."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from markdown_it.token import Token

# The indent at which a line is code in CommonMark, and no fence.
CODE = 4


def unclosed(token: Token, lines: list[str]) -> int | None:
    """The line of a fenced block that runs to the end of the notes with no closing fence,
    counted from 1; None for any other token."""
    # CommonMark gives each fence a map. Other tokens do not use these values.
    first, end = token.map or (0, 0)  # pragma: no mutate
    if token.type != "fence" or end < len(lines):
        return None
    last = lines[end - 1]
    if end - 1 > first and closes(last, token.markup):
        return None
    return first + 1


def closes(line: str, markup: str) -> bool:
    """Whether a line closes a fence opened with `markup`: at most three spaces before it,
    and nothing but the fence's character after it (CommonMark: four spaces make it code)."""
    text = line.lstrip(" ")
    if len(line) - len(text) >= CODE:
        return False
    bare = text.rstrip()
    # Every character in a CommonMark fence is the same.
    return bare.startswith(markup) and not bare.strip(markup[0])  # pragma: no mutate
