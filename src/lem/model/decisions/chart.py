"""One mermaid chart of a decision, as `lem decisions log --chart FILE` keeps it (`decisions.chart`
and `chart_type` on `main`).

The chart is in a file because its text does not pass through every shell: its text, with or
without its ```mermaid fence, kept with its line breaks. A file that is empty, longer than
`MOST` characters, of no chart type mermaid draws, or a flowchart with a text out of double
quotes (the owner's rule for every chart) is refused.
"""

import re

from lem.kernel.errors import Refusal
from lem.model.decisions import quotes

# The longest chart a record keeps: about a dozen nodes is the form's own bound
# (`prompts/writing.md`), and this is a guess at three times that, not a measurement.
MOST = 4000
FENCE = re.compile(r"\s*(`{3,}|~{3,})\s*(\w*)\s*$")
# The first word of a chart mermaid draws (mermaid 11, its diagram types).
TYPES = frozenset(
    (
        "flowchart",
        "graph",
        "sequenceDiagram",
        "stateDiagram",
        "stateDiagram-v2",
        "classDiagram",
        "erDiagram",
        "journey",
        "gantt",
        "pie",
        "quadrantChart",
        "requirementDiagram",
        "gitGraph",
        "mindmap",
        "timeline",
        "sankey-beta",
        "xychart-beta",
        "block-beta",
        "packet-beta",
        "architecture-beta",
        "kanban",
        "radar-beta",
        "C4Context",
        "C4Container",
        "C4Component",
        "C4Dynamic",
        "C4Deployment",
    )
)
CODE = "chart"
FRONT = "---"


def unfenced(text: str, name: str) -> list[str]:
    """The chart's lines without its fence; a fence of another language is refused."""
    rows = text.strip("\n").splitlines()
    fence = FENCE.match(rows[0]) if rows else None
    if fence is None:
        return rows
    if fence[2] not in {"", "mermaid"}:
        raise Refusal(
            CODE,
            f"{name} holds a ```{fence[2]} block",
            "--chart takes one mermaid chart: its text, or its text in a ```mermaid fence",
        )
    rows = rows[1:]
    if rows and rows[-1].strip() == fence[1]:
        rows = rows[:-1]
    return rows


def after_front(rows: list[str]) -> list[str]:
    """The rows after the chart's front matter, when it has one."""
    if not rows or rows[0].strip() != FRONT:
        return rows
    for index, row in enumerate(rows[1:], start=1):
        if row.strip() == FRONT:
            return rows[index + 1 :]
    return []


def kind_of(body: str) -> str:
    """The first word of a chart, after its front matter and its `%%` lines."""
    for row in after_front(body.splitlines()):
        said = row.strip()
        if said and not said.startswith("%%"):
            return said.split()[0]
    return ""


def sized(text: str, name: str) -> str:
    """The chart's text without its fence; an empty one and a long one are refused."""
    rows = unfenced(text, name)
    body = "\n".join(row.rstrip() for row in rows).strip("\n")
    if not body.strip():
        raise Refusal(CODE, f"{name} holds no chart", "write one mermaid chart in it")
    if len(body) > MOST:
        raise Refusal(
            CODE,
            f"the chart in {name} has {len(body)} characters, and a record keeps {MOST}",
            "one chart for one idea, about a dozen nodes (prompts/writing.md)",
        )
    return body


def chart_of(text: str, name: str) -> str:
    """The text of the chart in the file `name`, checked."""
    body = sized(text, name)
    kind = kind_of(body)
    if kind not in TYPES:
        raise Refusal(
            CODE,
            f"the chart in {name} opens with {kind!r}, which is no chart type mermaid draws",
            "open it with one of them, as flowchart TD or sequenceDiagram",
        )
    bare = quotes.unquoted(body) if kind in quotes.FLOWS else None
    if bare is not None:
        raise Refusal(
            CODE,
            f"the chart in {name} has a text out of double quotes, {bare!r}",
            "put every node's and edge's text of a flowchart in double quotes, as A[\"The "
            'total shows 0"] -->|"yes"| B["A credit note"]',
        )
    return body
