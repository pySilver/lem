"""The personas' read of the criteria and the owner's approval, as one line of the pull
request's checks (`main:land.read_line`, `approval_said`), on the standard track."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.landing.pr_approval import approved
from lem.model.landing import propose_criteria

if TYPE_CHECKING:
    from lem.records.approvals import PersonaRead
    from lem.records.record import Record
    from lem.records.task import Task

FAMILIES = MappingProxyType({1: "one model family", 2: "two model families"})
NO_WAIT = "the build started with no wait for the owner"
WITHOUT_READ = "- the criteria: no read by the personas is on record"
UNREAD = (
    "- the criteria changed after the personas' read{0}, and the change was not read"
)
QUIET = "- the criteria were not read by the personas: {0} reads in a row, and none of the {1}"


def changes(task: Task, read: PersonaRead) -> str:
    """Each change from the owner's notes after the read counts, even a reversal: the changes
    written after the read ended, by their order, never by their second."""
    count = len(task.criteria.changed) - read.changes
    if count <= 0:
        return ""
    times = "once" if count == 1 else f"{count} times"
    return f"; the criteria changed {times} after the personas' read, from the owner's notes"


def doubts(read: PersonaRead) -> str:
    """What a read found: the criteria flagged or nobody confused, a split of the families,
    and who did not answer."""
    noun = "criterion" if read.criteria == 1 else "criteria"
    said = f"{read.flagged} of {read.criteria} {noun} flagged"
    if not read.flagged:
        said = "nobody confused"
    if read.split:
        said = f"{said}; the two families split"
    silent = (f"; no answer from {one.name} ({one.why})" for one in read.silent)
    return said + "".join(silent)


def found(read: PersonaRead) -> str:
    """Who read the criteria, in which families, and what they found."""
    count = len(read.families)
    families = FAMILIES.get(count, "{0} model families").format(count)
    listed = ", ".join(read.families)
    asked = f"{read.answered} of {read.asked} personas asked"
    return f"read by {asked}, {families} ({listed}); {doubts(read)}"


def unanswered(task: Task, read: PersonaRead) -> str:
    """A read nobody answered: how many in a row, and how many personas were asked."""
    quiet = propose_criteria.quiet(propose_criteria.done(task))
    return QUIET.format(quiet, f"{read.asked} personas asked answered")


def read_line(record: Record) -> str:
    """The personas' read of the criteria and the owner's approval, as one line."""
    task = record.task
    read = propose_criteria.newest(task)
    approval = approved(task)
    ending = approval or NO_WAIT
    if read is not None and not read.answered:
        return f"{unanswered(task, read)}{changes(task, read)}; {ending}"
    if read is not None:
        said = found(read) + changes(task, read)
        return f"- the criteria were {said}; {ending}"
    if task.criteria.skip == "yes":
        return (
            f"- the criteria: not read by the personas, on the owner's word; {ending}"
        )
    return f"{WITHOUT_READ}; {approval}" if approval else WITHOUT_READ
