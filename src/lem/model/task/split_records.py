"""The records of a split (`lem task split`): the feature queued after all of its parts, its
turn going to its lead, and one record for each part, an ordinary task on the standard track
whose criteria are approved and read (`docs/plans/2026-11-27-a-feature-in-parts.md`, "The order
of the parts").

The feature's `then` is `lead`, so its turn starts its end and not a second interview
(`model/task/queue.py started_in`); a part's record is `part_record.py`'s. A split run again
finds the records it made, and makes only what is missing.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.task import holds, part_criteria, parts, table

if TYPE_CHECKING:
    from lem.model.criteria.read import Sheet
    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.records.task import Task

type Parts = tuple[parts.Part, ...]

CODE = "split"
LEAD = "lead"
QUEUED = "queued"


def done(task: Task, slugs: tuple[str, ...]) -> bool:
    """Whether the feature was split already into the parts `slugs`."""
    then = task.shape.then if task.shape else None
    waits = all(slug in task.after for slug in slugs)
    return task.status == QUEUED and then == LEAD and waits


def splittable(task: Task, slugs: tuple[str, ...]) -> Refusal | None:
    """Why the task may not be split into the parts `slugs`, or None: it is a part, has no
    read of its request yet, is held, or is past its shape."""
    slug = task.slug
    held = table.held_refusal(task, QUEUED)
    if held is not None:
        return held
    if task.part_of is not None:
        return Refusal(
            CODE,
            f"{slug} is a part of {task.part_of}, and a part has no parts of its own",
            f"a part of {task.part_of} more is lem task open SLUG --part-of {task.part_of}",
        )
    if task.shape is None:
        return Refusal(
            CODE,
            f"{slug} has no read of its request yet, so no type and no track",
            f"lem task read {slug} gives them first",
        )
    if task.status == "shaping" or done(task, slugs):
        return None
    return Refusal(
        CODE,
        f"{slug} is {task.status}, and a split takes a feature that is shaping, after the "
        "owner's yes to its criteria",
        f"a part of {slug} more is lem task open SLUG --part-of {slug} while {slug} is "
        "queued",
    )


def queued(record: Record, *, slugs: tuple[str, ...], now: Moment) -> Record:
    """The feature queued after each of its parts, its turn going to its lead."""
    task = record.task
    more = tuple(slug for slug in slugs if slug not in task.after)
    shape = replace(task.shape, then=LEAD) if task.shape else None
    task = replace(task, after=(*task.after, *more), shape=shape)
    names = ", ".join(slugs)
    return holds.moved(
        replace(record, task=task),
        status=QUEUED,
        line=f"queued after its parts: {names}",
        now=now,
    )


def same(task: Task, part: parts.Part, feature: str) -> bool:
    """Whether the task found under a part's slug is that part, made by a split before."""
    words = task.ask.split()
    return task.part_of == feature and words == part.ask.split()


def missing(every: tuple[Record, ...], wanted: Parts, feature: Task) -> Parts:
    """The parts no record holds yet; refused when a part's slug is another task's."""
    found = {record.task.slug: record.task for record in every}
    left: list[parts.Part] = []
    for part in wanted:
        task = found.get(part.slug)
        if task is None:
            left.append(part)
        elif not same(task, part, feature.slug):
            raise Refusal(
                "task-exists",
                f"the task {part.slug} is here already, and it is not the part "
                f"{part.heading!r} of {feature.slug}",
                "give the part's heading another slug, and the owner's yes to the criteria "
                "again",
            )
    return tuple(left)


def planned(record: Record, sheet: Sheet, every: tuple[Record, ...]) -> Parts:
    """The parts of the feature's approved criteria, which the file `sheet` holds word for
    word; refused when the split may not run on the record as it is, and when parts made
    before took another approval (`part_criteria.stale`)."""
    slug = record.task.slug
    part_criteria.stale(every, record.task)
    found = parts.parts_of(slug, sheet.criteria)
    refused = splittable(record.task, tuple(part.slug for part in found))
    if refused is not None:
        raise refused
    approval = part_criteria.approval_of(record, sheet)
    return parts.parts_of(slug, approval.criteria)
