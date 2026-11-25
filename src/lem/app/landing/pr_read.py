"""The personas' read of the criteria and the owner's approval, as one line of the pull
request's checks (`main:land.read_line`, `approval_said`), on the standard track."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.model.landing import propose_criteria

if TYPE_CHECKING:
    from lem.records.approvals import PersonaRead
    from lem.records.record import Record
    from lem.records.task import Task

FAMILIES = MappingProxyType({1: "one model family", 2: "two model families"})
NO_WAIT = "the build started with no wait for the owner"
UNREAD = (
    "- the criteria changed after the personas' read{0}, and the change was not read"
)
QUIET = "- the criteria were not read by the personas: {0} reads in a row, and none of the {1}"


def approved(task: Task) -> str:
    """Who approved the criteria and when, when it was the owner or made without him."""
    approvals = task.criteria.approvals
    newest = approvals[-1] if approvals else None
    if newest is None or newest.by not in {"owner", "alone"}:
        return ""
    day = newest.at.date().isoformat()
    if newest.by == "owner":
        return f"the owner approved them on {day}"
    return f"approved on {day} while the task ran without the owner"


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
    ending = approved(task) or NO_WAIT
    if read is not None and not read.answered:
        return f"{unanswered(task, read)}; {ending}"
    if read is not None:
        return f"- the criteria were {found(read)}; {ending}"
    if task.criteria.skip == "yes":
        return (
            f"- the criteria: not read by the personas, on the owner's word; {ending}"
        )
    line = "- the criteria: no read by the personas is on record"
    return f"{line}; {approved(task)}" if approved(task) else line
