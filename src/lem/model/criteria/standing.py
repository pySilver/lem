"""A task's criteria as they stand, as `lem criteria show` and `record` give them: the file they
come from and whether it is the fast track's, the size and why, the marks of the criteria, How
it works, the approval, every approval, the changes of the newest one and the history."""

from typing import TYPE_CHECKING

from lem.model.criteria import digest
from lem.model.decisions.changes import Approved, Past
from lem.records.approvals import Size
from lem.records.base import Frozen
from lem.records.criterion import Criterion
from lem.records.decisions import CriterionChanged

if TYPE_CHECKING:
    from lem.model.criteria.read import Sheet
    from lem.model.decisions.changes import Changes


class Shown(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The criteria as they stand (`criteria_digest` is the mark of their texts, `digest` of
    the criteria with their tests)."""

    task: str
    plan: str
    small: bool
    size: Size
    why: str
    digest: str
    criteria_digest: str
    criteria: tuple[Criterion, ...]
    how: str | None
    approved: Approved | None
    approvals: tuple[Approved, ...]
    changes: tuple[CriterionChanged, ...]
    history: tuple[Past, ...]


def shown_of(
    slug: str, path: str, sheet: Sheet, changes: Changes, *, small: bool
) -> Shown:
    """The criteria of `sheet`, read from `path`, with the task's approvals and changes."""
    return Shown(
        task=slug,
        plan=path,
        small=small,
        size=sheet.size,
        why=sheet.why,
        digest=sheet.digest,
        criteria_digest=digest.of_texts(sheet.size, sheet.criteria),
        criteria=sheet.criteria,
        how=sheet.how,
        approved=changes.approved,
        approvals=changes.approvals,
        changes=changes.changes,
        history=changes.history,
    )
