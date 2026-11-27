"""`lem task split NAME --file CRITERIA`: a feature in parts, from the criteria the owner
approved (`docs/plans/2026-11-27-a-feature-in-parts.md`, step 36b).

The file must be the feature's newest approval word for word, read by the personas or with the
read skipped on his word (`model/task/part_criteria.py`); its headings give the parts
(`model/task/parts.py`). Once no other task holds a part's slug, `feature/NAME` is cut from
origin's base in the feature's worktree and pushed (`split_branch.py`). Under the workspace's
claim lock, the checks run again on the records as they are then, and the feature is written
`queued` after every part first, then each part's record: a run cut off between them leaves the
feature waiting for a task with no record, which holds it `queued` (`model/task/behind.py`), and
the split run again makes only the parts that are missing. The parts that are `shaping` start
now, each in a session of its own; the others wait for the part before them.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.criteria import texts
from lem.app.tasks import release, split_branch
from lem.kernel import clock, locks
from lem.model.task import part_carry, part_criteria, part_record, parts, split_records
from lem.records.base import Frozen
from lem.store import places, tasks, workspace

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.criteria.read import Sheet
    from lem.records.base import Moment
    from lem.records.record import Record

THE_CRITERIA = "the feature's criteria the owner approved"


class Made(Frozen, frozen=True, kw_only=True):
    """One part of the split: its slug, its status, the part it waits for, and whether this
    call made its record."""

    slug: str
    status: str
    after: tuple[str, ...] = ()
    made: bool = False


class Split(Frozen, frozen=True, kw_only=True):
    """The split: the feature, its branch and worktree, the parts in order, the parts that
    start now (each needs its session), and the line to say when origin did not answer."""

    feature: str
    branch: str
    worktree: str
    parts: tuple[Made, ...]
    starts: tuple[str, ...]
    said: str | None = None


def feature_written(
    where: places.Workspace, record: Record, slugs: tuple[str, ...], now: Moment
) -> Record:
    """The feature queued after the parts `slugs`, unless a split before queued it so."""
    if split_records.done(record.task, slugs):
        return record
    change = partial(split_records.queued, slugs=slugs, now=now)
    return tasks.update(where.state, record.task.slug, change, record.revision)


def parts_written(
    where: places.Workspace,
    feature: Record,
    sheet: Sheet,
    left: tuple[parts.Part, ...],
    now: Moment,
) -> None:
    """The record of each part in `left`, with its criteria copied from the feature's."""
    approval = part_criteria.approval_of(feature, sheet)
    for part in left:
        criteria = part_carry.carried(feature.task, approval, part.criteria)
        made = part_record.part_record(feature.task, part, criteria, now)
        workspace.published(where.state, made)


def written(
    where: places.Workspace, slug: str, sheet: Sheet
) -> tuple[tuple[parts.Part, ...], frozenset[str]]:
    """Under the claim lock, the checks on the records as they are then, the feature queued
    after its parts, then each part that has no record yet; the parts, and the slugs this
    call made."""
    with locks.held(places.locks_folder(where.state) / workspace.LOCK):
        record = tasks.read(where.state, slug)
        found = split_records.planned(record, sheet)
        left = split_records.missing(tasks.every(where.state), found, slug)
        slugs = tuple(part.slug for part in found)
        now = clock.now()
        record = feature_written(where, record, slugs, now)
        parts_written(where, record, sheet, left, now)
    return found, frozenset(part.slug for part in left)


def shown(
    where: places.Workspace, found: tuple[parts.Part, ...], made: frozenset[str]
) -> tuple[Made, ...]:
    """Each part as its record is now, in the order of the headings."""
    records = (tasks.read(where.state, part.slug).task for part in found)
    return tuple(
        Made(
            slug=task.slug, status=task.status, after=task.after, made=task.slug in made
        )
        for task in records
    )


def split(folder: Path, slug: str, path: Path) -> Split:
    """Split the feature `slug` into the parts of the criteria in `path`."""
    where = places.workspace(folder)
    sheet = texts.sheet_at(path, THE_CRITERIA)
    found = split_records.planned(release.checked(where.state, slug), sheet)
    split_records.missing(tasks.every(where.state), found, slug)
    branch = split_branch.branched(where, slug)
    made = shown(where, *written(where, slug, sheet))
    return Split(
        feature=slug,
        branch=branch.branch,
        worktree=branch.worktree,
        parts=made,
        starts=tuple(part.slug for part in made if part.status == "shaping"),
        said=branch.said,
    )
