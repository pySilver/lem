"""Where the owner answers his own wait (`board_model.answer_of` on `main`, its branches of the
interview, the skip of the read and the criteria): in the task's session, or on the board."""

from typing import TYPE_CHECKING

from lem.board.views import words
from lem.model.criteria import waits
from lem.model.owner import turns

if TYPE_CHECKING:
    from lem.records.holds import OwnerHold
    from lem.records.task import Task

YES_NO = "Yes, or No with your words, and Lem changes them and asks for your yes again."
SKIP = (
    "Lem asks whether to skip the personas’ read of the criteria, since each "
    "names only you. Answer Yes or No on this board, "
    "or y or n in the task’s session."
)
INTERVIEW = (
    "The interview runs in the task’s session. Answer its questions there, and "
    "approve the criteria at its end."
)
FAST = (
    "The one criterion of a request someone else wrote waits for your yes. "
    "Answer Yes or No under its text on this board, or y or n in the task’s "
    "session. No needs your words: what the criterion should say."
)


def answer(task: Task, hold: OwnerHold) -> str:
    """Where he answers the wait `hold` of the task."""
    if hold.on == "skip-read":
        return SKIP
    if hold.on == "interview" and turns.asked(task) is None:
        return INTERVIEW
    if hold.on == "interview":
        return (
            "The criteria wait for your yes in the task’s session. Approve or change "
            f"them there, or on this board: {YES_NO}"
        )
    if hold.on == "criteria":
        return criteria(task, hold)
    shown = words.said(hold.line)
    return (
        f"It waits on what its state says: “{shown}”. "
        "The task’s session says what to do."
    )


def criteria(task: Task, hold: OwnerHold) -> str:
    """Where he answers the criteria that wait for his yes: the fast track's one criterion
    of a request someone else wrote, a change from his note, a read no persona answered, or
    the criteria with the personas' read."""
    shape = task.shape
    if shape is not None and shape.someone_else and task.criteria.size == "small":
        return FAST
    if hold.line == waits.CHANGED:
        return (
            "The criteria changed from your note, and wait for your yes again, each "
            "changed one with its text before beside it. Approve or change them in the "
            f"task’s session, or on this board: {YES_NO}"
        )
    reads = task.criteria.reads
    if reads and not reads[-1].answered:
        return (
            "No persona answered the read of the acceptance criteria. "
            "Approve or change them in the task’s session, "
            f"or on this board: {YES_NO}"
        )
    return (
        "The acceptance criteria, with the personas’ read on top, wait in the "
        "task’s session. Approve or change them there, "
        f"or on this board: {YES_NO}"
    )
