"""What one sync of a feature works with: the ports, the workspace, the feature's record as the
sync read it, where it takes in the base (`model/task/sync_stops.Place`), and the moment.


A task is refused before any git when it takes no sync (`model/task/sync.py`); its base is
the settings' (`bases.chosen`), since a feature is no part."""

import dataclasses
from typing import TYPE_CHECKING

from lem.app.tasks import bases, ports, release, where
from lem.model.task import sync as rules
from lem.model.task.sync_stops import Place
from lem.store import survey

if TYPE_CHECKING:
    from pathlib import Path

    from lem.app import wiring
    from lem.ports.git import Git
    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.store.places import Workspace


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Sync:
    """One sync: the ports, the workspace, the feature's record, its place and the moment."""

    ports: wiring.Ports
    workspace: Workspace
    record: Record
    place: Place
    now: Moment

    @property
    def git(self) -> Git:
        """The workspace's git."""
        return self.ports.git

    @property
    def checkout(self) -> Path:
        """The workspace's main checkout, from which origin is fetched."""
        return self.workspace.checkout


def opened(workspace: Workspace, slug: str, now: Moment) -> Sync:
    """The sync of the feature as its record reads now; refused for a task that takes none."""
    record = release.checked(workspace.state, slug)
    every = (one.task for one in survey.records(workspace.state).readable)
    refused = rules.refused(record.task, feature=rules.named(slug, every))
    if refused is not None:
        raise refused
    given = ports.bound(workspace)
    place = Place(
        slug=slug,
        branch=where.branch(record),
        base=bases.chosen(given.git, workspace, record),
        worktree=where.worktree(workspace, slug),
    )
    return Sync(ports=given, workspace=workspace, record=record, place=place, now=now)
