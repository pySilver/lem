"""The lines of `handoff.md` that are code: a line of a code block is a line of its part and never
a heading, and a block that never closes is refused, since each line after its fence would read
as code (`criteria.fenced_lines` on `main`)."""

import re

from lem.kernel.errors import Refusal

COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
FENCE = re.compile(r" {0,3}(?P<mark>`{3,}|~{3,})(?P<rest>.*)")
FIX = "write {} again in the form of `templates/handoff.md`, then run this again"


def fenced(text: str, slug: str, name: str) -> str:
    """`text` with no comment, and each line of a code block moved in by a space so that it
    reads as no heading; refused when a block never closes."""
    moved, opened = code_moved(COMMENT.sub("", text).splitlines())
    if opened is not None:
        raise Refusal(
            "handoff-form",
            f"{name} of {slug} has a code block that opens with {opened} and never "
            "closes, so each line after it reads as code",
            FIX.format(name),
        )
    return "\n".join(moved)


def code_moved(lines: list[str]) -> tuple[list[str], str | None]:
    """The lines, each of a code block (its fences too) moved in by a space, and the fence of
    a block still open at the end."""
    opened: str | None = None
    moved: list[str] = []
    for line in lines:
        code = opened is not None
        opened = next_fence(opened, FENCE.fullmatch(line))
        code = code or opened is not None
        moved.append(f" {line}" if code else line)
    return moved, opened


def next_fence(opened: str | None, mark: re.Match[str] | None) -> str | None:
    """The fence of the block open after a line: the fence `mark` opens, none when it closes
    `opened` (the same character, at least as long, nothing after it), else `opened`."""
    if mark is None:
        return opened
    if opened is None:
        return mark["mark"]
    fence = mark["mark"]
    same = fence[0] == opened[0]
    longer = len(fence) >= len(opened)
    return None if same and longer and not mark["rest"].strip() else opened
