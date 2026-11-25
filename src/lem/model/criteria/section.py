"""Where the criteria are in a text: the `## Acceptance criteria` section, the charts in it, and
the body of `## How it works` after it (`criteria.parse` and `criteria.how_it_works` on `main`).

A heading inside a code block is a line of code, never a heading: a plan may show the form in a
fence, and what is inside one is an example.
"""

import re
from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lem.model.criteria.fences import Fence

HEADING = re.compile(r"^##\s+Acceptance criteria\s*$")
HOW = re.compile(r"^##\s+How it works\s*$")
# The next heading of a level that ends a section: `## ` for the criteria, `# ` or `## ` for
# How it works.
NEXT = re.compile(r"^## ")
NEXT_HOW = re.compile(r"^#{1,2}\s")
MERMAID = "mermaid"
FORM = "the plan opens with it, as `lem criteria show --help` says"

# A text's lines, and the numbers of those inside a code block.
type Rows = tuple[str, ...]
type Code = frozenset[int]
type Charts = Mapping[int, Fence]


def heading(rows: Rows, code: Code, form: re.Pattern[str], start: int = 0) -> int:
    """The first line from `start` on that `form` matches outside a code block, or -1."""
    for index, row in enumerate(rows[start:], start=start):
        if index not in code and form.match(row):
            return index
    return -1


def ending(rows: Rows, code: Code, start: int, form: re.Pattern[str]) -> int:
    """The line after the section that starts at `start`: the next heading `form` matches
    outside a code block, or the end of the text."""
    found = heading(rows, code, form, start + 1)
    return len(rows) if found < 0 else found


def bounds(rows: Rows, code: Code, name: str) -> range:
    """The lines of the `## Acceptance criteria` section after its heading; a text with none
    is refused."""
    start = heading(rows, code, HEADING)
    if start < 0:
        raise Refusal(
            "criteria-form", f"{name} has no `## Acceptance criteria` section", FORM
        )
    return range(start + 1, ending(rows, code, start, NEXT))


def how_it_works(rows: Rows, code: Code) -> str | None:
    """The body of `## How it works`, as markdown: the chart of several criteria and the
    sentence it shows; None when the text has none."""
    start = heading(rows, code, HOW)
    if start < 0:
        return None
    end = ending(rows, code, start, NEXT_HOW)
    body = "\n".join(rows[start + 1 : end])
    return body.strip() or None


def charts(blocks: tuple[Fence, ...], section: range) -> Charts:
    """The `mermaid` blocks of the section, by their first line: each is the chart of the
    criterion above it, at any indent. Any other block is an example."""
    found = {
        block.first: block
        for block in blocks
        if block.word == MERMAID and block.first in section
    }
    return MappingProxyType(found)


def dedented(row: str, indent: int) -> str:
    """A chart's line taken out of its block's indent, never past its own."""
    own = len(row) - len(row.lstrip(" "))
    return row[min(indent, own) :]


def chart_of(rows: Rows, block: Fence) -> str | None:
    """A chart's text without its fences."""
    inside = rows[block.first + 1 : block.last]
    body = "\n".join(dedented(row, block.indent) for row in inside)
    return body.strip("\n") or None
