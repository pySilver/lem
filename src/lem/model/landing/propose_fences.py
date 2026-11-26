"""The line of a fenced block of the notes with no explicit close, for `propose`'s refusal
(`main:criteria.fenced_lines`)."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from markdown_it.token import Token


def unclosed(token: Token) -> int | None:
    """The opening line of a fence the parser ends with its container, counted from 1."""
    if token.type != "fence" or token.map is None:
        return None
    first, end = token.map
    # The map counts both fences, while the content holds just the lines between them.
    # The last content line at EOF may have no newline.
    body = token.content.count("\n")
    if token.content and not token.content.endswith("\n"):
        body += 1
    return first + 1 if end - first == body + 1 else None
