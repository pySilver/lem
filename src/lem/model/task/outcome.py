"""The outcome a task's first line quotes: the first sentence of prose under `## Outcome` in a
`task.md` (`outcome_of` on `main`).

A numbered story, a list, a chart, a table or a bold label (a few words, or any that ends in a
colon: "Today:") is no sentence to quote. A bold sentence, on one line or wrapped over more, is
quoted whole and without its `**`, and so is a sentence that a few bold words open ("**Done**
shows ..."); the `**` inside a code span stays.
"""

import re

from msgspec.structs import replace

from lem.model.task import markdown, quotes
from lem.records.base import Frozen

SECTION = re.compile(r"(?m)^##[ \t]+Outcome[ \t]*$")
FENCE = re.compile(r"`{3,}|~{3,}")
# A line of a story, a list, a quote, a table or an image, and a line that opens with bold.
MARKER = re.compile(r"(\d+\.|[-*+>|!]|\*\*)")
# The rule under the header of a table: dashes, colons and pipes, with one pipe or more.
TABLE_RULE = re.compile(r"[\s|:-]*-[\s|:-]*")


class Reading(Frozen, frozen=True, kw_only=True):
    """The read so far: the paragraph of prose, whether the last line was blank, the fence of
    the code block it is in, the column of the step it is in, and whether it is done."""

    paragraph: tuple[str, ...] = ()
    blank: bool = False
    fenced: str = ""
    inside: int | None = None
    done: bool = False


def outcome_of(text: str) -> str | None:
    """The first sentence of prose under `## Outcome` in `text`, or None."""
    found = SECTION.search(text)
    if found is None:
        return None
    reading = Reading()
    for row in markdown.unfenced(text[found.end() :].splitlines()):
        reading = read_row(reading, row)
        if reading.done:
            break
    return quotes.quoted(reading.paragraph)


def read_row(reading: Reading, row: str) -> Reading:
    """The read after one more row: a fence opens or closes a block, and a heading outside a
    block ends the section."""
    line = row.strip()
    indent = len(row) - len(row.lstrip())
    fence = FENCE.match(line)
    rest = line[fence.end() :] if fence else ""
    if fence and markdown.closes(reading.fenced, fence[0], rest):
        return toggled(reading, fence[0], indent)
    if line.startswith("#") and not reading.fenced:
        return replace(reading, done=True)
    return read_line(reading, line, indent)


def toggled(reading: Reading, fence: str, indent: int) -> Reading:
    """The read after a fence: a block opens or closes, and a fence indented less than the
    step's text ends the list."""
    keep = bool(reading.fenced) or indent >= (reading.inside or 0)
    inside = reading.inside if keep else None
    return replace(reading, inside=inside, fenced="" if reading.fenced else fence)


def read_line(reading: Reading, line: str, indent: int) -> Reading:
    """The read after a line that is no fence: prose goes on the paragraph, and anything else
    ends it, quoted when it holds more than a few words."""
    fenced = bool(reading.fenced)
    inside = reading.inside
    if not fenced:
        inside = markdown.step_of(line, indent, inside, blank=reading.blank)
    rule = not fenced and "|" in line and TABLE_RULE.fullmatch(line) is not None
    moved = replace(reading, inside=inside, blank=not line)
    if prose(moved, line, rule=rule):
        return replace(moved, paragraph=(*moved.paragraph, line))
    return ended(moved, rule=rule)


def prose(reading: Reading, line: str, *, rule: bool) -> bool:
    """Whether a line is prose: words outside a block, a step and a table, that open with no
    marker of a list, a quote or a table, or with a bold run that is no label."""
    if not line or reading.fenced or reading.inside is not None or rule:
        return False
    return markdown.bold(line) or MARKER.match(line) is None


def ended(reading: Reading, *, rule: bool) -> Reading:
    """The read after a line that is no prose: the paragraph is the outcome when it holds more
    than a few words (the row above a table's rule is its header, no sentence), else it
    starts again."""
    paragraph = reading.paragraph[:-1] if rule else reading.paragraph
    if len(" ".join(paragraph).split()) > quotes.FEW_WORDS:
        return replace(reading, paragraph=paragraph, done=True)
    return replace(reading, paragraph=())
