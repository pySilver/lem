"""The agent's notes in the pull request's text (`main:land.with_outside`, `small_text`,
`no_media`): on the standard track the notes with what was seen outside the change under their
own headings, on the fast track the notes' own lines first and the four headings of what was
seen at the end; on both, a picture of the task's board is named, never linked, since the
forge has no such file."""

import re
from typing import TYPE_CHECKING

from lem.app.landing import pr_outside
from lem.app.landing.pr_inputs import Block, Lines, block
from lem.model.landing.propose_lines import FILED, FIXED, NOT_WORTH, SEEN
from lem.model.landing.propose_notes import Notes, Part, lines_of

if TYPE_CHECKING:
    from lem.model.landing.propose_facts import Facts
    from lem.records.record import Record

ORDER = (FILED, NOT_WORTH, FIXED, SEEN)
# A picture of a task's `media/` folder, linked from a document: the task's folder is in no
# commit, so the pull request names the picture and links nothing.
MEDIA = re.compile(
    r"(!?)\[([^\]]*)\]\(\s*(?:[^)\s]*/)?media/([^)\s]+)(?:\s+\"[^\"]*\")?\s*\)"
)


def no_media(text: str) -> str:
    """The text with each link to a file of `media/` replaced by its caption."""
    return MEDIA.sub(
        lambda found: (
            f"{found.group(2) or found.group(3)} (a picture on the task's board)"
        ),
        text,
    )


def own(notes: Notes, heading: str) -> Lines:
    """The notes' own lines under `heading`."""
    return tuple(
        line
        for found in notes.parts
        if found.heading == heading
        for line in lines_of(found.lines)
    )


def fixed(notes: Notes) -> str:
    """The notes' lines under `## Fixed on the way`, which name a review's cheap defects a
    builder fixed by their numbers."""
    return "\n".join(own(notes, FIXED))


def inserted(parts: list[Part], heading: str, more: Lines, *, join: bool) -> None:
    """Put `more` under `heading`: joined with the lines there (`join`) or in their place,
    or a part of its own after the last heading that comes before it in `ORDER`."""
    there = [at for at, found in enumerate(parts) if found.heading == heading]
    if there:
        before = lines_of(parts[there[0]].lines) if join else ()
        joined = (*before, *(line for line in more if line not in before))
        parts[there[0]] = Part(heading=heading, lines=("", *joined, ""))
        return
    earlier = ORDER[: ORDER.index(heading)]
    places = [at for at, found in enumerate(parts) if found.heading in earlier]
    place = places[-1] + 1 if places else len(parts)
    if place and parts[place - 1].lines[-1:] != ("",):
        previous = parts[place - 1]
        parts[place - 1] = Part(heading=previous.heading, lines=(*previous.lines, ""))
    parts.insert(place, Part(heading=heading, lines=("", *more, "")))


def standard(record: Record, notes: Notes, facts: Facts) -> Lines:
    """The standard track's notes, with each item and each seen defect under its heading;
    notes that get no line come back as they are."""
    steps, seen = pr_outside.parts(record, facts, fixed(notes))
    parts = list(notes.parts)
    if any(steps.values()) or seen:
        mine = {heading: own(notes, heading) for heading in (FILED, NOT_WORTH)}
        placed = pr_outside.placed(mine, steps)
        for heading in (FILED, NOT_WORTH):
            if placed[heading] != mine[heading]:
                inserted(parts, heading, placed[heading] or ("none",), join=False)
        if seen:
            inserted(parts, SEEN, seen, join=True)
    lines = [
        *notes.head,
        *(line for found in parts for line in (found.heading, *found.lines)),
    ]
    return tuple(no_media("\n".join(lines)).strip().splitlines())


def tail(record: Record, notes: Notes, facts: Facts) -> tuple[Block, ...]:
    """The fast track's notes: their own lines but the four headings of what was seen, then
    those four, each when it has a line."""
    steps, seen = pr_outside.parts(record, facts, fixed(notes))
    mine = {heading: own(notes, heading) for heading in (FILED, NOT_WORTH)}
    placed = pr_outside.placed(mine, steps)
    rest = [*notes.head]
    for found in notes.parts:
        if found.heading not in ORDER:
            rest.extend((found.heading, *found.lines))
    text = no_media("\n".join(rest)).strip()
    shown = () if text.lower() in {"", "none"} else tuple(text.splitlines())
    return (
        *block(None, shown),
        *block(FILED, placed[FILED]),
        *block(NOT_WORTH, placed[NOT_WORTH]),
        *block(FIXED, own(notes, FIXED)),
        *block(SEEN, (*own(notes, SEEN), *seen)),
    )
