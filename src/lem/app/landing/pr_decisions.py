"""The decisions of the build in the pull request's text (`main:land.breaker_lines`,
`decided`, `after`, `folded_stories`): each stop of the circuit breaker with its cause and how
it ended, each decision of the record with who took it and why, and the story of each important
one folded under the list."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.landing.pr_inputs import Lines
from lem.model.landing.green_words import taken_by, without_him
from lem.records.decisions import Breaker, Taken

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.task import Task

BREAKER_SAYS = MappingProxyType(
    {
        "irreversible": "the next step could not be reversed by a later no",
        "criteria": "no option of the ladder kept the approved criteria",
    }
)
FAMILIES = MappingProxyType({1: "one model family", 2: "two model families"})
KNOWN = MappingProxyType(
    {"reproduced": "reproduced", "derived": "derived from the code, not run"}
)
# The longest text of a decision's summary in the pull request, in characters: one line at
# the width of a laptop's window. A guess, not a measurement.
CELL = 80


def helped(task: Task, breaker: Breaker) -> str:
    """How a stop of the breaker ended: the owner's help, or that it waits for him."""
    help_of = next(
        (
            found.id
            for found in task.decisions
            if isinstance(found, Taken)
            and found.by == "owner"
            and found.breaker == breaker.id
        ),
        None,
    )
    if help_of is None:
        return "it waits for the owner"
    return f"the owner helped, decision {help_of}"


def breaker_line(task: Task, breaker: Breaker) -> str:
    """One stop of the build at the breaker: when, what, why, and how it ended."""
    cause = BREAKER_SAYS[breaker.cause]
    if breaker.irreversible:
        cause = f"{cause} ({breaker.irreversible})"
    stamp = breaker.at.strftime("%Y-%m-%d %H:%M UTC")
    said = f"Why it stopped: {cause}; {helped(task, breaker)}."
    return (
        f"- the build stopped at breaker {breaker.id}, {stamp}: {breaker.what}. {said}"
    )


def after(decision: Taken) -> str:
    """What follows the option a decision took: by whom, why, each level's word, and the
    owner's own words. It opens with ", "."""
    line = f", by {taken_by(decision)}"
    if decision.unsettled:
        line = ", the lead's pick, which no level of the ladder settled"
    if decision.by == "owner" and decision.breaker is not None:
        line = f"{line}, his help on breaker {decision.breaker}"
    elif decision.by == "personas":
        names = {name.rpartition(", ")[0] or name for name, _ in decision.votes}
        families = {
            name.rpartition(", ")[2] for name, _ in decision.votes if ", " in name
        }
        count = len(families)
        named = (
            f", {FAMILIES.get(count, f'{count} model families')}" if families else ""
        )
        line = f"{line}: {len(decision.votes)} votes of {len(names)} personas{named}, all for it"
    line = f"{line}. {decision.why}"
    if decision.levels:
        said = "; ".join(f"{name}: {word}" for name, word in decision.levels)
        line = f"{line} Each level: {said}."
    if decision.words and decision.words != decision.chose:
        line = f'{line} The owner\'s words: "{decision.words}"'
    return line


def lines(record: Record) -> Lines:
    """Each stop of the breaker, then each decision of the record."""
    task = record.task
    stops = tuple(
        breaker_line(task, found)
        for found in task.decisions
        if isinstance(found, Breaker)
    )
    taken = tuple(
        f'- {found.what}: "{found.chose}"{after(found)}'
        for found in task.decisions
        if isinstance(found, Taken)
    )
    return stops + taken


def one_line(text: str) -> str:
    """A text in one line of at most `CELL` characters, cut at a word, with an ellipsis."""
    flat = " ".join(text.split())
    if len(flat) <= CELL:
        return flat
    cut = flat[:CELL].rsplit(" ", 1)[0].rstrip(",;:.")
    return f"{cut}…"


def stories(record: Record) -> Lines:
    """The story and the chart of each important decision that has one, folded under the
    list, which the forge draws: one the request is not green for, or his help on a
    breaker."""
    found: list[str] = []
    for decision in record.task.decisions:
        if not isinstance(decision, Taken):
            continue
        important = without_him(decision) or (
            decision.by == "owner" and decision.breaker is not None
        )
        if not important or not (decision.story or decision.chart):
            continue
        summary = f"Decision {decision.id}, its story: {one_line(decision.what)}"
        found.extend(("", f"<details><summary>{summary}</summary>", ""))
        story = decision.story
        if story is not None:
            known = KNOWN[story.case_was]
            found.extend((f"**The case** ({known}):", "", *story.case, ""))
            found.extend((f"**Why it could happen:** {story.cause}", ""))
        if decision.chart:
            found.extend(("```mermaid", *decision.chart.splitlines(), "```", ""))
        found.append("</details>")
    return tuple(found)
