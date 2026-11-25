"""`lem criteria digest` and `lem criteria approved`: the mark of a set of criteria without their
tests, of a file or of the task's criteria as they stand, and the newest approval
(`criteria.main` on `main`)."""

from typing import TYPE_CHECKING

from lem.app.criteria import show, texts, where
from lem.model.criteria import digest
from lem.records.approvals import Approval
from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path


class Mark(Frozen, frozen=True, kw_only=True):
    """The mark of the criteria of a file: the task, the file, the mark."""

    task: str
    of: str
    digest: str


class Approved(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The newest approval of the task, or None, with a line that says what stands then."""

    task: str
    approved: Approval | None
    says: str | None


def marked(folder: Path, slug: str, path: Path | None) -> Mark:
    """`lem criteria digest SLUG [--file FILE]`."""
    if path is None:
        seen = show.shown(folder, slug)
        return Mark(task=slug, of=seen.plan, digest=seen.criteria_digest)
    where.here_of(folder, slug)
    sheet = texts.sheet_at(path, "the criteria to mark")
    return Mark(
        task=slug, of=str(path), digest=digest.of_texts(sheet.size, sheet.criteria)
    )


def approved(folder: Path, slug: str) -> Approved:
    """`lem criteria approved SLUG`."""
    approvals = where.here_of(folder, slug).read().task.criteria.approvals
    if approvals:
        return Approved(task=slug, approved=approvals[-1], says=None)
    return Approved(
        task=slug,
        approved=None,
        says="no approved criteria: the plan's own criteria are their one source",
    )
