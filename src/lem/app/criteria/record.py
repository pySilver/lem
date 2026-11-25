"""`lem criteria record`: the fast track's `criteria.md` read into the task's record, its test
lines with it (`sheet.py`); a criterion's text must stay the one approved."""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.criteria import sheet
from lem.kernel.errors import Refusal
from lem.store import places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.record import Record


def written(found: Record, *, read: sheet.Sheet) -> Record:
    """The record with the criteria as the file has them."""
    criteria = replace(
        found.task.criteria, size=read.size, why=read.why, criteria=read.criteria
    )
    return replace(found, task=replace(found.task, criteria=criteria))


def check(found: Record, read: sheet.Sheet) -> None:
    """Refuse criteria whose texts are not the approved ones."""
    approvals = found.task.criteria.approvals
    if not approvals:
        return
    approved = [criterion.text for criterion in approvals[-1].criteria]
    if approved != [criterion.text for criterion in read.criteria]:
        raise Refusal(
            "criteria-changed",
            f"the criteria of {sheet.NAME} are not the approved ones",
            "a criterion's text stays as approved; only its test lines are added",
        )


def recorded(folder: Path, slug: str) -> sheet.Sheet:
    """Read the task's `criteria.md` into its record."""
    state = places.workspace(folder).state
    found = tasks.read(state, slug)
    read = sheet.sheet_of(places.task_folder(state, slug) / sheet.NAME)
    check(found, read)
    tasks.update(state, slug, partial(written, read=read), found.revision)
    return read
