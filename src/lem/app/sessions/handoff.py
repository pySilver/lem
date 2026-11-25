"""The form of `handoff.md` (`templates/handoff.md`): the line `task: SLUG · from PHASE ·
written: TIME`, then the five parts, each with words under its heading.

A comment is no part of the form: it is left out before the read. A line of a code block is a
line of its part and never a heading, and a block that never closes is refused, since each line
after its fence would read as code (`criteria.fenced_lines` on `main`). What the file lacks is
named, each part by its heading, in one refusal; so is a time that is no time.
"""

import itertools
import re
from datetime import UTC, datetime

from lem.kernel.errors import Refusal
from lem.records.base import Frozen

HANDOFF = "handoff.md"
FIRST = re.compile(
    r"task:\s*(?P<task>[a-z0-9]+(?:-[a-z0-9]+)*)\s*·\s*from\s+(?P<phase>shape|build|land|fast)"
    r"\s*·\s*written:\s*(?P<written>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?)Z"
)
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
FENCE = re.compile(r" {0,3}(?P<mark>`{3,}|~{3,})(?P<rest>.*)")
HEADING = re.compile(r"^## +(.+?) *$", re.MULTILINE)
PARTS = ("Settled", "Open", "Next step", "Failed", "Changed files")
FIX = "write {} again in the form of `templates/handoff.md`, then run this again"


class Form(Frozen, frozen=True, kw_only=True):
    """What `handoff.md` says of itself: the phase it is from, and when it was written."""

    phase: str
    written: datetime


def form(text: str, slug: str) -> Form:
    """The handoff's own line, after a check of its whole form; refused with each part it
    lacks."""
    head, *parts = HEADING.split(fenced(text, slug))
    found = FIRST.fullmatch(head.strip())
    written = moment(found["written"]) if found else None
    lacks = lacking(parts)
    if found is None or found["task"] != slug or written is None:
        lacks.insert(0, f"a first line `task: {slug} · from PHASE · written: TIME`")
    if found is None or written is None or lacks:
        raise Refusal(
            "handoff-form",
            f"{HANDOFF} of {slug} is not in the form of `templates/handoff.md`: it lacks "
            + "; ".join(lacks),
            FIX.format(HANDOFF),
        )
    return Form(phase=found["phase"], written=written)


def moment(stamp: str) -> datetime | None:
    """The UTC moment `stamp` names, or None for a time that is no time (February 31)."""
    try:
        return datetime.fromisoformat(stamp).replace(tzinfo=UTC)
    except ValueError:
        return None


def fenced(text: str, slug: str) -> str:
    """`text` with no comment, and each line of a code block moved in by a space so that it
    reads as no heading; refused when a block never closes."""
    moved, opened = code_moved(COMMENT.sub("", text).splitlines())
    if opened is not None:
        raise Refusal(
            "handoff-form",
            f"{HANDOFF} of {slug} has a code block that opens with {opened} and never "
            "closes, so each line after it reads as code",
            FIX.format(HANDOFF),
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


def lacking(parts: list[str]) -> list[str]:
    """The headings of the form with no words under them in `parts`, the titles and bodies of
    the headings in turn."""
    pairs = itertools.batched(parts, 2, strict=True)
    said = {title.lower() for title, body in pairs if body.strip()}
    return [f"## {part}" for part in PARTS if part.lower() not in said]
