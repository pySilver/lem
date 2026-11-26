"""`lem criteria read`: the personas' read of the criteria, its start and what it found
(`project.cmd_log` of `criteria.read` and `criteria.read.start` on `main`)."""

from functools import partial
from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from lem.app.criteria import where
from lem.app.decisions.writing import Change, written
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.criteria import reads
from lem.records.journal.task import CriteriaNoted

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.approvals import PersonaRead
    from lem.records.record import Record

type Moment = Literal["start", "done", "silent"]
type By = Literal["lem", "lead"]
# The read's moment, and who runs it.
type Read = tuple[Moment, By]


def noting(
    moment: Moment, by: By, found: reads.Found | None, record: Record
) -> tuple[Change, PersonaRead]:
    """The read's start, its result, or its silence, on the record as it is."""
    now = clock.now()
    if moment == "start":
        task = reads.started(record.task, by, now)
    else:
        task = reads.ended(record.task, by, now, found)
    return written_read(replace(record, task=task))


def written_read(record: Record) -> tuple[Change, PersonaRead]:
    """The write of the read, with its line in Activity."""
    newest = record.task.criteria.reads[-1]
    noted = CriteriaNoted(
        at=newest.ended or newest.started,
        event="read-start" if newest.ended is None else "read-done",
        by=newest.by,
        asked=newest.asked,
        answered=newest.answered,
        flagged=newest.flagged,
        split=newest.split,
    )
    journal = (*record.journal, noted)
    return partial(replace, task=record.task, journal=journal), newest


def noted(
    folder: Path, slug: str, read: Read, found: reads.Found | None
) -> PersonaRead:
    """Write the read `read` (its moment, and who runs it) with what it `found`: `start` and
    `silent` found nothing, which `silent` writes as a read nobody answered."""
    moment, by = read
    if found is not None:
        why = reads.refused(found)
        if why is not None:
            raise Refusal(
                reads.FORM,
                why,
                "lem criteria read SLUG done --by lem|lead --asked N --answered N "
                '[--family F]... [--silent "PERSONA, FAMILY: WHY"]... --criteria N '
                "--flagged N [--split] --digest D",
            )
    here = where.here_of(folder, slug)
    return written(here.workspace.state, slug, partial(noting, moment, by, found))
