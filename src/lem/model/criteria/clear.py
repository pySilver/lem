"""What a read lets the lead freeze: the criteria it read, with nobody confused, or after two
reads of the same text in a row that nobody answered (`criteria.approve_held` on `main`). A read
with no result, its silence, counts for neither."""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.records.approvals import PersonaRead
    from lem.records.task import Task


def clear(task: Task, digest: str) -> Refusal | None:
    """Why the lead may not freeze the criteria of mark `digest` on a read: no read of them, a
    first read nobody answered, or a doubt (a flag, a split), which waits for the owner."""
    reads = [read for read in task.criteria.reads if read.digest is not None]
    last = reads[-1] if reads else None
    if last is None or last.digest != digest:
        of = "there is none" if last is None else f"it read {last.digest}"
        return Refusal(
            "not-read",
            f"--read freezes the criteria the newest read read, and {of}, not {digest}",
            "run the persona read over these criteria first (stages/plan.md, step 1)",
        )
    before = reads[-2] if len(reads) > 1 else None
    if last.answered == 0 and not unanswered(before, digest):
        return Refusal(
            "unanswered",
            "nobody answered the newest read of the criteria",
            "start it once more; after a second read in a row that nobody answered, the "
            "build goes on with the criteria as they are",
        )
    if last.flagged or last.split:
        return Refusal(
            "doubt",
            "the newest read flagged a criterion or split between the families",
            "the criteria wait for the owner: only his approval freezes them",
        )
    return None


def unanswered(read: PersonaRead | None, digest: str) -> bool:
    """Whether `read` is a read of the criteria of mark `digest` that nobody answered."""
    return read is not None and read.answered == 0 and read.digest == digest
