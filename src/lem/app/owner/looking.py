"""The look at a workspace that the list of what waits reads (`project.waiting_model` on `main`):
every task's record, the owner's presence, the tasks' newest sessions as the terminal shows them,
the guard's stops that stand, the worktrees there, and the server's last look at the forge.

The terminal is asked once, and only when a task has a session on record. When it cannot say,
no task can show as one with no session, and the look says why.
"""

import os
from typing import TYPE_CHECKING

from lem.app.owner import forge, merge_bases, read_order, releases, sessions
from lem.kernel import paths
from lem.model.owner import looks as owner_looks
from lem.records.base import Frozen
from lem.records.owner import Presence
from lem.store import owner, tasks

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.here import Here
    from lem.records.record import Record
    from lem.settings.team import Branch


class Looked(Frozen, frozen=True, kw_only=True):
    """The workspace's tasks as the list reads them, the owner's presence, why the sessions
    are not known (None when they are), and the forge's last look."""

    looks: owner_looks.Looks
    presence: Presence
    unknown: str | None = None
    forge: forge.Look


def looked(here: Here, now: datetime, branch: Branch | None = None) -> Looked:
    """The look at the workspace of `here` now."""
    records = tasks.every(here.where.state)
    shown, unknown = sessions.sessions_of(here, now, records)
    seen = forge.read(here.where.state)
    bases = merge_bases.gathered(here, branch, records)
    return Looked(
        looks=tuple(
            look_of(
                here,
                record,
                shown if unknown is None else None,
                seen,
                bases.for_task(record),
            )
            for record in releases.with_stops(records)
        ),
        presence=owner.read(paths.home(os.environ)),
        unknown=unknown,
        forge=seen,
    )


def look_of(
    here: Here,
    record: Record,
    shown: sessions.Listed | None,
    seen: forge.Look,
    basis: owner_looks.MergeBasis,
) -> owner_looks.Look:
    """One task as the list reads it."""
    slug = record.task.slug
    session = sessions.session_of(
        None if shown is None else shown.get(slug),
        record.task.opened,
        here.caller,
        known=shown is not None,
    )
    return owner_looks.Look(
        record=record,
        session=session,
        stop=sessions.stop_of(here, record, session),
        worktree=here.worktree(slug) is not None,
        conflict=forge.conflicts(seen, record),
        basis=basis,
        read_after_refusal=read_order.after_refusal(record, basis.tree),
    )
