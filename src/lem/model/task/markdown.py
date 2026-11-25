"""What the read of an outcome needs of Markdown, line by line: the code blocks and their
fences, the step of a story or the item of a list a line is in, and a bold label.

A fence closes only on a line of its own character, at least as long, with nothing after it,
as `criteria.fences` on `main` reads one.
"""

import re
from functools import reduce

from msgspec.structs import replace

from lem.model.task.quotes import FEW_WORDS
from lem.records.base import Frozen

FENCE_ROW = re.compile(r"( *)(`{3,}|~{3,})(.*)$")
STEP = re.compile(r"(?:\d+\.|[-*+])(?:[ \t]+|$)")
# A line that opens with bold: its run, and a colon right after it.
LABEL = re.compile(r"\*\*((?:`[^`]*`|[^*`])*)\*\*(:?)")
# A letter, a digit or a code span next on the line, after a bold run.
OPENER = re.compile(r"[ \t]*(?:[^\W_]|`)")
BOLD_START = re.compile(r"\*\*[^*\s]")
BACKTICK = "`"


class Blocks(Frozen, frozen=True, kw_only=True):
    """The code blocks of a text so far: the fence of the one open and its line, and the line
    that closed the last one (-1 for none)."""

    opened: str = ""
    at: int = -1
    last: int = -1


def closes(fenced: str, fence: str, rest: str) -> bool:
    """Whether a fence line ends the block `fenced`; with no block open, it opens one."""
    if not fenced:
        return True
    if fence[0] != fenced[0] or rest.strip():
        return False
    return len(fence) >= len(fenced)


def blocked(blocks: Blocks, row: tuple[int, str]) -> Blocks:
    """The blocks after one more row: a backtick fence whose words hold a backtick opens
    none."""
    mark = FENCE_ROW.match(row[1])
    if mark is None:
        return blocks
    fence, rest = mark[2], mark[3]
    if not blocks.opened:
        opened = "" if fence.startswith(BACKTICK) and BACKTICK in rest else fence
        return replace(blocks, opened=opened, at=row[0])
    if closes(blocks.opened, fence, rest):
        return replace(blocks, opened="", last=row[0])
    return blocks


def unfenced(rows: list[str]) -> list[str]:
    """The rows, with the fence that opens a block right after the last close left out: a
    sample in three backticks that holds a block of its own in three backticks has its inner
    close end it, and the outer close is that close again, never a block to the end. Any
    other block that never closes runs to the end: code, never quoted."""
    blocks = reduce(blocked, enumerate(rows), Blocks())
    if not blocks.opened or blocks.last < 0:
        return rows
    between = rows[blocks.last + 1 : blocks.at]
    if any(row.strip() for row in between):
        return rows
    before = rows[: blocks.at]
    after = rows[blocks.at + 1 :]
    return [*before, "", *after]


def step_of(line: str, indent: int, inside: int | None, *, blank: bool) -> int | None:
    """The column of the text of the step that `line`, of `indent`, is in, after a line in a
    step whose text starts at `inside` (None for none), or None. A step of a story or an item
    of a list holds the lines under it, as Markdown reads them: those that wrap it, indented
    or not, and a paragraph indented as far as its text; a line indented less after a blank
    one (`blank`) ends the list. A step inside a step keeps the column of the outer one."""
    marker = STEP.match(line)
    if marker and (inside is None or indent < inside):
        mark = marker[0]
        width = max(len(mark), len(mark.rstrip()) + 1)
        return indent + width
    if marker:
        return inside
    return None if line and blank and indent < (inside or 0) else inside


def labeled(line: str) -> bool:
    """Whether a line opens with a bold label: a run that closes on it within a few words, or
    that ends in a colon inside the bold or right after it. A run of a few words that ends in
    a letter or a digit, with a letter, a digit or a code span next, opens the sentence
    instead ("**Done** shows ..."); "**Today** - ...", "**Today**, ..." and "**Before.** ..."
    stay labels."""
    label = LABEL.match(line)
    if label is None:
        return False
    text, colon = label.groups()
    after = OPENER.match(line, label.end())
    if after and not colon and text[-1:].isalnum():
        return False
    few = len(text.split()) <= FEW_WORDS
    return bool(colon) or few or text.rstrip().endswith(":")


def bold(line: str) -> bool:
    """Whether a line opens with a bold run that is no label (a `***` rule opens no bold)."""
    return BOLD_START.match(line) is not None and not labeled(line)
