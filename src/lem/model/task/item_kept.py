"""The task's backlog item left to the backlog: a task whose request named an item for other work,
or whose approved criteria do not cover the item's whole run, does not do the item's work, so
it holds the item no more, its branch keeps it, and its pull request says why (`stages/land.md`,
step 6). The own-item gate then asks for no removal (`model/landing/propose_gates.py`)."""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.task.claim import ENDED
from lem.records.journal.task import StateNoted

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.record import Record


def kept(record: Record, *, why: str, now: Moment) -> Record:
    """`record` with no backlog item, and a line of the journal that says it stays and why;
    refused for a task that holds no item, that ended, or with no why."""
    task = record.task
    if task.backlog_item is None:
        raise Refusal(
            "no-item",
            f"{task.slug} holds no backlog item",
            "nothing to keep: its pull request removes no item",
        )
    if task.status in ENDED:
        raise Refusal(
            "task-ended",
            f"{task.slug} is {task.status}, and an ended task changes no more",
            "the item stays as it is",
        )
    if not why.strip():
        raise Refusal(
            "why",
            "--why says what of the item this task leaves undone, and it is empty",
            "give the reason in a few words",
        )
    line = f"the item {task.backlog_item} stays in the backlog: {why.strip()}"
    entry = StateNoted(at=now, status=task.status, line=line)
    held = replace(task, backlog_item=None)
    return replace(record, task=held, journal=(*record.journal, entry))
