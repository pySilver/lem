"""The frame of one landing step: the ports, the workspace, and the record and the world the
step read at its start; the task's folder and worktree; and the write of a change at the
revision it read."""

import dataclasses
from typing import TYPE_CHECKING

from lem.app.landing.world import gather
from lem.app.tasks import ports, release, where
from lem.store import places, tasks

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from lem.app import wiring
    from lem.model.landing.world import World
    from lem.records.record import Record

type Change = Callable[[Record], Record]


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Context:
    """What an act reads: the ports, the workspace, the record and the world at the step's
    start."""

    ports: wiring.Ports
    workspace: places.Workspace
    record: Record
    world: World

    @property
    def folder(self) -> Path:
        """The task's folder in the state."""
        return places.task_folder(self.workspace.state, self.record.task.slug)

    @property
    def worktree(self) -> Path:
        """The task's worktree."""
        return where.worktree(self.workspace, self.record.task.slug)

    def again(self, *, ends: bool = False) -> Context:
        """The context read again: the record, and the world after a fetch."""
        record = release.checked(self.workspace.state, self.record.task.slug, ends=ends)
        world = gather(self.ports, self.workspace, record, self.world.now, fetch=True)
        return dataclasses.replace(self, record=record, world=world)

    def write(self, record: Record, change: Change) -> Record:
        """Write `change` over `record`, at the revision it was read."""
        slug = record.task.slug
        return tasks.update(self.workspace.state, slug, change, record.revision)


def bound(workspace: places.Workspace) -> wiring.Ports:
    """The ports of the workspace, bound for this call."""
    return ports.bound(workspace)
