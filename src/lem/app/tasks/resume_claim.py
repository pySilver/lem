"""Claim a resume after Git reserves its branch (`project.open_resumed` on `main`)."""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.tasks import heads, ports, worktree
from lem.app.tasks.where import named
from lem.kernel.errors import Refusal
from lem.model.task import claim
from lem.settings.load import team_of
from lem.store import workspace

if TYPE_CHECKING:
    from collections.abc import Callable

    from lem.records.record import Record
    from lem.records.tickets import Tracker
    from lem.store.places import Workspace


def prepared(
    where: Workspace, made: Record, start: str | None
) -> Callable[[], None] | None:
    """Fetch outside the workspace lock and give the branch reservation to run inside it."""
    if made.task.branch is None:
        return None
    branch = named(made, None, team_of(where.checkout).branch)
    given = ports.bound(where)
    source = worktree.start_of(given, where, made, start)
    source, said = heads.fetched(given, where.checkout, source)
    return partial(
        heads.fresh,
        given,
        where.checkout,
        (branch, source),
        origin_answered=said is None,
    )


def checked(
    where: Workspace,
    made: Record,
    reserve: Callable[[], None] | None,
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
    if reserve is not None:
        reserve()
    return claimed


def opened(
    where: Workspace, made: Record, start: str | None, kind: Tracker | None
) -> Record:
    """Publish the new task that will use the reserved branch."""
    reserve = prepared(where, made, start)
    return workspace.claimed(
        where.state, partial(checked, where, made, reserve, kind=kind)
    )
