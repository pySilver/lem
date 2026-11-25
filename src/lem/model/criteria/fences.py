"""The code blocks of a markdown text, at any indent (`criteria.fences` on `main`): a line inside
one is code, never a heading or a criterion.

A fence closes only on a line of its own character, at least as long as the one that opened it,
with nothing after it: a shorter fence inside is a part of the block. A backtick fence whose info
holds a backtick opens nothing, as in CommonMark.
"""

import re

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.records.base import Frozen

MARK = re.compile(r"( *)(`{3,}|~{3,})(.*)$")
TICK = "`"


class Fence(Frozen, frozen=True, kw_only=True):
    """One block: its first and last line (the fences), its info word, its indent, and its
    fence's character and length, which the closing fence must match."""

    first: int
    last: int
    word: str
    indent: int
    mark: str
    length: int


# The blocks that closed, and the one still open at the end, or None.
type Scan = tuple[tuple[Fence, ...], Fence | None]


def opening(index: int, line: str) -> Fence | None:
    """The block `line` opens, or None when it opens none."""
    found = MARK.match(line)
    if found is None:
        return None
    indent, mark, rest = found.groups()
    if mark.startswith(TICK) and TICK in rest:
        return None
    return fence_at(index, len(indent), mark, rest)


def fence_at(index: int, indent: int, mark: str, rest: str) -> Fence:
    """The block that opens at line `index` with `mark`, its info word the first of `rest`."""
    words = rest.split() or [""]
    word = words[0].lower()
    char, length = mark[0], len(mark)
    return Fence(
        first=index, last=index, word=word, indent=indent, mark=char, length=length
    )


def closes(opened: Fence, line: str) -> bool:
    """Whether `line` closes the block `opened`."""
    found = MARK.match(line)
    if found is None or found[3].strip():
        return False
    mark = found[2]
    return mark[0] == opened.mark and len(mark) >= opened.length


def scanned(lines: list[str]) -> Scan:
    """The blocks of `lines` that close, and the one still open at the end, or None."""
    found: list[Fence] = []
    opened: Fence | None = None
    for index, line in enumerate(lines):
        if opened is None:
            opened = opening(index, line)
        elif closes(opened, line):
            found.append(replace(opened, last=index))
            opened = None
    return tuple(found), opened


def fences(lines: list[str]) -> tuple[Fence, ...]:
    """Every block of `lines`; one that never closes runs to the end of the text."""
    found, opened = scanned(lines)
    if opened is None:
        return found
    return (*found, replace(opened, last=len(lines) - 1))


def fenced(lines: list[str], where: str) -> frozenset[int]:
    """The numbers of the lines inside a block, its fences too, for a reader that takes a text
    by its headings. A block that never closes is refused: each line after it would read as
    code, and the reader would go on with less of the text than its writer wrote."""
    found, opened = scanned(lines)
    if opened is not None:
        number = opened.first + 1
        fence = lines[opened.first].strip()
        raise Refusal(
            "open-fence",
            f"{where}: line {number} opens a code block that never closes ({fence}), so "
            "each line after it reads as code and no heading after it counts",
            "close the fence, or put a sample that holds fences of its own in a longer "
            "fence (```` around ```)",
        )
    return frozenset(
        index for fence in found for index in range(fence.first, fence.last + 1)
    )
