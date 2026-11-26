"""`lem criteria skip`: the owner's word on the skip of the personas' read (`project.cmd_log` of
`read.skip.asked` on `main`)."""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.criteria import where
from lem.app.decisions.writing import Change, written
from lem.kernel import clock
from lem.model.criteria import skip
from lem.records.journal.task import CriteriaNoted

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.criteria import Criteria
    from lem.records.record import Record


def skipping(word: skip.Word, record: Record) -> tuple[Change, Criteria]:
    """His word on the skip, on the record as it is."""
    now = clock.now()
    task = skip.skipped(record.task, word, now)
    journal = record.journal
    if word != "no":
        noted = CriteriaNoted(
            at=now, event="skip-asked" if word == "asked" else "skip-yes"
        )
        journal = (*journal, noted)
    return partial(replace, task=task, journal=journal), task.criteria


def skipped(folder: Path, slug: str, word: skip.Word) -> Criteria:
    """`lem criteria skip SLUG asked|yes|no`."""
    here = where.here_of(folder, slug)
    return written(here.workspace.state, slug, partial(skipping, word))
