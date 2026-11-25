"""The form of `handoff.md` (`templates/handoff.md`): the line `task: SLUG · from PHASE ·
written: TIME`, then the five parts, each with words under its heading.

A comment and a code block are no part of the form: they are left out before the read, so that a
heading inside a code block is no heading. What the file lacks is named, each part by its
heading, in one refusal.
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
LEFT_OUT = re.compile(r"<!--.*?-->|^```.*?^```[^\n]*$", re.DOTALL | re.MULTILINE)
HEADING = re.compile(r"^## +(.+?) *$", re.MULTILINE)
PARTS = ("Settled", "Open", "Next step", "Failed", "Changed files")


class Form(Frozen, frozen=True, kw_only=True):
    """What `handoff.md` says of itself: the phase it is from, and when it was written."""

    phase: str
    written: datetime


def form(text: str, slug: str) -> Form:
    """The handoff's own line, after a check of its whole form; refused with each part it
    lacks."""
    head, *parts = HEADING.split(LEFT_OUT.sub("", text))
    found = FIRST.fullmatch(head.strip())
    lacks = lacking(parts)
    if found is None or found["task"] != slug:
        lacks.insert(0, f"a first line `task: {slug} · from PHASE · written: TIME`")
    if found is None or lacks:
        raise Refusal(
            "handoff-form",
            f"{HANDOFF} of {slug} is not in the form of `templates/handoff.md`: it lacks "
            + "; ".join(lacks),
            f"write {HANDOFF} again in that form, then run this again",
        )
    written = datetime.fromisoformat(found["written"]).replace(tzinfo=UTC)
    return Form(phase=found["phase"], written=written)


def lacking(parts: list[str]) -> list[str]:
    """The headings of the form with no words under them in `parts`, the titles and bodies of
    the headings in turn."""
    pairs = itertools.batched(parts, 2, strict=True)
    said = {title.lower() for title, body in pairs if body.strip()}
    return [f"## {part}" for part in PARTS if part.lower() not in said]
