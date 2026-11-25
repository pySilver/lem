"""The personas' read of the criteria and the owner's approval, as lines of the pull request's
checks (`main:land.read_line`, `unread`, `approval_said`), on the standard track."""

from types import MappingProxyType
from typing import TYPE_CHECKING

from lem.app.landing.pr_inputs import Lines
from lem.model.landing import propose_criteria
from lem.records.decisions import CriterionChanged

if TYPE_CHECKING:
    from lem.records.approvals import PersonaRead
    from lem.records.record import Record
    from lem.records.task import Task

FAMILIES = MappingProxyType({1: "one model family", 2: "two model families"})
NO_WAIT = "the build started with no wait for the owner"
SCOUT = (
    "- the criteria were written from the scout's facts of the code, read during the "
    "interview"
)


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


def found(read: PersonaRead) -> str:
    """What a read that someone answered found: who read, in which families, the doubt, and
    who did not answer."""
    count = len(read.families)
    families = FAMILIES.get(count, f"{count} model families")
    listed = ", ".join(read.families)
    noun = "criterion" if read.criteria == 1 else "criteria"
    doubt = f"{read.flagged} of {read.criteria} {noun} flagged"
    split = "; the two families split" if read.split else ""
    silent = "".join(f"; no answer from {one.name} ({one.why})" for one in read.silent)
    asked = f"{read.answered} of {read.asked} personas asked"
    doubts = (doubt if read.flagged else "nobody confused") + split + silent
    return f"read by {asked}, {families} ({listed}); {doubts}"


def read_line(record: Record) -> str:
    """The personas' read of the criteria and the owner's approval, as one line."""
    task = record.task
    read = propose_criteria.newest(task)
    ending = approved(task) or NO_WAIT
    if read is not None and not read.answered:
        quiet = propose_criteria.quiet(propose_criteria.done(task))
        none = f"none of the {read.asked} personas asked answered"
        said = f"not read by the personas: {quiet} reads in a row, and {none}"
        return f"- the criteria were {said}; {ending}"
    if read is not None:
        return f"- the criteria were {found(read)}; {ending}"
    if task.criteria.skip == "yes":
        return (
            "- the criteria: not read by the personas, on the owner's word; " + ending
        )
    return "- the criteria: no read by the personas is on record" + (
        f"; {approved(task)}" if approved(task) else ""
    )


def unread(record: Record) -> Lines:
    """The line that says the criteria are not the ones the personas read, and what changed
    them: an approval of his with other criteria, or a change of the build."""
    task = record.task
    read = propose_criteria.newest(task)
    if read is None or not read.answered or task.criteria.digest == read.digest:
        return ()
    ended = read.ended or read.started
    his = [
        approval.number
        for approval in task.criteria.approvals
        if approval.by == "owner"
        and approval.at >= ended
        and approval.digest != read.digest
    ]
    what = [f"by the owner's approval {his[-1]}"] if his else []
    if any(
        isinstance(change, CriterionChanged) and change.at >= ended
        for change in task.decisions
    ):
        what.append("by a change of the build")
    listed = f", {' and '.join(what)}" if what else ""
    return (
        f"- the criteria changed after the personas' read{listed}, and the change was not read",
    )


def scout(record: Record) -> Lines:
    """The criteria were written from the scout's facts: no path, the forge has no file of
    this machine."""
    scouted = any(span.name == "scout" for span in record.task.spans)
    return (SCOUT,) if scouted else ()
