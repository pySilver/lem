"""`lem criteria read` and `lem criteria skip`: the personas' read of the criteria, its start and
what it found, and the owner's word on its skip (`project.cmd_log` of `criteria.read`,
`criteria.read.start` and `read.skip.asked` on `main`)."""

from functools import partial
from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from lem.app.criteria import where
from lem.app.decisions.writing import Change, written
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.criteria import reads, skip

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.approvals import PersonaRead
    from lem.records.criteria import Criteria
    from lem.records.record import Record

type Moment = Literal["start", "done", "silent"]
type By = Literal["lem", "lead"]
# The read's moment, and who runs it.
type Read = tuple[Moment, By]


def noting(
    moment: Moment, by: By, found: reads.Found | None, record: Record
) -> tuple[Change, PersonaRead]:
    """The read's start, its result, or its silence, on the record as it is."""
    now, task = clock.now(), record.task
    if moment == "start":
        task = reads.started(task, by, now)
    else:
        task = reads.ended(task, by, now, found)
    return partial(replace, task=task), task.criteria.reads[-1]


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


def skipping(word: skip.Word, record: Record) -> tuple[Change, Criteria]:
    """His word on the skip, on the record as it is."""
    task = skip.skipped(record.task, word, clock.now())
    return partial(replace, task=task), task.criteria


def skipped(folder: Path, slug: str, word: skip.Word) -> Criteria:
    """`lem criteria skip SLUG asked|yes|no`."""
    here = where.here_of(folder, slug)
    return written(here.workspace.state, slug, partial(skipping, word))
