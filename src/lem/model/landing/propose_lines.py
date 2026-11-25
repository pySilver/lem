"""What `propose` asks of the notes' lines (`main:land.cmd_propose`, `unfiled_lines`,
`entry_spans`): the headings each request's notes hold, and a bar call or an item for each line
that names a finding nobody filed, so that no defect is raised again by the next review and none
over the bar goes unjudged.
"""

import re
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing.propose_facts import BACKLOG
from lem.model.landing.propose_notes import lines_of

if TYPE_CHECKING:
    from lem.model.landing.propose_notes import Notes

FILED = "## Filed in the backlog"
NOT_WORTH = "## Filed as not worth it"
FIXED = "## Fixed on the way"
SEEN = "## Seen, not filed"
LEFT_OPEN = "## Left open"
MIGRATION = "## Migration"
# The headings the notes of a request on the standard track hold, in this order: what only
# the one who read the task's report can say.
NOTES = ("## Decisions", LEFT_OPEN, "## Worth a look", FILED, "## Not done")
# The bar call of a line that names a finding nobody filed: `under: REASON` or
# `cheap: REASON`, anywhere in the line.
CALLED = re.compile(r"(?i)(?<![\w-])(under|cheap):[ \t]*\S")
# The path of an item of the backlog folder, as a line names it.
NAMED = re.compile(rf"(?<![\w./-]){re.escape(BACKLOG)}/[^\s`'\"()\[\],;]+")
LISTED = re.compile(r"(\s*)([-*+]|\d+[.)])\s")

type Entry = tuple[str, ...]


def wanted(*, small: bool, careful: bool) -> tuple[str, ...]:
    """The headings the notes hold: the standard track's five, and `## Migration` for a
    careful request; the fast track's notes have no fixed headings."""
    headings = () if small else NOTES
    return (*headings, MIGRATION) if careful else headings


def missing(notes: Notes, held: tuple[str, ...], slug: str) -> Refusal | None:
    """The refusal of notes that lack a heading of `held`."""
    there = {found.heading for found in notes.parts}
    absent = ", ".join(heading for heading in held if heading not in there)
    if not absent:
        return None
    listed = ", ".join(held)
    return Refusal(
        "notes-headings",
        f"the notes lack {absent}: they hold {listed}",
        "give each heading what is true of this task or the one word `none`, then "
        f"lem land propose {slug} again",
    )


def opens(line: str, depth: int, *, fresh: bool) -> bool:
    """Whether a line opens an entry: after a blank line or a heading, or a list item no
    deeper than the entry's first line."""
    mark = LISTED.match(line)
    if mark is None:
        return fresh
    return fresh or len(mark.group(1)) <= depth


def entries(lines: tuple[str, ...]) -> tuple[Entry, ...]:
    """The entries of a part of the notes, each as its lines: a list item with the lines
    that continue it (a deeper list item among them), or a paragraph's line. Blank lines, a
    lone `none` and a heading of a lower level are none."""
    if not lines_of(lines):
        return ()
    found: list[list[str]] = []
    depth, fresh = 0, True
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            fresh = True
        elif opens(line, depth, fresh=fresh):
            found.append([line])
            depth = len(line) - len(line.lstrip())
            fresh = False
        else:
            found[-1].append(line)
    return tuple(map(tuple, found))


def called(notes: Notes, *, small: bool) -> tuple[Entry, ...]:
    """The entries that name a finding nobody filed: under `## Left open` and
    `## Seen, not filed`, and on the fast track the lines before the first heading too,
    where the should findings the review left are."""
    head = entries(notes.head) if small else ()
    parts = (found for found in notes.parts if found.heading in {LEFT_OPEN, SEEN})
    return head + tuple(entry for found in parts for entry in entries(found.lines))


def named(text: str) -> tuple[str, ...]:
    """The paths of the backlog's items a text names."""
    return tuple(path.rstrip(".:") for path in NAMED.findall(text))


def bare(notes: Notes, *, small: bool, in_tip: frozenset[str]) -> tuple[str, ...]:
    """The first line of each entry that names a finding nobody filed, with neither a bar
    call and its reason nor the path of an item the tip holds."""
    return tuple(
        entry[0].strip()
        for entry in called(notes, small=small)
        if not CALLED.search("\n".join(entry))
        and not in_tip.intersection(named("\n".join(entry)))
    )
