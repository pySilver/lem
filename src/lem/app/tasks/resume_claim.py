"""Claim a resume after Git reserves its branch (`project.open_resumed` on `main`)."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.tasks import heads, ports, worktree
from lem.app.tasks.where import named
from lem.kernel.errors import Refusal
from lem.model.task import claim
from lem.settings.load import base_of, team_of
from lem.store import workspace

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.tickets import Tracker
    from lem.store.places import Workspace


def prepared(where: Workspace, made: Record, start: str | None) -> None:
    """Cut the successor's own branch before it can be published."""
    if made.task.branch is None:
        return
    team = team_of(where.checkout)
    branch = named(made, None, team.branch)
    source = worktree.start_of(start, base_of(team))
    heads.fresh(ports.bound(where), where.checkout, (branch, source))


def checked(
    where: Workspace,
    made: Record,
    start: str | None,
    every: tuple[Record, ...],
    *,
    kind: Tracker | None,
) -> Record:
    """Check the claim and reserve its branch inside the workspace lock."""
    slug = made.task.slug
    if any(record.task.slug == slug for record in every):
        raise Refusal(
            "task-exists", f"a task {slug} is here already", "run the resume again"
        )
    claimed = claim.claimed(made, every, kind)
    prepared(where, claimed, start)
    return claimed


def opened(
    where: Workspace, made: Record, start: str | None, kind: Tracker | None
) -> Record:
    """Publish the new task that will use the reserved branch."""
    return workspace.claimed(
        where.state, partial(checked, where, made, start, kind=kind)
    )
