"""The parts of a feature as its landing sees them (`docs/plans/2026-11-27-a-feature-in-parts.md`,
"The end"): each task that the feature's `Task.after` names and whose `Task.part_of` names the
feature, as its record reads now, and, while the feature's pull request is open, each open pull
request on the forge whose base is the feature's branch.

A feature's `after` holds every part (`lem task open --part-of` puts it there, and the owner's
word that starts a feature keeps it), so a decision about one task reads only that task and those
it names (decision 30): a task whose `after` is empty reads nothing more, and the forge is not
asked. A part has no parts of its own. A named record that does not read is passed over while no
other named record is a part; once one is, it is kept in `Feature.unread`, since it may be a part
that has not ended.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Fault
from lem.model.landing.feature_seen import Feature, PartSeen, Targeting
from lem.model.landing.review import newest
from lem.records.landing.record import Landing
from lem.store import places, task_file

if TYPE_CHECKING:
    from pathlib import Path

    from lem.model.landing.world import World
    from lem.ports.forge import Forge
    from lem.records.record import Record
    from lem.records.task import Task

OPEN = "open"
type Found = tuple[tuple[Record, ...], tuple[str, ...]]


def part_seen(record: Record) -> PartSeen:
    """One part as its record reads now: its pull request, its proposal's green and careful
    call, its newest answered review and its merge."""
    landing = record.landing or Landing()
    proposed, review = landing.proposed, newest(landing)
    called = bool(review and review.careful)
    return PartSeen(
        slug=record.task.slug,
        status=record.task.status,
        pull=landing.pull,
        green=proposed.green if proposed else None,
        careful=bool(proposed and proposed.careful) or called,
        review=review,
        merged=landing.merged,
    )


def read_named(state: Path, slug: str) -> Record | str | None:
    """The record of the task `slug`, its slug when its record does not read, or None when
    no such task is published."""
    path = places.task_folder(state, slug) / task_file.RECORD
    if not places.SLUG.fullmatch(slug) or not task_file.published(path):
        return None
    try:
        return task_file.read(path)
    except Fault, OSError:
        return slug


def of(state: Path, task: Task) -> Found:
    """The records of the parts of `task` among the tasks its `after` names, and the named
    tasks whose record does not read."""
    records: list[Record] = []
    unread: list[str] = []
    named = dict.fromkeys(task.after) if task.part_of is None else ()
    for slug in named:
        found = read_named(state, slug)
        if isinstance(found, str):
            unread.append(found)
        elif found is not None and found.task.part_of == task.slug:
            records.append(found)
    return tuple(records), tuple(unread)


def named(state: Path, task: Task) -> bool:
    """Whether a part names `task`: whether it is a feature."""
    return bool(of(state, task)[0])


def kept(state: Path, task: Task) -> tuple[str, ...]:
    """The slugs of the parts of `task`, which its `after` keeps once it no longer waits."""
    return tuple(record.task.slug for record in of(state, task)[0])


def targeting(forge: Forge, branch: str) -> tuple[Targeting, ...]:
    """Each open pull request on the forge whose base is `branch`."""
    return tuple(
        Targeting(number=pull.number, url=pull.url, head=pull.head_ref)
        for pull in forge.pulls_into(branch)
    )


def seen(forge: Forge, state: Path, record: Record, world: World) -> Feature | None:
    """The feature's parts, the named records that do not read, and, while its pull request
    is open, the open pull requests into its branch; None for a task that no part names."""
    parts, unread = of(state, record.task)
    if not parts:
        return None
    phase = (record.landing or Landing()).phase
    into = targeting(forge, world.branch) if phase == OPEN else ()
    return Feature(parts=tuple(map(part_seen, parts)), unread=unread, targeting=into)
