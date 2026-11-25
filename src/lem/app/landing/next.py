"""`lem land next`: the due step of the landing and why, from the record and the world now.

It takes no step lock and changes nothing but origin's refs, which it fetches. A task that is not
ready to land gets its reason without a look at git or the forge.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import frame, say
from lem.app.landing.world import gather
from lem.kernel import clock
from lem.kernel.envelope import Envelope
from lem.model.landing import phases
from lem.model.landing.world import Due
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


def due_of(workspace: places.Workspace, record: Record) -> Due:
    """The due step of the record's task, gathered now; none for a task not ready."""
    status = record.task.status
    if status not in phases.LANDS:
        return Due(step="none", why=f"the task is {status}: it lands once it is ready")
    ports = frame.bound(workspace)
    world = gather(ports, workspace, record, clock.now(), fetch=True)
    return phases.due(record, world)


def due_now(folder: Path, slug: str) -> Envelope:
    """The due step of the task `slug`, with the command that runs it."""
    workspace = places.workspace(folder)
    due = due_of(workspace, tasks.read(workspace.state, slug))
    encoded = msgspec.Raw(msgspec.json.encode(due))
    return Envelope(ok=True, outcome=encoded, following=say.following(slug, due))
