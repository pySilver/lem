"""The agent's notes in the pull request's text (`main:land.with_outside`, `small_text`,
`no_media`): on the standard track the notes with what was seen outside the change under their
own headings, on the fast track the notes' own lines first and the four headings of what was
seen at the end; on both, a picture of the task's board is named, never linked, since the
forge has no such file."""

import re
from typing import TYPE_CHECKING

from lem.app.landing import pr_outside, pr_parts, pr_placed
from lem.app.landing.pr_inputs import Block, Lines, block
from lem.model.landing.propose_lines import FILED, FIXED, NOT_WORTH, SEEN
from lem.model.landing.propose_notes import lines_of

if TYPE_CHECKING:
    from lem.model.landing.propose_facts import Facts
    from lem.model.landing.propose_notes import Notes
    from lem.records.record import Record

# The lines under each heading of the items.
type Headed = dict[str, Lines]
# A picture of a task's `media/` folder, linked from a document: the task's folder is in no
# commit, so the pull request names the picture and links nothing.
MEDIA = re.compile(
    r"(!?)\[([^\]]*)\]\(\s*(?:[^)\s]*/)?media/([^)\s]+)(?:\s+\"[^\"]*\")?\s*\)"
)


def caption(found: re.Match[str]) -> str:
    """A link to a picture as its caption, or its file's name when it has none."""
    named = found.group(2) or found.group(3)
    return f"{named} (a picture on the task's board)"


def no_media(text: str) -> Lines:
    """The text with each link to a file of `media/` replaced by its caption, as lines."""
    return tuple(MEDIA.sub(caption, text).strip().splitlines())


def own(notes: Notes, heading: str) -> Lines:
    """The notes' own lines under `heading`."""
    parts = (found.lines for found in notes.parts if found.heading == heading)
    return tuple(line for lines in parts for line in lines_of(lines))


def fixed(notes: Notes) -> str:
    """The notes' lines under `## Fixed on the way`, which name a review's cheap defects a
    builder fixed by their numbers."""
    return "\n".join(own(notes, FIXED))


def filings(record: Record, notes: Notes, facts: Facts) -> tuple[Headed, Lines]:
    """The lines of the items under their two headings, the notes' own and the step's, and
    the seen lines."""
    steps, seen = pr_outside.parts(record, facts, fixed(notes))
    mine = {heading: own(notes, heading) for heading in pr_placed.HEADINGS}
    return pr_placed.placed(mine, steps), seen


def standard(record: Record, notes: Notes, facts: Facts) -> Lines:
    """The standard track's notes, with each item and each seen defect under its heading;
    notes that get no line come back as they are."""
    placed, seen = filings(record, notes, facts)
    parts = list(notes.parts)
    for heading in pr_placed.HEADINGS:
        if placed[heading] != own(notes, heading):
            pr_parts.inserted(parts, heading, placed[heading] or ("none",))
    if seen:
        pr_parts.inserted(parts, SEEN, (*own(notes, SEEN), *seen))
    return no_media(pr_parts.written(notes.head, parts))


def tail(record: Record, notes: Notes, facts: Facts) -> tuple[Block, ...]:
    """The fast track's notes: their own lines but the four headings of what was seen, then
    those four, each when it has a line."""
    placed, seen = filings(record, notes, facts)
    rest = tuple(part for part in notes.parts if part.heading not in pr_parts.ORDER)
    shown = no_media(pr_parts.written(notes.head, rest))
    if [line.lower() for line in shown] == ["none"]:
        shown = ()
    return (
        *block(None, shown),
        *block(FILED, placed[FILED]),
        *block(NOT_WORTH, placed[NOT_WORTH]),
        *block(FIXED, own(notes, FIXED)),
        *block(SEEN, (*own(notes, SEEN), *seen)),
    )
