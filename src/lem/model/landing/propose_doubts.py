"""The refusals of `propose` for a doubt about the criteria that only the owner settles
(`main:land.cmd_propose`, `interview_unapproved`): a read that flagged a criterion or split the
model families, an interview, and a complete request someone else wrote, each with no approval
of his after it. The lead's freeze of a read is not his yes."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing.propose_criteria import APPROVE, HIS, approved_after, newest
from lem.model.landing.propose_facts import small

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.task import Task


def interviewed(task: Task) -> bool:
    """Whether the task had an interview: its span, or the shape that sent it there."""
    shape = task.shape
    spans = any(span.name == "interview" for span in task.spans)
    return spans or (shape is not None and shape.then == "interview")


def doubted(record: Record) -> Refusal | None:
    """The refusal of a read that flagged a criterion or split the families, with no
    approval of his, nor one without him, after it."""
    task, read = record.task, newest(record.task)
    if read is None or not (read.flagged or read.split):
        return None
    if approved_after(task, read, HIS):
        return None
    noun = "criterion" if read.flagged == 1 else "criteria"
    doubt = f"{read.flagged} flagged {noun}"
    if not read.flagged:
        doubt = "a split between the two families"
    return Refusal(
        "criteria-doubt",
        f"the newest read of {task.slug}'s criteria found {doubt}, and no approval of "
        "the owner's came after it",
        "the criteria with the personas' answers on top go to the owner "
        "(stages/interview.md, step 6), and his yes is kept with "
        f"{APPROVE.format(task.slug)}",
    )


def unapproved(record: Record) -> Refusal | None:
    """The refusal of a request that had an interview, or that someone else wrote, with no
    approval of his: the lead's freeze of a read is not his yes."""
    task = record.task
    his = any(approval.by in HIS for approval in task.criteria.approvals)
    if interviewed(task) and not small(record) and not his:
        return Refusal(
            "interview-unapproved",
            f"{task.slug} had an interview, and its criteria carry no approval of "
            "the owner's: the interview ends with his yes",
            f"{APPROVE.format(task.slug)} (stages/interview.md, steps 6 and 7), or, "
            f"while the task runs without him, lem criteria approve {task.slug} "
            "--alone (stages/away.md)",
        )
    return elsewhere(record)


def elsewhere(record: Record) -> Refusal | None:
    """The refusal of a complete request someone else wrote whose criteria have no approval
    of his after the newest read: nobody at the terminal read that request."""
    task, read = record.task, newest(record.task)
    someone = task.shape is not None and task.shape.someone_else
    if read is None or not someone:
        return None
    if approved_after(task, read, HIS):
        return None
    return Refusal(
        "someone-else",
        f"{task.slug} is a complete request that someone else wrote, and no approval of "
        "the owner's came after the newest read of its criteria: nobody at the terminal "
        "read that request, and a freeze by the read is not his yes (stages/plan.md, "
        "step 1)",
        "the criteria with the personas' answers go to the owner, and his yes is kept "
        f"with {APPROVE.format(task.slug)}",
    )
