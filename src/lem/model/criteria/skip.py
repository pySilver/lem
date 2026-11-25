"""His word on the skip of the personas' read (`read.skip.asked` and the decision `--by owner` on
`main`; `stages/interview.md`, step 5).

When every criterion names only the developer, the interview asks him one fixed question before
the read starts; the read is his to skip, never the agent's. While the question waits, the task
waits for him on it; his yes or no puts the interview's wait back, from the moment it began.
"""

from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from lem.records.holds import Hold, OwnerHold

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.task import Task

type Word = Literal["asked", "yes", "no"]

ASKED = "the owner decides whether the personas read the criteria"
INTERVIEW = "the interview waits for the owner"


def held(task: Task, word: Word, now: datetime) -> Hold | None:
    """The hold after his word: the skip's while it is asked, the interview's after his
    answer to it; any other hold stays."""
    hold = task.hold
    since = hold.since if isinstance(hold, OwnerHold) else now
    if word == "asked":
        return OwnerHold(on="skip-read", line=ASKED, since=since)
    if isinstance(hold, OwnerHold) and hold.on == "skip-read":
        return OwnerHold(on="interview", line=INTERVIEW, since=since)
    return hold


def skipped(task: Task, word: Word, now: datetime) -> Task:
    """The task with his word on the skip."""
    criteria = replace(task.criteria, skip=word)
    return replace(task, criteria=criteria, hold=held(task, word, now))
