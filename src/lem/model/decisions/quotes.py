"""Whether each node's and edge's text of a flowchart is in double quotes (`decisions.unquoted`
on `main`). A check of the common forms, not a parser: it reads a row with its quoted texts taken
out."""

import re

FLOWS = frozenset(("flowchart", "graph"))
# The rows of a flowchart that hold no node's or edge's text, by their first word.
NO_TEXT = frozenset(
    (
        "flowchart",
        "graph",
        "classDef",
        "class",
        "style",
        "linkStyle",
        "click",
        "direction",
        "subgraph",
        "end",
    )
)
# A node's shape opening right after its id, and an edge's text between pipes or between `--`
# and its arrow.
SHAPE = re.compile(
    r"[A-Za-z0-9_]+(\[\[|\[\(|\(\[|\(\(\(|\(\(|\{\{|\[/|\[\\|\[|\(|\{|>)"
)
PIPED = re.compile(r"\|([^|]*)\|")
SPOKEN = re.compile(r"(?<![-=])(?:--|==)\s+([^\s\->=][^>]*?)\s+(?:-->|==>|---|===)")
QUOTED = re.compile(r'"[^"]*"')
EMPTY = '""'
QUOTE = '"'


def bare_in(row: str) -> bool:
    """Whether a row holds a node's or an edge's text out of quotes."""
    bare = QUOTED.sub(EMPTY, row)
    for found in SHAPE.finditer(bare):
        after = bare[found.end() :].lstrip()
        if not after.startswith(QUOTE):
            return True
    edges = (*PIPED.findall(bare), *SPOKEN.findall(bare))
    return any(edge.strip() != EMPTY for edge in edges)


def counted(row: str) -> bool:
    """Whether a row may hold a node's or an edge's text."""
    words = row.split() or [""]
    first = words[0]
    return bool(first) and first not in NO_TEXT and not first.startswith("%%")


def start_of(rows: list[str]) -> int:
    """The row after the one that names the flowchart's type: front matter before it holds no
    node."""
    for index, row in enumerate(rows):
        words = row.split()
        if words and words[0] in FLOWS:
            return index + 1
    return len(rows)


def unquoted(body: str) -> str | None:
    """The first row of a flowchart with a text out of quotes, or None when each is quoted."""
    rows = body.splitlines()
    for row in rows[start_of(rows) :]:
        if counted(row) and bare_in(row):
            return row.strip()
    return None
