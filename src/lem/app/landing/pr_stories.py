"""The story of each important decision, folded under the decisions of the pull request's
text, which the forge draws (`main:land.folded_stories`, `story_lines`, `chart_lines`): one the
request is not green for, or the owner's help on a breaker, that has a case or a chart."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.model.landing.green_words import without_him
from lem.records.decisions import Taken

if TYPE_CHECKING:
    from lem.app.landing.pr_inputs import Lines
    from lem.records.record import Record

KNOWN = MappingProxyType(
    {"reproduced": "reproduced", "derived": "derived from the code, not run"}
)
# The longest text of a decision's summary in the pull request, in characters: one line at
# the width of a laptop's window. A guess, not a measurement.
CELL = 80


def one_line(text: str) -> str:
    """A text in one line of at most `CELL` characters, cut at a word, with an ellipsis."""
    flat = " ".join(text.split())
    if len(flat) <= CELL:
        return flat
    cut = flat[:CELL].rsplit(" ", 1)[0]
    return f"{cut.rstrip(',;:.')}…"


def important(decision: Taken) -> bool:
    """Whether a decision's story is told: it is not green for it, or it is his help on a
    breaker, and it has a case or a chart."""
    his = decision.by == "owner" and decision.breaker is not None
    told = decision.story is not None or decision.chart is not None
    return told and (without_him(decision) or his)


def story_lines(decision: Taken) -> Lines:
    """A decision's story folded: its summary, the case with how it is known, the cause,
    and its chart as a fenced mermaid block."""
    summary = f"Decision {decision.id}, its story: {one_line(decision.what)}"
    found = ["", f"<details><summary>{summary}</summary>", ""]
    story = decision.story
    if story is not None:
        known = KNOWN[story.case_was]
        found.extend((f"**The case** ({known}):", "", *story.case, ""))
        found.extend((f"**Why it could happen:** {story.cause}", ""))
    if decision.chart:
        found.extend(("```mermaid", *decision.chart.splitlines(), "```", ""))
    return (*found, "</details>")


def stories(record: Record) -> Lines:
    """The story of each important decision, in the order of the record."""
    return tuple(
        line
        for decision in record.task.decisions
        if isinstance(decision, Taken) and important(decision)
        for line in story_lines(decision)
    )
