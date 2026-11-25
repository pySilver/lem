"""The committed criteria the checks and polish may use."""

from typing import TYPE_CHECKING

from lem.app.criteria import texts
from lem.app.landing import checks_git
from lem.kernel.errors import Refusal
from lem.model.criteria.read import sheet_of

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.criteria import Criteria
    from lem.records.record import Record
    from lem.records.red import Inputs


def verified(worktree: Path, record: Record, found: Inputs) -> Criteria:
    """Use the recorded criteria only when their tests agree with the plan at the run's tip."""
    criteria = record.task.criteria
    if found.plan is None:
        return criteria
    path = worktree / found.plan
    from_git = checks_git.raw(worktree, "show", f"{found.tip}:{found.plan}")
    if from_git.returncode == 0:
        sheet = sheet_of(texts.text_of(from_git.stdout, path), path.name)
        if sheet.digest == criteria.digest:
            return criteria
    slug = record.task.slug
    raise Refusal(
        "criteria",
        f"the criteria on record do not match the plan {found.plan} at {found.tip}",
        f"the lead puts the plan right and runs lem criteria record {slug}, then retries",
    )


def can_take(worktree: Path, record: Record, found: Inputs) -> bool:
    """The kept red test run matches the live criteria and inputs."""
    criteria = verified(worktree, record, found)
    red = criteria.red
    if red is None or not red.ok:
        return False
    return (red.digest, red.inputs) == (criteria.digest, found)
