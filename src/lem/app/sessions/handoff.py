"""The form of `handoff.md` (`templates/handoff.md`): the line `task: SLUG · from PHASE ·
written: TIME`, then the five parts, each with words under its heading.

A comment is no part of the form: it is left out before the read. A line of a code block is a
line of its part and never a heading, and a block that never closes is refused, since each line
after its fence would read as code (`criteria.fenced_lines` on `main`). What the file lacks is
named, each part by its heading, in one refusal; so is a time that is no time.
"""

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import msgspec

from lem.app.sessions.fences import FIX, fenced
from lem.app.sessions.handoff_parts import Changed, lacking
from lem.kernel.errors import Refusal
from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path

HANDOFF = "handoff.md"
HEADING = re.compile(r"^## +(.+?) *$", re.MULTILINE)
FIRST = re.compile(
    r"task:\s*(?P<task>[a-z0-9]+(?:-[a-z0-9]+)*)\s*·\s*from\s+(?P<phase>shape|build|land|fast)"
    r"\s*·\s*written:\s*(?P<written>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?)Z"
)


class Form(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """What `handoff.md` says of itself: the task, the phase it is from, when it was written,
    and its changed files."""

    task: str
    phase: str = msgspec.field(name="from")
    written: datetime
    changed: tuple[Changed, ...] = ()


def form(text: str, slug: str) -> Form:
    """The handoff's own line, after a check of its whole form; refused with each part it
    lacks."""
    head, *parts = HEADING.split(fenced(text, slug, HANDOFF))
    lacks, changed = lacking(parts)
    first = first_of(head, slug)
    if first is None or lacks:
        raise lacked(slug, lacks, first=first is not None)
    return msgspec.structs.replace(first, changed=changed)


def lacked(slug: str, lacks: list[str], *, first: bool) -> Refusal:
    """The refusal of a handoff that lacks `lacks`, and its first line unless `first`."""
    line = (
        () if first else (f"a first line `task: {slug} · from PHASE · written: TIME`",)
    )
    said = "; ".join((*line, *lacks))
    return Refusal(
        "handoff-form",
        f"{HANDOFF} of {slug} is not in the form of `templates/handoff.md`: it lacks {said}",
        FIX.format(HANDOFF),
    )


def first_of(head: str, slug: str) -> Form | None:
    """The phase and the UTC moment of the handoff's first line; None when the line is not in
    its form, names another task, or names a time that is no time (February 31)."""
    found = FIRST.fullmatch(head.strip())
    if found is None or found["task"] != slug:
        return None
    try:
        written = datetime.fromisoformat(found["written"])
    except ValueError:
        return None
    moment = written.replace(tzinfo=UTC)
    return Form(task=slug, phase=found["phase"], written=moment)


def checked(folder: Path, slug: str, ended: str, opened_at: datetime) -> Form:
    """The handoff of the task in `folder`, refused when it is missing, not in its form, from
    another phase than `ended`, or written before the session that leaves opened."""
    path = folder / HANDOFF
    if not path.is_file():
        raise Refusal(
            "no-handoff",
            f"{path} is not there",
            "write the handoff in the form of `templates/handoff.md` first",
        )
    found = form(path.read_text(encoding="utf-8"), slug)
    if found.phase != ended:
        raise Refusal(
            "handoff-phase",
            f"{HANDOFF} of {slug} is from {found.phase}, and the phase that ends is {ended}",
            "write it again for the phase that ends",
        )
    if found.written < opened_at.replace(second=0):
        raise Refusal(
            "handoff-old",
            f"{HANDOFF} of {slug} was written before this session opened: it is an older "
            "session's",
            "write it again",
        )
    return found
