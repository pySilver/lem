"""The first record of a part of a feature (`lem task split`;
`docs/plans/2026-11-27-a-feature-in-parts.md`, "The order of the parts").

A part is an ordinary task on the standard track, whose criteria are approved and read
(`part_carry.py`). A part first, or marked independent, opens `shaping` with `then` set to
`lead`, so its session starts the lead; every other part opens `queued` after the part before
it, and the queue duty gives it its turn. Its Activity says where its read and approval came
from, as a resume's carried lines do (`carried_from`).
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel import release
from lem.model.task.split_records import LEAD, QUEUED
from lem.records.journal.task import CriteriaNoted, StateNoted
from lem.records.record import Record
from lem.records.task import Task

if TYPE_CHECKING:
    from lem.model.task.parts import Part
    from lem.records.base import Moment
    from lem.records.criteria import Criteria
    from lem.records.journal.entry import Entry
    from lem.records.task import Status


def criteria_lines(criteria: Criteria, origin: str, now: Moment) -> tuple[Entry, ...]:
    """The lines of the read and the approval a part took from its feature `origin`."""
    reads = tuple(
        CriteriaNoted(
            at=now,
            event="read-done",
            by=read.by,
            asked=read.asked,
            answered=read.answered,
            flagged=read.flagged,
            split=read.split,
            carried_from=origin,
        )
        for read in criteria.reads
    )
    approved = tuple(
        CriteriaNoted(
            at=now,
            event="approved",
            by=approval.by,
            number=approval.number,
            size=approval.size,
            carried_from=origin,
        )
        for approval in criteria.approvals
    )
    return (*reads, *approved)


def part_task(feature: Task, part: Part, criteria: Criteria, now: Moment) -> Task:
    """A part's task: queued after the part before it, else shaping, its shape the feature's
    with the lead next, its criteria the ones copied for it."""
    status: Status = QUEUED if part.after else "shaping"
    shape = feature.shape
    if shape is not None:
        shape = replace(shape, then=LEAD, first_line=None, fits=False)
    return Task(
        slug=part.slug,
        ask=part.ask,
        opened=now,
        status=status,
        since=now,
        after=part.after,
        part_of=feature.slug,
        mode=feature.mode,
        mode_since=feature.mode_since,
        shape=shape,
        owner_careful=feature.owner_careful,
        criteria=criteria,
    )


def part_record(feature: Task, part: Part, criteria: Criteria, now: Moment) -> Record:
    """The first record of a part, with the line that it opened and its criteria's lines."""
    task = part_task(feature, part, criteria, now)
    opened = StateNoted(
        at=now, status=task.status, line=f"the task is open: a part of {feature.slug}"
    )
    lines = criteria_lines(criteria, feature.slug, now)
    return Record(release=release.running(), task=task, journal=(opened, *lines))
