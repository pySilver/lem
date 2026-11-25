"""The two ends a task's own commands write besides the landing's: `answered`, which has its
report to show, and the start over of a landing that cannot go on (`landing.md` E, "Start
over"; `project.answered_form` and `with_start_over` on `main`)."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.records.journal.task import Summary
from lem.records.landing.propose import OwnerMerge

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.task import Task

# The calls of an investigation that end its task with the report, and the line a start over
# writes first, which `lem land start` reads.
ANSWERING = frozenset(("not-a-bug", "answer"))
START_OVER = "the landing starts over"


def answer_refusal(task: Task, *, report: bool) -> Refusal | None:
    """Why `task` may not be answered: it needs its investigation's report (`report`, the
    file is there) and a record whose call ends it."""
    slug = task.slug
    if not report:
        return Refusal(
            "answered",
            f"{slug} has no investigation.md in its folder: an answered task ends with its "
            "report",
            "write the investigator's report there first",
        )
    call = task.investigation.call if task.investigation else None
    if call not in ANSWERING:
        return Refusal(
            "answered",
            f"{slug} is answered only after an investigation whose call is not-a-bug or "
            f"answer; its call is {call}",
            f"lem task investigated {slug} ... --call answer|not-a-bug first",
        )
    return None


def started_over(record: Record, why: str) -> Record:
    """The landing started over: its reviews archived, its attempts from 1, the owner's
    standing merge and the carried reads cleared, and his merge ended with `why`."""
    landing = record.landing
    if landing is None:
        return record
    proposed = landing.proposed
    if proposed is not None:
        ended = OwnerMerge(state="ended", why=f"the landing started over: {why}")
        proposed = replace(proposed, owner_merge=ended)
    archived = (*landing.archived, *landing.reviews)
    changed = replace(
        landing,
        reviews=(),
        filed=(),
        reads=(),
        standing=None,
        archived=archived,
        proposed=proposed,
    )
    return replace(record, landing=changed)


def start_over_line(why: str) -> str:
    """The journal's line of a start over: the mark `lem land start` reads, and why."""
    return f"{START_OVER}: {why}"


def summarized(record: Record) -> bool:
    """Whether retention folded the task's journal into its summary: the files a resumed task
    would go on from are gone."""
    return any(isinstance(entry, Summary) for entry in record.journal)
