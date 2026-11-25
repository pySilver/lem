"""The breaker's document, checked before the breaker trips (`decisions.breaker_document` on
`main`): the owner reads it far from the task, so it brings the context back before it asks
anything, and a document that lacks a part is refused with each part it lacks.

A line inside a code block is a line of its part, never a heading; a block that never closes is
refused before any part is named as missing.
"""

from lem.kernel.errors import Refusal
from lem.model.criteria import fences
from lem.model.decisions.parts import PARTS, holds

H1 = "# "
H2 = "## "

type Code = frozenset[int]


def part_named(row: str) -> str | None:
    """The part a `## ` heading opens, by the words it opens with, or None."""
    words = row.removeprefix(H2).lower().split()
    head = " ".join(words)
    return next((part for part in PARTS if head.startswith(part)), None)


def parted(rows: list[str], code: Code) -> dict[str, list[str]]:
    """The lines of each part the document has, by the part's words."""
    found: dict[str, list[str]] = {}
    current: str | None = None
    for index, row in enumerate(rows):
        if row.startswith(H2) and index not in code:
            current = part_named(row)
            found.setdefault(current or "", [])
        elif current:
            found[current].append(row)
    return found


def title_line(rows: list[str], code: Code) -> str:
    """The text of the document's first `# ` line, or nothing."""
    for index, row in enumerate(rows):
        if row.startswith(H1) and index not in code:
            return " ".join(row[len(H1) :].split())
    return ""


def heading_of(part: str) -> str:
    """A part as a refusal names it: its heading, and what it must hold."""
    heading = part.capitalize()
    return f"## {heading} ({PARTS[part]})"


def missing(rows: list[str], code: Code) -> list[str]:
    """Each part the document lacks, or does not fill as it must."""
    found = parted(rows, code)
    lacked = [heading_of(part) for part in PARTS if not holds(part, found)]
    if not title_line(rows, code):
        lacked.insert(
            0, "a first line # that says what stopped the task, in one sentence"
        )
    return lacked


def title_of(text: str, name: str) -> str:
    """The document's title, after a check of its parts."""
    rows = text.splitlines()
    code = fences.fenced(rows, name)
    lacked = missing(rows, code)
    if lacked:
        listed = "; ".join(lacked)
        raise Refusal(
            "breaker-document",
            f"{name} is no breaker's document yet: it lacks {listed}",
            "templates/breaker.md of the skill is its form: the owner reads it far from the "
            "task, so it brings the context back",
        )
    return title_line(rows, code)
