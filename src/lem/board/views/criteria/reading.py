"""The personas' read in one line, under the head of the criteria that wait for the owner's yes
(`board_task.approve_card` on `main`)."""

from typing import TYPE_CHECKING

from lem.board.views.criteria.terms import criteria_count

if TYPE_CHECKING:
    from lem.records.task import Task

NO_READ = "criteria.md in the task directory"


def read_line(task: Task) -> str:
    """What the newest read found, or where the criteria are when nobody read them."""
    reads = task.criteria.reads
    if not reads:
        return NO_READ
    read = reads[-1]
    if not read.answered:
        return "Nobody answered the personas’ read."
    if not (read.flagged or read.split):
        return "The personas read them, and nobody was confused."
    count = criteria_count(read.criteria)
    split = "; the two model families split" if read.split else ""
    return (
        f"The personas flagged {read.flagged} of {count}{split}: read the flagged one "
        "before you approve."
    )
