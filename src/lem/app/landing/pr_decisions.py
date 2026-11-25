"""The decisions of the build in the pull request's text (`main:land.breaker_lines`,
`decided`, `after`): each stop of the circuit breaker with its cause and how it ended, and each
decision of the record with who took it and why."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.landing import pr_stories
from lem.model.landing.green_words import taken_by
from lem.records.decisions import Breaker, Taken

if TYPE_CHECKING:
    from lem.app.landing.pr_inputs import Lines
    from lem.records.record import Record
    from lem.records.task import Task

BREAKER_SAYS = MappingProxyType(
    {
        "irreversible": "the next step could not be reversed by a later no",
        "criteria": "no option of the ladder kept the approved criteria",
    }
)
FAMILIES = MappingProxyType({1: "one model family", 2: "two model families"})
STAMP = "%Y-%m-%d %H:%M UTC"


def helped(task: Task, breaker: Breaker) -> str:
    """How a stop of the breaker ended: the owner's help, or that it waits for him."""
    helps = (
        found.id
        for found in task.decisions
        if isinstance(found, Taken) and found.breaker == breaker.id
    )
    number = next(helps, None)
    if number is None:
        return "it waits for the owner"
    return f"the owner helped, decision {number}"


def breaker_line(task: Task, breaker: Breaker) -> str:
    """One stop of the build at the breaker: when, what, why, and how it ended."""
    cause = BREAKER_SAYS[breaker.cause]
    if breaker.irreversible:
        cause = f"{cause} ({breaker.irreversible})"
    stamp = breaker.at.strftime(STAMP)
    said = f"Why it stopped: {cause}; {helped(task, breaker)}."
    return (
        f"- the build stopped at breaker {breaker.id}, {stamp}: {breaker.what}. {said}"
    )


def voters(decision: Taken, part: int) -> set[str]:
    """The personas (part 0) or the model families (part 2) of a decision's votes, each
    voter written `PERSONA, FAMILY`."""
    parts = (name.partition(", ")[part] for name, _ in decision.votes)
    return set(filter(None, parts))


def voted(decision: Taken) -> str:
    """How the personas settled a decision: their votes, the personas and the model
    families, all for it."""
    count = len(voters(decision, 2))
    kinds = FAMILIES.get(count, "{0} model families").format(count)
    named = f", {kinds}" if count else ""
    personas = len(voters(decision, 0))
    return f": {len(decision.votes)} votes of {personas} personas{named}, all for it"


def after(decision: Taken) -> str:
    """What follows the option a decision took: by whom, why, each level's word, and the
    owner's own words."""
    line = f", by {taken_by(decision)}"
    if decision.unsettled:
        line = ", the lead's pick, which no level of the ladder settled"
    if decision.by == "owner" and decision.breaker is not None:
        line = f"{line}, his help on breaker {decision.breaker}"
    elif decision.by == "personas":
        line += voted(decision)
    line = f"{line}. {decision.why}"
    levels = "; ".join(map(": ".join, decision.levels))
    if levels:
        line = f"{line} Each level: {levels}."
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


def part(record: Record) -> Lines:
    """The standard track's part of the decisions: each one, or `none`, and the story of
    each important one folded under them."""
    return (*(lines(record) or ("none",)), *pr_stories.stories(record))
