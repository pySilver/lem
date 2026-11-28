"""The parts of a feature as its landing sees them (`docs/plans/2026-11-27-a-feature-in-parts.md`,
"The end"): each task whose `Task.part_of` names the task, as its record reads now, and, while
the feature's pull request is open, each open pull request on the forge whose base is the
feature's branch.

A task that no record names has no parts: its world holds no `Feature`, and the forge is not
asked. A part has no parts of its own, so its records are not read for it. A record that does
not read is passed over, as the sync duty passes over it; once a part names the task, each such
record is kept in `Feature.unread`, since it may be a part that has not ended.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.model.landing.feature_seen import Feature, PartSeen, Targeting
from lem.model.landing.review import newest
from lem.records.landing.record import Landing
from lem.store import survey

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.landing.world import World
    from lem.ports.forge import Forge
    from lem.records.record import Record
    from lem.store.places import Workspace

OPEN = "open"


def part_seen(record: Record) -> PartSeen:
    """One part as its record reads now: its pull request, its proposal's green, its newest
    answered review and its merge."""
    landing = record.landing or Landing()
    proposed = landing.proposed
    return PartSeen(
        slug=record.task.slug,
        status=record.task.status,
        pull=landing.pull,
        green=proposed.green if proposed else None,
        review=newest(landing),
        merged=landing.merged,
    )


type Found = tuple[tuple[Record, ...], tuple[str, ...]]


def of(state: Path, slug: str) -> Found:
    """The records of the parts of the task `slug`, and the tasks whose record does not
    read."""
    found = survey.records(state)
    return tuple(filter(partial(names, slug), found.readable)), found.unread


def names(slug: str, record: Record) -> bool:
    """Whether the task of `record` is a part of the task `slug`."""
    return record.task.part_of == slug


def named(state: Path, slug: str) -> bool:
    """Whether a part names the task `slug`: whether it is a feature."""
    return bool(of(state, slug)[0])


def targeting(forge: Forge, branch: str) -> tuple[Targeting, ...]:
    """Each open pull request on the forge whose base is `branch`."""
    return tuple(
        Targeting(number=pull.number, url=pull.url, head=pull.head_ref)
        for pull in forge.open_pulls()
        if pull.state == OPEN and pull.base == branch
    )


def seen(
    forge: Forge, workspace: Workspace, record: Record, world: World
) -> Feature | None:
    """The feature's parts, the records that do not read, and, while its pull request is
    open, the open pull requests into its branch; None for a task that no part names."""
    task = record.task
    if task.part_of is not None:
        return None
    parts, unread = of(workspace.state, task.slug)
    if not parts:
        return None
    phase = (record.landing or Landing()).phase
    into = targeting(forge, world.branch) if phase == OPEN else ()
    return Feature(parts=tuple(map(part_seen, parts)), unread=unread, targeting=into)
