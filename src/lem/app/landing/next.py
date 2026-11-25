"""`lem land next`: the due step of the landing and why, from the record and the world now.

It takes no step lock and changes nothing but origin's refs, which it fetches. What the record
alone decides (a task not ready, one that ended, a landing after the forge's merge) is said with
no look at git or the forge; a landing that prepares or whose pull request is open reads the
world, since its due step depends on it.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.app.landing import following, frame, step_release
from lem.app.landing.world import gather
from lem.kernel import clock
from lem.kernel.envelope import Envelope
from lem.model.landing import phases
from lem.store import places

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.landing.world import Due
    from lem.records.record import Record


def due_with(workspace: places.Workspace, record: Record) -> tuple[Due, bool]:
    """The due step of the record's task, and whether its merge squashes the branch; from the
    record when it alone decides, else gathered now."""
    found = phases.settled(record)
    if found is not None:
        return found, True
    ports = frame.bound(workspace)
    world = gather(ports, workspace, record, clock.now(), fetch=True)
    return phases.due(record, world), world.rules.history == "squash"


def due_of(workspace: places.Workspace, record: Record) -> Due:
    """The due step of the record's task, from the record when it alone decides, else
    gathered now."""
    return due_with(workspace, record)[0]


def due_now(folder: Path, slug: str) -> Envelope:
    """The due step of the task `slug`, with the command that runs it."""
    workspace = places.workspace(folder)
    record = step_release.observed(workspace.state, slug)
    due, squash = due_with(workspace, record)
    step_release.reportable(record, due)
    encoded = msgspec.Raw(msgspec.json.encode(due))
    return Envelope(
        ok=True,
        outcome=encoded,
        following=following.following(slug, due, squash=squash),
    )
