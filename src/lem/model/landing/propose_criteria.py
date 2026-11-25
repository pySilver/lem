"""The refusals of `propose` that the criteria give (`main:land.cmd_propose`, `read_skipped`,
`interview_unapproved`): the personas read the criteria of a task on the standard track before
the build, and a doubt of theirs, an interview, or a request someone else wrote reaches the
owner, so a request is not proposed over criteria nobody read or over a doubt he never saw.

A read counts once it ended (`lem criteria read SLUG done` or `silent`); an approval counts for
a read when it came at its end or after it.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.landing.propose_facts import small

if TYPE_CHECKING:
    from lem.records.approvals import ApprovedBy, PersonaRead
    from lem.records.record import Record
    from lem.records.task import Task

INTERVIEW = (
    "stages/interview.md, step 5; for the standard track from a complete request "
    "stages/plan.md, step 1"
)
type Approvers = frozenset[ApprovedBy]

APPROVE = "lem criteria approve {0} --file FILE"
OWNER = "owner"
# The approvals that answer the personas' doubt: his, or one made while the task ran
# without him.
HIS: frozenset[ApprovedBy] = frozenset((OWNER, "alone"))


def done(task: Task) -> tuple[PersonaRead, ...]:
    """The reads of the criteria that ended, oldest first."""
    return tuple(read for read in task.criteria.reads if read.ended is not None)


def quiet(reads: tuple[PersonaRead, ...]) -> int:
    """How many reads in a row, the newest last, nobody answered."""
    count = 0
    for read in reversed(reads):
        if read.answered:
            break
        count += 1
    return count


def newest(task: Task) -> PersonaRead | None:
    """The newest read of the criteria that ended."""
    ended = done(task)
    return ended[-1] if ended else None


def approved_after(task: Task, read: PersonaRead, by: Approvers) -> bool:
    """Whether an approval of one of `by` came at the read's end or after it."""
    ended = read.ended or read.started
    return any(
        approval.by in by and approval.at >= ended
        for approval in task.criteria.approvals
    )


def unread(record: Record) -> Refusal | None:
    """The refusal of a task on the standard track with no read of its criteria, unless the
    owner's word to skip it stands, with his approval after it and before any lead."""
    task, slug = record.task, record.task.slug
    if small(record) or newest(task) is not None:
        return None
    if task.criteria.skip == "yes":
        return skipped(task)
    return Refusal(
        "no-read",
        f"{slug} takes the standard track, and no read of its criteria by the personas "
        f"is on record: the personas read its criteria before the build ({INTERVIEW})",
        f"whoever ran the read records it with lem criteria read {slug} done; only the "
        f"owner skips a read, with lem criteria skip {slug} yes and his approval after it, "
        "both before a lead starts",
    )


def skipped(task: Task) -> Refusal | None:
    """The owner's word to skip the read counts with his approval and no lead before it."""
    slug = task.slug
    his = [approval for approval in task.criteria.approvals if approval.by == OWNER]
    leads = [span.start for span in task.spans if span.name == "lead"]
    if not his:
        return Refusal(
            "skip-unapproved",
            f"the owner's word to skip the personas' read of {slug}'s criteria is on "
            "record, and no approval of the owner's came after it",
            f"the owner's yes to the criteria is kept with {APPROVE.format(slug)} "
            "(stages/interview.md, step 7)",
        )
    if leads and min(leads) < his[0].at:
        return Refusal(
            "skip-late",
            f"a lead of {slug} started before the owner's approval that came after the "
            "word to skip the personas' read: on the standard track from a complete "
            "request the read always runs, as the only approval there (stages/plan.md, "
            "step 1)",
            f"the lead runs the read and records it with lem criteria read {slug} done",
        )
    return None


def silent(record: Record) -> Refusal | None:
    """The refusal of a newest read nobody answered, the first such in a row."""
    task, read = record.task, newest(record.task)
    if read is None or read.answered or quiet(done(task)) > 1:
        return None
    slug = task.slug
    return Refusal(
        "criteria-silent",
        f"nobody answered the newest read of {slug}'s criteria; after a second read in "
        "a row that nobody answered, the request is proposed as not green",
        f"start the read once more and record it with lem criteria read {slug} "
        f"({INTERVIEW})",
    )
