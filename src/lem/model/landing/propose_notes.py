"""The notes of a pull request as `propose` reads them: the lines before the first `## `
heading, and each heading with its lines (`main:land.sections_of`, `lines_of`).

markdown-it-py reads the headings and the code blocks, so a line of a fenced block is never a
heading. A block that never closes is refused: each line after its fence would read as code,
and the step would go on with less of the notes than their writer wrote.
"""

import itertools

from lem.kernel.errors import Refusal
from lem.model.landing import propose_fences
from lem.records.base import Frozen

# The line of each heading of the notes.
type Starts = tuple[int, ...]

WHERE = "the notes of the pull request (--notes)"
HEADING = "##"


class Part(Frozen, frozen=True, kw_only=True):
    """One heading of the notes, as written, with its lines."""

    heading: str
    lines: tuple[str, ...] = ()

    @classmethod
    def cut(cls, lines: list[str], start: int, end: int) -> Part:
        """The heading at `start` with its lines up to `end`."""
        body = lines[start + 1 : end]
        return cls(heading=lines[start].strip(), lines=tuple(body))


class Notes(Frozen, frozen=True, kw_only=True):
    """The notes: the lines before the first heading, and each heading with its lines."""

    head: tuple[str, ...] = ()
    parts: tuple[Part, ...] = ()


def starts(text: str) -> Starts | Refusal:
    """The line of each `## ` heading of the notes, or the refusal of a block that never
    closes."""
    from markdown_it import (
        MarkdownIt,
    )  # only `propose` reads notes: no other step loads it

    found: list[int] = []
    for token in MarkdownIt("commonmark").parse(text):
        opened = propose_fences.unclosed(token)
        if opened is not None:
            return Refusal(
                "notes-fence",
                f"{WHERE}: line {opened} opens a code block that never closes. "
                "A heading inside the block does not count.",
                "close the fence, or put a sample that holds fences of its own in a "
                "longer fence (```` around ```), then propose again",
            )
        heading = token.type == "heading_open" and token.markup == HEADING
        if heading and token.level == 0 and token.map:
            found.append(token.map[0])
    return tuple(found)


def parsed(text: str) -> Notes | Refusal:
    """The notes by their headings, or the refusal of a block that never closes."""
    found = starts(text)
    if isinstance(found, Refusal):
        return found
    lines = text.splitlines()
    head = lines[: found[0]] if found else lines
    return Notes(head=tuple(head), parts=parts_of(lines, found))


def parts_of(lines: list[str], found: Starts) -> tuple[Part, ...]:
    """Each heading at the lines `found` with the lines up to the next."""
    ends = (*found, len(lines))
    cuts = itertools.pairwise(ends)
    return tuple(Part.cut(lines, start, end) for start, end in cuts)


def lines_of(body: tuple[str, ...]) -> tuple[str, ...]:
    """The lines of a part with text in them; none for a lone `none`."""
    said = tuple(line for line in body if line.strip())
    words = [line.strip().lower() for line in said]
    return () if words == ["none"] else said
